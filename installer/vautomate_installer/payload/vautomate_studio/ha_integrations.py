"""Native ZHA/MQTT forms and reviewed official Zigbee2MQTT app installation."""
from __future__ import annotations
import asyncio
import re
import ipaddress
from urllib.parse import urlparse
from copy import deepcopy
from homeassistant.helpers.storage import Store
from .engine import ProductError
from .integration_setup import KINDS

Z2M_REPOSITORY='https://github.com/zigbee2mqtt/hassio-zigbee2mqtt'
Z2M_SLUG='45df7312_zigbee2mqtt'
SAFE_MENUS={'setup_strategy_advanced','reuse_settings','form_initial_network','manual_pick_radio_type','choose_serial_port','broker','addon'}


class HAIntegrations:
    def __init__(self,hass,authorize):self.hass=hass;self.authorize=authorize;self.owned=set();self.store=Store(hass,1,'vautomate_studio.z2m_setup.v1')

    async def supervisor(self,endpoint,method='get',payload=None,timeout=15):
        from homeassistant.components.hassio.const import DATA_COMPONENT
        client=self.hass.data.get(DATA_COMPONENT)
        if client is None:raise ProductError('not_supported','Managed apps require Home Assistant OS.')
        result=await client.send_command(endpoint,method=method,payload=payload or {},timeout=timeout,source='vautomate_studio')
        return result.get('data',result)

    async def serial_ports(self):
        def read():
            try:
                from serial.tools.list_ports import comports
                return [{'value':p.device,'label':str(p.description or p.device)[:100]} for p in comports() if p.vid is not None][:32]
            except ImportError:return []
        return await self.hass.async_add_executor_job(read)

    async def status(self):
        integrations=[{'id':e.entry_id,'domain':e.domain,'name':e.title,'state':str(getattr(e.state,'value',e.state))} for domain in sorted(KINDS-{'zigbee2mqtt'}) for e in self.hass.config_entries.async_entries(domain)]
        report={'integrations':integrations,'serial_ports':await self.serial_ports(),'supervised':'hassio' in self.hass.config.components,'apps':[]}
        if report['supervised']:
            try:
                data=await self.supervisor('/addons')
                report['apps']=[{'id':a['slug'],'name':a['name'],'state':a.get('state'),'version':a.get('version')} for a in data.get('addons',[]) if a['slug'] in {Z2M_SLUG,'core_mosquitto'}]
            except Exception:report['apps_attention']=True
        return report

    def serialize(self,result,domain='zha'):
        kind=str(result['type']);flow=result.get('flow_id')
        if kind=='create_entry':
            self.owned.discard(flow);return {'type':'complete','name':str(result.get('title') or 'Integration'),'message':'Integration added. Return to Devices to select its controls.'}
        if kind=='abort':self.owned.discard(flow);return {'type':'aborted','reason':str(result.get('reason','setup_stopped'))[:100]}
        output={'type':kind,'step':str(result.get('step_id','setup')),'errors':{str(k):str(v)[:100] for k,v in (result.get('errors') or {}).items()}}
        if kind=='menu':
            options=result.get('menu_options',[]);options=list(options) if isinstance(options,dict) else options
            output['options']=[o for o in options if (o in SAFE_MENUS if domain=='zha' else not re.search('reset|erase|migrat|restore|delete|remove',o,re.I))]
            if not output['options']:return {'type':'aborted','reason':'network_migration_requires_specialist_review'}
        elif kind=='form':
            schema=result.get('data_schema')
            if schema is None:fields=[]
            else:
                from homeassistant.helpers import config_validation as cv
                try:
                    import probatio
                    fields=probatio.to_field_list(schema,custom_serializer=cv.custom_serializer)
                except ImportError:
                    import voluptuous_serialize
                    fields=voluptuous_serialize.convert(schema,custom_serializer=cv.custom_serializer)
            # Never return a flow's credential data, suggested passwords or exception placeholders.
            def scrub(node):
                if isinstance(node,list):
                    for child in node:scrub(child)
                elif isinstance(node,dict):
                    if any(word in str(node.get('name','')).lower() for word in ['password','secret','token','credential','key','psk']):node.pop('default',None);node.pop('description',None)
                    if isinstance(node.get('default'),dict):node.pop('default')
                    for child in node.values():scrub(child)
            scrub(fields)
            output['fields']=fields
        elif kind not in {'progress','progress_done'}:return {'type':'aborted','reason':'unsupported_setup_step'}
        return output

    async def begin(self,kind):
        if kind=='zigbee2mqtt':
            marker=await self.store.async_load()
            if marker and marker.get('installed_by_studio') and not marker.get('configured'):
                if marker.get('stage')=='configuration_requested':return 'managed-z2m',{'type':'check_required','message':'A previous coordinator configuration was interrupted. Its result must be checked before any settings are rewritten.'}
                return 'managed-z2m',self.z2m_form()
            return 'managed-z2m',{'type':'form','step':'z2m_install','fields':[{'name':'install_broker','type':'boolean','default':False},{'name':'software_approved','type':'boolean','default':False}]}
        if kind not in KINDS-{'zigbee2mqtt'}:raise ProductError('not_allowed','Unsupported integration.')
        if kind in {'zha','mqtt'} and self.hass.config_entries.async_entries(kind):raise ProductError('already_configured','This integration already exists.')
        result=await self.hass.config_entries.flow.async_init(kind,context={'source':'user','show_advanced_options':False})
        identity=result.get('flow_id');self.owned.add(identity)
        return identity,self.serialize(result,kind)

    async def step(self,kind,handle,values):
        if kind=='zigbee2mqtt':return await (self.z2m_configure(values) if 'adapter' in values else self.z2m_install(values))
        if handle not in self.owned:raise ProductError('not_allowed','This flow is not owned by VAutomate.')
        progress=next((f for f in self.hass.config_entries.flow.async_progress() if f['flow_id']==handle),None)
        if not progress or progress.get('handler')!=kind:raise ProductError('state_changed','Setup is no longer available.')
        if set(values)=={'next_step_id'} and (kind=='zha' and values['next_step_id'] not in SAFE_MENUS or re.search('reset|erase|migrat|restore|delete|remove',str(values['next_step_id']),re.I)):raise ProductError('not_allowed','Destructive network changes are not available in this setup flow.')
        # Do not accept arbitrary nested configuration/code. Native schema validates known fields.
        if len(values)>16 or any(not isinstance(k,str) or len(k)>80 for k in values):raise ProductError('invalid_input','Review setup fields.')
        result=await self.hass.config_entries.flow.async_configure(handle,None if values=={'_refresh':True} else values)
        return self.serialize(result,kind)

    async def cancel(self,kind,handle):
        if kind!='zigbee2mqtt' and handle in self.owned:
            self.hass.config_entries.flow.async_abort(handle);self.owned.discard(handle)

    async def z2m_install(self,values):
        if set(values)!={'install_broker','software_approved'} or values['software_approved'] is not True or type(values['install_broker']) is not bool:raise ProductError('confirmation_required','Approve installing Zigbee2MQTT and choose whether to install its broker.')
        report=await self.status()
        if any(e['domain']=='zha' for e in report['integrations']):raise ProductError('network_in_use','ZHA is already configured. Use a separate coordinator or a reviewed network migration before installing a competing network.')
        # Repository URL is fixed; no caller-controlled repository or app command exists.
        store=await self.supervisor('/store')
        repos=store.get('repositories',[])
        if not any(r.get('source')==Z2M_REPOSITORY or r.get('url')==Z2M_REPOSITORY for r in repos):await self.supervisor('/store/repositories','post',{'repository':Z2M_REPOSITORY},timeout=120)
        installed={a['id'] for a in report['apps']}
        if Z2M_SLUG in installed:raise ProductError('already_configured','An existing Zigbee2MQTT installation was found. Its settings have been kept. Connect its existing MQTT integration instead of replacing its network.')
        await self.store.async_save({'installed_by_studio':True,'configured':False,'stage':'install_requested'})
        if values['install_broker'] and 'core_mosquitto' not in installed:await self.supervisor('/addons/core_mosquitto/install','post',timeout=180)
        if Z2M_SLUG not in installed:await self.supervisor('/addons/'+Z2M_SLUG+'/install','post',timeout=180)
        # Keep manual updates and do not start a radio before its adapter has been selected.
        for slug in [Z2M_SLUG]+(['core_mosquitto'] if values['install_broker'] else []):await self.supervisor('/addons/'+slug+'/options','post',{'auto_update':False})
        await self.store.async_save({'installed_by_studio':True,'configured':False,'stage':'installed'})
        return self.z2m_form()

    def z2m_form(self):
        return {'type':'form','step':'z2m_configure','fields':[{'name':'adapter','type':'select','options':[['ember','Silicon Labs / Ember'],['zstack','Texas Instruments / zStack'],['deconz','deCONZ'],['zigate','ZiGate'],['zboss','ZBOSS']]},{'name':'port','type':'string'},{'name':'baudrate','type':'integer','default':115200},{'name':'broker_mode','type':'select','options':[['existing','Use the configured MQTT connection'],['managed','Use the installed Mosquitto broker']]}]}

    async def z2m_configure(self,values):
        if set(values)!={'adapter','port','baudrate','broker_mode'} or values['adapter'] not in {'ember','zstack','deconz','zigate','zboss'} or values['broker_mode'] not in {'existing','managed'} or type(values['baudrate']) is not int or values['baudrate'] not in {9600,38400,57600,115200,230400,460800}:raise ProductError('invalid_input','Choose your coordinator model, connection and broker.')
        marker=await self.store.async_load()
        if self.hass.config_entries.async_entries('zha'):raise ProductError('network_in_use','ZHA was configured while this setup was open. Stop and review the coordinator before starting another network.')
        if not marker or not marker.get('installed_by_studio') or marker.get('configured'):raise ProductError('not_allowed','This setup cannot overwrite an existing Zigbee network.')
        port=values['port'];ports={p['value'] for p in await self.serial_ports()}
        if not isinstance(port,str):raise ProductError('invalid_input','Choose your coordinator connection.')
        if port not in ports:
            try:
                target=urlparse(port);address=ipaddress.ip_address(target.hostname)
                if target.scheme!='tcp' or not address.is_private or address.is_loopback or not target.port or not 1024<=target.port<=65535 or target.username or target.password or target.path not in {'','/'}:raise ValueError()
            except (TypeError,ValueError):raise ProductError('invalid_input','Choose a detected USB coordinator or a private LAN coordinator such as tcp://192.168.x.x:6638.') from None
        entries=self.hass.config_entries.async_entries('mqtt')
        if entries:
            broker=deepcopy(entries[0].data)
            if broker.get('transport','tcp')!='tcp' or any(broker.get(k) for k in ['certificate','client_cert','client_key']):raise ProductError('not_supported','This MQTT connection uses custom transport or certificates. Its security settings were kept; a compatible bridge profile is required.')
        else:
            if values['broker_mode']!='managed':raise ProductError('mqtt_required','Add this homeÃ¢â‚¬â„¢s MQTT connection first, then resume Zigbee2MQTT setup.')
            await self.supervisor('/addons/core_mosquitto/start','post',timeout=120)
            service=await self.supervisor('/services/mqtt');broker={'broker':service['host'],'port':service.get('port',1883),'username':service.get('username'),'password':service.get('password')}
            # Native flow validates the connection, rather than writing a config entry directly.
            flow=await self.hass.config_entries.flow.async_init('mqtt',context={'source':'user'})
            flow=await self.hass.config_entries.flow.async_configure(flow['flow_id'],{'next_step_id':'broker'})
            flow=await self.hass.config_entries.flow.async_configure(flow['flow_id'],{**broker,'protocol':'3.1.1','other_settings':{}})
            if str(flow['type'])!='create_entry':
                if flow.get('flow_id'):self.hass.config_entries.flow.async_abort(flow['flow_id'])
                raise ProductError('mqtt_connection_failed','The broker did not confirm a connection. Check MQTT status before starting a radio.')
        info=await self.supervisor('/addons/'+Z2M_SLUG+'/info');options=deepcopy(info.get('options',{}))
        options.update(data_path='/config/vautomate_studio_zigbee2mqtt',serial={'port':port,'adapter':values['adapter'],'baudrate':values['baudrate']},mqtt={'server':'mqtt://'+str(broker['broker'])+':'+str(broker.get('port',1883)),'user':broker.get('username') or '','password':broker.get('password') or '','base_topic':'zigbee2mqtt'})
        await self.store.async_save({**marker,'stage':'configuration_requested'})
        await self.supervisor('/addons/'+Z2M_SLUG+'/options','post',{'options':options,'auto_update':False})
        await self.supervisor('/addons/'+Z2M_SLUG+'/start','post',timeout=120)
        await self.store.async_save({'installed_by_studio':True,'configured':True,'stage':'started'})
        return {'type':'complete','name':'Zigbee2MQTT connected','message':'Coordinator settings were saved and the bridge was started. Check its online status before pairing. No join window was opened.'}
