"""Owned, explicit integration setup. No arbitrary config-flow or Supervisor proxy."""
from __future__ import annotations
import asyncio
from collections import OrderedDict
import secrets
import time
from .engine import ProductError


CATALOGUE=[
 {'id':'zha','name':'ZHA','category':'Zigbee','description':'Connect a coordinator directly and pair Zigbee devices.'},
 {'id':'zigbee2mqtt','name':'Zigbee2MQTT','category':'Zigbee','description':'Install the bridge, connect MQTT and choose your coordinator.'},
 {'id':'mqtt','name':'MQTT connection','category':'Connections','description':'Use an existing broker or install the managed MQTT broker.'},
 {'id':'shelly','name':'Shelly','category':'Lighting & switches','description':'Connect Shelly devices on this home network.'},
 {'id':'hue','name':'Philips Hue','category':'Lighting','description':'Connect a Hue bridge and its lights.'},
 {'id':'esphome','name':'ESPHome','category':'Connected devices','description':'Connect an ESPHome device using its network address.'},
 {'id':'onvif','name':'ONVIF camera','category':'Cameras & security','description':'Connect a compatible camera using its address and credentials.'},
 {'id':'sonos','name':'Sonos','category':'Media','description':'Discover and connect Sonos speakers on this network.'},
 {'id':'denonavr','name':'Denon / Marantz','category':'Media','description':'Connect a supported network receiver.'},
 {'id':'webostv','name':'LG webOS TV','category':'Media','description':'Connect and approve access on a compatible LG television.'}
]
KINDS={item['id'] for item in CATALOGUE}


class IntegrationSetup:
    def __init__(self,engine,adapter,clock=time.monotonic):
        self.engine=engine;self.adapter=adapter;self.clock=clock;self.reviews=OrderedDict();self.sessions={};self.lock=asyncio.Lock()

    async def admin(self,actor):self.engine.admin(actor);await self.adapter.authorize(actor.id)

    async def status(self,actor):
        await self.admin(actor)
        report=await self.adapter.status()
        report['catalogue']=CATALOGUE
        report['setups']=[{'session_id':s['id'],'generation':s['generation'],'kind':s['kind'],**({'type':'working','step':'preparing'} if s['phase'] in {'working','requested'} else s.get('view',{'type':'check_required'}))} for s in self.sessions.values() if s['actor']==actor.id and s['phase'] not in {'complete','aborted','cancelled'}]
        return report

    async def preview(self,actor,payload):
        await self.admin(actor)
        if not self.engine.controls:raise ProductError('read_only','Integration setup is disabled in read-only evaluation.')
        if not isinstance(payload,dict) or set(payload)!={'kind'} or not isinstance(payload['kind'],str) or payload['kind'] not in KINDS:raise ProductError('invalid_input','Choose ZHA, Zigbee2MQTT or an MQTT connection.')
        report=await self.adapter.status();kind=payload['kind']
        if kind=='zha' and any(e['domain']=='zha' for e in report['integrations']):raise ProductError('already_configured','ZHA is already configured. Open Add a device to pair devices.')
        if kind=='mqtt' and any(e['domain']=='mqtt' for e in report['integrations']):raise ProductError('already_configured','MQTT is already configured for this home.')
        if kind=='zigbee2mqtt' and not report['supervised']:raise ProductError('not_supported','Managed Zigbee2MQTT installation requires Home Assistant OS.')
        nonce=secrets.token_urlsafe(32);self.reviews[nonce]={'actor':actor.id,'kind':kind,'expires':self.clock()+300}
        while len(self.reviews)>32:self.reviews.popitem(last=False)
        return {'approval_nonce':nonce,'kind':kind,'writes':False,'existing_networks_preserved':True,'needs_coordinator':kind!='mqtt','third_party_software':kind=='zigbee2mqtt'}

    async def begin(self,actor,payload):
        await self.admin(actor)
        if not self.engine.controls:raise ProductError('read_only','Integration setup is disabled in read-only evaluation.')
        if not isinstance(payload,dict) or set(payload)!={'approval_nonce','confirmed'} or payload['confirmed'] is not True:raise ProductError('confirmation_required','Review and approve this setup first.')
        review=self.reviews.get(payload['approval_nonce']) if isinstance(payload['approval_nonce'],str) else None
        if not review or review['actor']!=actor.id or review['expires']<self.clock():raise ProductError('approval_expired','Review this setup again.')
        if self.lock.locked():raise ProductError('busy','Another integration setup is responding.')
        async with self.lock:
            await self.admin(actor)
            if any(s['actor']==actor.id and s['phase'] not in {'complete','cancelled','aborted'} for s in self.sessions.values()):raise ProductError('busy','Finish or cancel your open setup before starting another.')
            # Reclaim completed/cancelled receipts before refusing a new setup.
            # Active or uncertain flows always require deliberate reconciliation.
            for identity,old in list(self.sessions.items()):
                if len(self.sessions)<32:break
                if old['phase'] in {'complete','cancelled','aborted'}:self.sessions.pop(identity)
            if len(self.sessions)>=32:raise ProductError('busy','Integration setup capacity reached. Finish existing setups or restart the service.')
            self.reviews.pop(payload['approval_nonce']);identity=secrets.token_urlsafe(24)
            session={'id':identity,'actor':actor.id,'kind':review['kind'],'phase':'requested','expires':self.clock()+900,'generation':0,'receipts':{},'handle':None}
            self.sessions[identity]=session
            try:
                handle,result=await self.adapter.begin(session['kind']);session['handle']=handle
                return self.present(session,result)
            except Exception:
                session['phase']='check_required'
                raise ProductError('setup_attention','Setup did not confirm a result. Check Integrations before starting again.') from None

    def present(self,session,result):
        session['phase']=result['type'];session['view']=result;session['generation']+=1
        return {'session_id':session['id'],'generation':session['generation'],'kind':session['kind'],**result}

    def owned(self,actor,identity):
        session=self.sessions.get(identity) if isinstance(identity,str) else None
        if not session or session['actor']!=actor.id:raise ProductError('not_allowed','This setup belongs to another account or is no longer available.')
        if session['expires']<self.clock():raise ProductError('setup_expired','This setup expired. Cancel it before starting again.')
        return session

    async def step(self,actor,payload):
        await self.admin(actor)
        if not self.engine.controls:raise ProductError('read_only','Integration setup is disabled in read-only evaluation.')
        if not isinstance(payload,dict) or set(payload)!={'session_id','generation','input','request_id'} or type(payload['generation']) is not int or not isinstance(payload['input'],dict) or not isinstance(payload['request_id'],str) or not 8<=len(payload['request_id'])<=80:raise ProductError('invalid_input','Complete the current setup step.')
        session=self.owned(actor,payload['session_id']);request=payload['request_id']
        if request in session['receipts']:return session['receipts'][request]
        if payload['generation']!=session['generation'] or session['phase'] not in {'form','menu','progress','progress_done'}:raise ProductError('state_changed','This setup changed. Check its current status.')
        if self.lock.locked():raise ProductError('busy','Setup is responding. Do not resubmit this step.')
        async with self.lock:
            await self.admin(actor)
            # Consume a step before invoking a native flow; timeouts never replay radio writes.
            session['phase']='working';session['receipts'][request]={'session_id':session['id'],'type':'check_required','retry_automatically':False}
            while len(session['receipts'])>64:session['receipts'].pop(next(iter(session['receipts'])))
            try:result=await self.adapter.step(session['kind'],session['handle'],payload['input'])
            except ProductError:
                session['phase']='check_required';session['view']={'type':'check_required'};raise
            except Exception:
                session['phase']='check_required';session['view']={'type':'check_required'};raise ProductError('setup_attention','The result could not be confirmed. Check Integrations before trying another setup.') from None
            response=self.present(session,result);session['receipts'][request]=response;return response

    async def cancel(self,actor,payload):
        await self.admin(actor)
        if not isinstance(payload,dict) or set(payload)!={'session_id'}:raise ProductError('invalid_input','Choose your current setup.')
        session=self.sessions.get(payload['session_id']) if isinstance(payload['session_id'],str) else None
        if not session or session['actor']!=actor.id:raise ProductError('not_allowed','This setup is not yours.')
        if self.lock.locked():raise ProductError('busy','Wait for the current step to finish before cancelling.')
        if session['handle'] and session['phase'] not in {'complete','aborted','cancelled'}:await self.adapter.cancel(session['kind'],session['handle'])
        session['phase']='cancelled';return {'cancelled':True,'already_created_integrations_removed':False}

    async def close(self):
        for session in self.sessions.values():
            if session['handle'] and session['phase'] not in {'complete','aborted','cancelled'}:
                try:await self.adapter.cancel(session['kind'],session['handle'])
                except Exception:pass
