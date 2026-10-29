"""Narrow ZHA/Zigbee2MQTT adapter. No generic MQTT or radio command endpoint."""
from __future__ import annotations
import asyncio
import hashlib
import json
import re
import uuid

from homeassistant.core import Context,callback
from homeassistant.helpers import device_registry as dr,entity_registry as er
from homeassistant.helpers.storage import Store
from .engine import DOMAINS,ProductError

BASE=re.compile(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*\Z')
IEEE=re.compile(r'0x[0-9a-fA-F]{16}\Z')


def opaque(value):return hashlib.sha256(value.encode()).hexdigest()[:24]


class HAPairing:
    def __init__(self,hass,entry):
        self.hass=hass;self.entry=entry;self.store=Store(hass,1,'vautomate_studio.pairing.v1')
        self.bridges={};self.pending={};self.unsubs=[];self.mqtt_identity=None;self.observe_lock=asyncio.Lock()

    async def authorize(self,identity):
        user=await self.hass.auth.async_get_user(identity)
        if user is None or not user.is_active or not user.is_admin or user.system_generated:raise ProductError('not_allowed','An active home administrator is required.')

    async def load(self):
        value=await self.store.async_load()
        if value is None:return None
        required={'id','actor','controller_id','room_id','phase','started_at','deadline','baseline'}
        if not isinstance(value,dict) or set(value)!=required or any(not isinstance(value[k],str) for k in ['id','actor','controller_id','room_id','phase']) or any(type(value[k]) not in {int,float} for k in ['started_at','deadline']) or not isinstance(value['baseline'],list) or len(value['baseline'])>512 or any(not isinstance(i,str) for i in value['baseline']):raise ProductError('storage_attention','Pairing records need recovery. The existing record has been kept.')
        return value

    async def save(self,value):await self.store.async_save(value)

    def mqtt(self):
        from homeassistant.components import mqtt
        return mqtt

    def connected(self):
        try:return self.mqtt().is_connected(self.hass)
        except (ImportError,KeyError,AttributeError):return False

    async def observe(self):
        if not self.connected():return
        mqtt=self.mqtt();identity=id(self.hass.data.get(mqtt.DATA_MQTT))
        async with self.observe_lock:
            if self.mqtt_identity==identity:return
            await self.close()
            prefixes={'+'};configured=self.entry.options.get('zigbee2mqtt_base_topic')
            if isinstance(configured,str) and '/' in configured and len(configured)<=100 and BASE.fullmatch(configured):prefixes.add(configured)
            try:
                for prefix in sorted(prefixes):
                    for suffix in ['state','info','devices','response/health_check','response/permit_join']:
                        self.unsubs.append(await mqtt.async_subscribe(self.hass,prefix+'/bridge/'+suffix,self.message,qos=0))
                self.mqtt_identity=identity
            except Exception:
                await self.close()
                raise ProductError('network_unavailable','Zigbee discovery is not available yet.') from None

    async def close(self):
        for unsub in self.unsubs:unsub()
        self.unsubs=[];self.mqtt_identity=None;self.bridges.clear()
        for future in self.pending.values():
            if not future.done():future.cancel()
        self.pending.clear()

    @callback
    def message(self,message):
        raw=message.payload
        if not isinstance(raw,str) or len(raw)>2_000_000:return
        base,separator,kind=message.topic.partition('/bridge/')
        if not separator or len(base)>100 or not BASE.fullmatch(base):return
        try:data=json.loads(raw)
        except (ValueError,TypeError):return
        if kind.startswith('response/'):
            if not isinstance(data,dict) or not isinstance(data.get('transaction'),str):return
            future=self.pending.get((base,kind,data['transaction']))
            if future and not future.done():
                detail=data.get('data') if isinstance(data.get('data'),dict) else {}
                future.set_result({'ok':data.get('status')=='ok','time':detail.get('time'),'healthy':detail.get('healthy') is True})
            return
        if base not in self.bridges and len(self.bridges)>=16:return
        bridge=self.bridges.setdefault(base,{'online':False,'devices':[],'devices_known':False,'oversized':False})
        if kind=='state' and isinstance(data,dict):bridge['online']=data.get('state')=='online'
        elif kind=='info' and isinstance(data,dict):bridge['permit_join']=data.get('permit_join') is True
        elif kind=='devices' and isinstance(data,list):
            bridge['oversized']=len(data)>512;bridge['devices_known']=True;devices=[]
            for item in data[:512]:
                if not isinstance(item,dict) or item.get('type')=='Coordinator' or item.get('disabled'):continue
                ieee=item.get('ieee_address')
                if not isinstance(ieee,str) or not IEEE.fullmatch(ieee):continue
                definition=item.get('definition') if isinstance(item.get('definition'),dict) else {}
                name=item.get('friendly_name');name=name if isinstance(name,str) else 'New device'
                devices.append({'ieee':ieee.lower(),'id':opaque(base+':'+ieee.lower()),'name':name[:100],'interview':item.get('interview_state'),'supported':item.get('supported') is True,'model':str(definition.get('model') or '')[:80]})
            bridge['devices']=devices

    async def controllers(self):
        try:await self.observe()
        except ProductError:pass
        result=[]
        for entry in self.hass.config_entries.async_entries('zha'):
            result.append({'id':'zha:'+entry.entry_id,'name':entry.title or 'Zigbee network','kind':'zha','online':getattr(entry.state,'value',entry.state)=='loaded' and self.hass.services.has_service('zha','permit')})
        for base,bridge in self.bridges.items():
            result.append({'id':'z2m:'+opaque(base),'name':'Zigbee2MQTT · '+base,'kind':'zigbee2mqtt','online':self.connected() and bridge['online'] and bridge['devices_known'] and not bridge['oversized'],'permit_join':bridge.get('permit_join',False)})
        return result

    def entities(self,device_id):
        result=[]
        for entity in er.async_get(self.hass).entities.values():
            if entity.device_id!=device_id or entity.disabled_by or entity.entity_category:continue
            state=self.hass.states.get(entity.entity_id)
            if state is None or entity.entity_id.split('.')[0] not in DOMAINS:continue
            result.append({'entity_id':entity.entity_id,'name':str(state.attributes.get('friendly_name') or entity.entity_id)[:100]})
        return sorted(result,key=lambda e:e['entity_id'])[:64]

    async def devices(self,identity):
        registry=dr.async_get(self.hass)
        if identity.startswith('zha:'):
            entry_id=identity[4:]
            return [{'id':device.id,'name':device.name_by_user or device.name or 'New device','stage':'ready' if (entities:=self.entities(device.id)) else 'preparing','entities':entities} for device in registry.devices.values() if entry_id in device.config_entries]
        pair=next(((base,b) for base,b in self.bridges.items() if identity=='z2m:'+opaque(base)),None)
        if not pair:raise ProductError('network_unavailable','Reconnect to your Zigbee network.')
        base,bridge=pair
        if not bridge['devices_known'] or bridge['oversized']:raise ProductError('network_attention','This network needs installer review before pairing.')
        result=[]
        for item in bridge['devices']:
            device=next((d for d in registry.devices.values() if any(domain=='mqtt' and item['ieee'] in value.lower() for domain,value in d.identifiers)),None)
            entities=self.entities(device.id) if device else []
            stage='failed' if item['interview']=='FAILED' else 'ready' if item['interview']=='SUCCESSFUL' and item['supported'] and entities else 'preparing'
            result.append({'id':item['id'],'name':item['name'],'stage':stage,'entities':entities,'model':item['model']})
        return result

    async def request_bridge(self,base,kind,data):
        if kind not in {'health_check','permit_join'}:raise ProductError('not_allowed','Unsupported network action.')
        if not self.connected() or not self.bridges.get(base,{}).get('online'):raise ProductError('network_unavailable','Your Zigbee network is disconnected.')
        transaction=uuid.uuid4().hex;key=(base,'response/'+kind,transaction);future=asyncio.get_running_loop().create_future();self.pending[key]=future
        try:
            await self.mqtt().async_publish(self.hass,base+'/bridge/request/'+kind,json.dumps({**data,'transaction':transaction}),qos=0,retain=False)
            return await asyncio.wait_for(future,8)
        finally:self.pending.pop(key,None)

    async def permit(self,user_id,identity,duration):
        if type(duration) is not int or duration not in {0,60}:raise ProductError('invalid_input','Pairing windows must be bounded.')
        await self.authorize(user_id)
        controllers=await self.controllers()
        if not any(c['id']==identity and (c['online'] or duration==0) for c in controllers):raise ProductError('network_unavailable','Your Zigbee network is not ready.')
        if identity.startswith('zha:'):
            await asyncio.wait_for(self.hass.services.async_call('zha','permit',{'duration':duration},blocking=True,context=Context(user_id=user_id)),10)
            return True
        base=next(base for base in self.bridges if identity=='z2m:'+opaque(base))
        if duration:
            health=await self.request_bridge(base,'health_check',{})
            if not health['ok'] or not health['healthy']:return False
        result=await self.request_bridge(base,'permit_join',{'time':duration})
        return result['ok'] and type(result['time']) is int and result['time']==duration
