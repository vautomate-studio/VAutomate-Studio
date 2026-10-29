"""Bounded reviewed pairing and explicit room placement. No automatic admission or replay."""
from __future__ import annotations
import asyncio
from collections import OrderedDict
from copy import deepcopy
import secrets
import time
import uuid

from .engine import ProductError


class Pairing:
    def __init__(self,engine,adapter,*,clock=time.monotonic,wall=time.time):
        self.engine=engine;self.adapter=adapter;self.clock=clock;self.wall=wall
        self.lock=asyncio.Lock();self.reviews=OrderedDict();self.receipts=OrderedDict();self.session=None

    async def initialize(self):
        self.session=await self.adapter.load()
        if self.session and self.session.get('phase') not in {'closed','assigned'}:
            self.session['phase']='interrupted'
            await self.adapter.save(self.session)

    async def admin(self,actor):
        self.engine.admin(actor)
        await self.adapter.authorize(actor.id)

    def remember(self,cache,key,value,limit=32):
        cache[key]=value
        while len(cache)>limit:cache.popitem(last=False)

    async def controller(self,identity):
        item=next((c for c in await self.adapter.controllers() if c['id']==identity),None)
        if not item or not item['online']:raise ProductError('network_unavailable','This Zigbee network is not ready. Check its connection before pairing.')
        return item

    async def status(self,actor):
        await self.admin(actor)
        controllers=await self.adapter.controllers()
        result={'controllers':controllers,'session':None,'can_start':self.engine.controls,'hardware_certified':False,'automatic_pairing':False}
        if self.session:
            session=self.session;public={key:deepcopy(session[key]) for key in ['id','controller_id','room_id','phase','started_at','deadline']}
            public['seconds_remaining']=max(0,min(60,int(session['deadline']-self.wall())))
            if public['seconds_remaining']==0 and public['phase']=='listening':public['phase']='window_finished'
            baseline=set(session.get('baseline',[]))
            try:devices=await self.adapter.devices(session['controller_id'])
            except Exception:devices=[];public['network_attention']=True
            public['devices']=[device for device in devices if device['id'] not in baseline][:64]
            result['session']=public
        return result

    async def preview(self,actor,payload):
        await self.admin(actor)
        if not self.engine.controls:raise ProductError('read_only','Pairing is disabled while this installation is in read-only evaluation mode.')
        if not isinstance(payload,dict) or set(payload)!={'controller_id','room_id'}:raise ProductError('invalid_input','Choose a Zigbee network and a room.')
        controller=await self.controller(payload['controller_id'])
        room=next((r for r in self.engine.document['layout']['rooms'] if r['id']==payload['room_id']),None)
        if not room:raise ProductError('invalid_input','Choose an existing room before adding a device.')
        nonce=secrets.token_urlsafe(32)
        plan={'controller_id':controller['id'],'controller_name':controller['name'],'room_id':room['id'],'room_name':room['name'],'duration':60}
        self.remember(self.reviews,nonce,{'actor':actor.id,'expires':self.clock()+300,'plan':plan})
        return {'approval_nonce':nonce,'plan':deepcopy(plan),'writes':False,'opens_network':False}

    async def begin(self,actor,payload):
        await self.admin(actor)
        if not self.engine.controls:raise ProductError('read_only','Pairing is disabled in read-only evaluation mode.')
        if not isinstance(payload,dict) or set(payload)!={'approval_nonce','ready'} or payload['ready'] is not True:raise ProductError('confirmation_required','Confirm that your device is ready to pair.')
        nonce=payload['approval_nonce'];key=(actor.id,nonce) if isinstance(nonce,str) else None
        if key in self.receipts:return deepcopy(self.receipts[key])
        review=self.reviews.get(nonce) if isinstance(nonce,str) else None
        if not review or review['actor']!=actor.id or review['expires']<self.clock():raise ProductError('approval_expired','Review this pairing request again.')
        if self.lock.locked():raise ProductError('busy','Your Zigbee network is already responding. Check its status.')
        async with self.lock:
            await self.admin(actor)
            if self.session and self.session['phase'] not in {'closed','assigned'}:raise ProductError('busy','Close the previous pairing window before opening another.')
            plan=review['plan'];await self.controller(plan['controller_id'])
            room=next((r for r in self.engine.document['layout']['rooms'] if r['id']==plan['room_id']),None)
            if not room or room['name']!=plan['room_name']:raise ProductError('state_changed','This room changed. Review pairing again.')
            baseline=await self.adapter.devices(plan['controller_id'])
            if len(baseline)>512:raise ProductError('network_too_large','This network needs installer review before adding devices.')
            record={'id':uuid.uuid4().hex,'actor':actor.id,'controller_id':plan['controller_id'],'room_id':plan['room_id'],'phase':'requested','started_at':self.wall(),'deadline':self.wall()+60,'baseline':[d['id'] for d in baseline][:512]}
            # Journal before admission. Restarting invalidates a review, never reopens a network.
            await self.adapter.save(record);self.session=record;del self.reviews[nonce]
            receipt={'session_id':record['id'],'status':'check_required','retry_automatically':False};self.remember(self.receipts,key,receipt,64)
            try:
                accepted=await self.adapter.permit(actor.id,record['controller_id'],60)
                record['phase']='listening' if accepted else 'check_required'
                receipt['status']='listening' if accepted else 'check_required'
            except asyncio.CancelledError:raise
            except Exception:record['phase']='check_required'
            finally:await self.adapter.save(record)
            self.engine.audit(actor,'pairing_window_requested',None,receipt['status'])
            return deepcopy(receipt)

    async def cancel(self,actor,payload):
        await self.admin(actor)
        if not isinstance(payload,dict) or set(payload)!={'session_id'} or not self.session or payload['session_id']!=self.session['id']:raise ProductError('invalid_input','Choose the current pairing session.')
        if self.session['phase'] in {'closed','assigned'}:return {'status':'closed'}
        if self.lock.locked():raise ProductError('busy','Pairing is responding. Wait for its status, then close it.')
        async with self.lock:
            await self.admin(actor)
            try:accepted=await self.adapter.permit(actor.id,self.session['controller_id'],0)
            except Exception:accepted=False
            self.session['phase']='closed' if accepted else 'check_required'
            await self.adapter.save(self.session)
            return {'status':self.session['phase'],'retry_automatically':False}

    async def assign(self,actor,payload):
        await self.admin(actor)
        if not isinstance(payload,dict) or set(payload)!={'session_id','device_id','room_id','entities','revision'}:raise ProductError('invalid_input','Review the new device and its room.')
        if not self.session or payload['session_id']!=self.session['id']:raise ProductError('state_changed','This pairing session is no longer available.')
        if self.lock.locked():raise ProductError('busy','Pairing is already responding.')
        async with self.lock:
            devices=await self.adapter.devices(self.session['controller_id'])
            device=next((d for d in devices if d['id']==payload['device_id'] and d['id'] not in self.session['baseline']),None)
            if not device or device['stage']!='ready':raise ProductError('device_not_ready','Wait for this device to finish setup before adding its controls.')
            identities=payload['entities']
            if not isinstance(identities,list) or not identities or len(identities)>64 or any(not isinstance(i,str) for i in identities) or len(set(identities))!=len(identities):raise ProductError('invalid_input','Choose the device controls or readings you want in this room.')
            allowed={entity['entity_id'] for entity in device['entities']}
            if any(identity not in allowed for identity in identities):raise ProductError('not_allowed','Only this newly paired device can be placed by this review.')
            layout=deepcopy(self.engine.document['layout']);room=next((r for r in layout['rooms'] if r['id']==payload['room_id']),None)
            if not room:raise ProductError('invalid_input','Choose an existing room.')
            for other in layout['rooms']:
                if other['id']!=room['id'] and any(i in other['entities'] for i in identities):raise ProductError('already_assigned','This device already has a room. Use the dashboard editor to move it.')
            room['entities']=list(dict.fromkeys(room['entities']+identities))
            result=await self.engine.publish(actor,layout,payload['revision'])
            return {**result,'device_id':device['id'],'assigned':True,'device_operated':False}
