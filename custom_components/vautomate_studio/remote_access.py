"""Administrator-owned Tailscale setup; no generic app, ingress or network proxy."""
from __future__ import annotations
import asyncio
import ipaddress
import re
import secrets
import time
from urllib.parse import urlsplit
from .engine import ProductError

SLUG='a0d7b954_tailscale'
REPOSITORY='https://github.com/hassio-addons/repository'

def login_url(value):
    if not isinstance(value,str) or len(value)>1024:return None
    try:u=urlsplit(value)
    except ValueError:return None
    if u.scheme!='https' or u.netloc!='login.tailscale.com' or u.query or u.fragment or not re.fullmatch(r'/a/[A-Za-z0-9_-]+',u.path):return None
    return value

def node_view(data,port):
    if not isinstance(data,dict) or data.get('Status') not in {'Running','NeedsLogin','NeedsMachineAuth','Stopped','Starting','NoState','InUseOtherUser'}:
        raise ProductError('remote_status_unavailable','Tailscale status could not be verified. Check again shortly.')
    address=None
    try:
        ip=ipaddress.ip_address(data.get('IPv4',''))
        if ip in ipaddress.ip_network('100.64.0.0/10'):address=str(ip)
    except ValueError:pass
    connected=data['Status']=='Running' and data.get('KeyExpired') is not True and bool(address)
    return {'vpn_state':data['Status'],'connected':connected,'key_expired':data.get('KeyExpired') is True,
            'key_expiry':str(data.get('KeyExpiry') or '')[:64],
            'remote_address':f'http://{address}:{port}' if connected else None,
            'verified_at':time.time()}

class RemoteAccess:
    def __init__(self,engine,adapter,clock=time.monotonic):
        self.engine=engine;self.adapter=adapter;self.clock=clock;self.reviews={};self.task=None;self.phase=None;self.failure=None

    async def admin(self,actor):self.engine.admin(actor);await self.adapter.authorize(actor.id)

    async def status(self,actor):
        await self.admin(actor)
        try:report=await self.adapter.status(actor.id)
        except ProductError:raise
        except Exception:raise ProductError('remote_status_unavailable','Remote access status is unavailable. Check the home connection and try again.') from None
        return {**report,'phase':self.phase,'failure':self.failure,'phone_client_required':True,'public_sharing_enabled':False if not report.get('configuration_attention') else None}

    async def preview(self,actor,payload):
        await self.admin(actor)
        if payload!={}:raise ProductError('invalid_input','Review remote access without extra settings.')
        if not self.engine.controls:raise ProductError('read_only','Remote access setup is disabled in read-only evaluation.')
        report=await self.status(actor)
        if not report['supported']:raise ProductError('not_supported','Managed remote access requires Home Assistant OS.')
        if report.get('configuration_attention'):raise ProductError('existing_configuration','The existing Tailscale app uses advanced sharing settings. Have your installer review it; its configuration was kept.')
        nonce=secrets.token_urlsafe(32)
        self.reviews={k:v for k,v in self.reviews.items() if v['expires']>self.clock()}
        if len(self.reviews)>=32:raise ProductError('busy','Remote setup is busy. Try again shortly.')
        self.reviews[nonce]={'actor':actor.id,'expires':self.clock()+300}
        return {'approval_nonce':nonce,'installed':report['installed'],'writes':False,'start_on_boot':True,'automatic_updates':False,'requires_customer_tailscale_account':True}

    async def enable(self,actor,payload):
        await self.admin(actor)
        if not self.engine.controls:raise ProductError('read_only','Remote access setup is disabled in read-only evaluation.')
        if not isinstance(payload,dict) or set(payload)!={'approval_nonce','confirmed'} or payload['confirmed'] is not True:raise ProductError('confirmation_required','Approve enabling private remote access first.')
        review=self.reviews.get(payload['approval_nonce']) if isinstance(payload['approval_nonce'],str) else None
        if not review or review['actor']!=actor.id or review['expires']<self.clock():raise ProductError('approval_expired','Review remote access again.')
        if self.task and not self.task.done():raise ProductError('busy','Remote access setup is already running. Check its progress.')
        self.reviews.pop(payload['approval_nonce']);self.phase='installing';self.failure=None
        self.task=asyncio.create_task(self._enable(actor))
        return {'phase':self.phase,'accepted':True,'retry_automatically':False}

    async def _enable(self,actor):
        try:
            await self.adapter.journal('requested')
            await self.admin(actor)
            await self.adapter.install()
            self.phase='starting'
            await self.admin(actor)
            await self.adapter.start()
            await self.adapter.journal('ready');self.phase='ready'
        except Exception:
            self.phase='attention';self.failure='Setup did not confirm completion. Check status before trying again. Your existing network settings were kept.'
            try:await self.adapter.journal('check_required')
            except Exception:pass

    async def signin(self,actor,payload):
        await self.admin(actor)
        if not self.engine.controls:raise ProductError('read_only','Remote access setup is disabled in read-only evaluation.')
        if payload!={}:raise ProductError('invalid_input','Start sign-in without extra settings.')
        if self.task and not self.task.done():raise ProductError('busy','Wait for installation to finish.')
        try:
            report=await self.adapter.status(actor.id)
            if report.get('connected'):return {'connected':True,'url':None}
            if not report.get('installed') or report.get('app_state')!='started':raise ProductError('remote_not_started','Enable remote access and wait for Tailscale to start first.')
            if report.get('configuration_attention'):raise ProductError('existing_configuration','Have your installer review the existing advanced Tailscale configuration.')
            result=await self.adapter.signin(actor.id)
            url=login_url(result.get('url'))
            if result.get('url') and not url:raise ProductError('remote_signin_unavailable','Tailscale returned an unexpected sign-in address. Check for a compatible app update.')
            return {'url':url,'connected':False,'check_status':True}
        except ProductError:raise
        except Exception:raise ProductError('remote_signin_unavailable','Sign-in did not return a result. Check status before starting it again.') from None

    async def disable(self,actor,payload):
        await self.admin(actor)
        if not self.engine.controls:raise ProductError('read_only','Remote access changes are disabled in read-only evaluation.')
        if payload!={'confirmed':True}:raise ProductError('confirmation_required','Confirm turning off remote access. A remote connection may be interrupted.')
        if self.task and not self.task.done():raise ProductError('busy','Wait for the current setup to finish.')
        self.phase='stopping';self.failure=None;self.task=asyncio.create_task(self._disable(actor))
        return {'accepted':True,'account_kept':True,'retry_automatically':False}

    async def _disable(self,actor):
        try:
            await self.adapter.journal('stop_requested');await self.admin(actor)
            await self.adapter.stop();await self.adapter.journal('disabled');self.phase='disabled'
        except Exception:self.phase='attention';self.failure='The stop was not confirmed. Check status before trying again.'

    async def shutdown(self):
        if self.task and not self.task.done():
            self.task.cancel()
            try:await self.task
            except asyncio.CancelledError:pass

class HARemote:
    def __init__(self,hass,integrations):
        from homeassistant.helpers.storage import Store
        self.hass=hass;self.integrations=integrations;self.authorize=integrations.authorize;self.sessions={};self.store=Store(hass,1,'vautomate_studio.remote_access.v1')

    async def journal(self,stage):await self.store.async_save({'stage':stage,'app':SLUG})
    async def supervisor(self,*args,**kwargs):return await self.integrations.supervisor(*args,**kwargs)

    async def info(self):
        apps=await self.supervisor('/addons')
        if not any(a['slug']==SLUG for a in apps.get('addons',[])):return None
        return await self.supervisor('/addons/'+SLUG+'/info')

    def advanced(self,info):
        options=info.get('options',{})
        return bool(options.get('login_server','https://controlplane.tailscale.com')!='https://controlplane.tailscale.com' or options.get('advertise_routes') or options.get('advertise_exit_node') or options.get('advertise_connector') or options.get('share_homeassistant','disabled')!='disabled' or options.get('services') or options.get('exit_node') or options.get('taildrop') or any(options.get('taildrive',{}).values()))

    async def status(self,user_id):
        supported='hassio' in self.hass.config.components
        report={'supported':supported,'installed':False,'connected':False,'app_state':'not_installed','start_on_boot':False,'watchdog':False,'automatic_updates':False,'remote_address':None}
        if not supported:return report
        info=await self.info()
        if info is None:return report
        report.update(installed=True,app_state=info['state'],start_on_boot=info.get('boot')=='auto',watchdog=info.get('watchdog') is True,automatic_updates=info.get('auto_update') is True,configuration_attention=self.advanced(info))
        if info['state']=='started':
            try:report.update(node_view(await self.web(user_id,'GET','data'),self.hass.http.server_port))
            except Exception:report['status_attention']=True
        return report

    async def install(self):
        info=await self.info()
        if info is None:
            store=await self.supervisor('/store')
            if not any(a['slug']==SLUG for a in store.get('addons',[])):
                repositories=[r['source'] for r in store.get('repositories',[])]
                if REPOSITORY not in repositories:await self.supervisor('/store/repositories','post',{'repositories':repositories+[REPOSITORY]})
                await self.supervisor('/store/reload','post')
                store=await self.supervisor('/store')
            if not any(a['slug']==SLUG for a in store.get('addons',[])):raise ProductError('remote_app_unavailable','The official Tailscale app is not available in this server’s app store.')
            await self.supervisor('/addons/'+SLUG+'/install','post',timeout=180)
            info=await self.info()
            if info is None:raise ProductError('remote_install_unconfirmed','Tailscale installation did not confirm completion.')
            options=dict(info.get('options',{}));options.update(accept_dns=False,accept_routes=False,advertise_routes=[],advertise_exit_node=False,share_homeassistant='disabled')
            for key,value in {'advertise_connector':False,'taildrop':False,'services':[]}.items():
                if key in options:options[key]=value
            if 'taildrive' in options:options['taildrive']={key:False for key in options['taildrive']}
            await self.supervisor('/addons/'+SLUG+'/options','post',{'options':options,'auto_update':False})
        elif self.advanced(info):raise ProductError('existing_configuration','Advanced sharing settings were kept. Ask your installer to review this app.')
        await self.supervisor('/addons/'+SLUG+'/options','post',{'boot':'auto','watchdog':True,'auto_update':False})

    async def start(self):
        info=await self.info()
        if info is None:raise ProductError('remote_app_unavailable','Install Tailscale first.')
        if info['state']!='started':await self.supervisor('/addons/'+SLUG+'/start','post',timeout=90)

    async def stop(self):
        info=await self.info()
        if info is None:return
        await self.supervisor('/addons/'+SLUG+'/options','post',{'boot':'manual','watchdog':False})
        if info['state']=='started':await self.supervisor('/addons/'+SLUG+'/stop','post',timeout=90)

    async def signin(self,user_id):return await self.web(user_id,'POST','up',{'Reauthenticate':False})

    async def web(self,user_id,method,operation,body=None):
        # Only the fixed Tailscale app and its two documented web endpoints.
        if (method,operation) not in {('GET','data'),('POST','up')}:raise ProductError('not_allowed','Unsupported remote access action.')
        from homeassistant.helpers.aiohttp_client import async_get_clientsession
        import aiohttp
        info=await self.info();entry=(info or {}).get('ingress_entry','')
        if not re.fullmatch(r'/api/hassio_ingress/[A-Za-z0-9_-]+/?',entry):raise ProductError('remote_status_unavailable','Tailscale’s secure setup interface is not ready.')
        cached=self.sessions.get(user_id)
        if not cached or cached[0]<time.monotonic():
            session=await self.supervisor('/ingress/session','post',{'user_id':user_id})
            token=session.get('session')
            if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',token):raise ProductError('remote_status_unavailable','A secure remote setup session could not be created.')
            cached=(time.monotonic()+240,token)
            self.sessions={k:v for k,v in self.sessions.items() if v[0]>time.monotonic()}
            if len(self.sessions)>=32:self.sessions.pop(next(iter(self.sessions)))
            self.sessions[user_id]=cached
        path=entry.replace('/api/hassio_ingress/','/ingress/',1).rstrip('/')+'/api/'+operation
        async with async_get_clientsession(self.hass).request(method,'http://supervisor'+path,json=body if method=='POST' else None,cookies={'ingress_session':cached[1]},headers={'Origin':'http://supervisor'},timeout=aiohttp.ClientTimeout(total=18),allow_redirects=False) as response:
            if response.status!=200:
                if response.status in {401,403}:self.sessions.pop(user_id,None)
                raise ProductError('remote_status_unavailable','Tailscale’s setup interface could not confirm this request. Check status before trying again.')
            raw=await response.content.read(65537)
            if len(raw)>65536:raise ProductError('remote_status_unavailable','The remote status response was larger than expected.')
            import json
            return json.loads(raw)
