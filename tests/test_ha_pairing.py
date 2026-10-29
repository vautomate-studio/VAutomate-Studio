"""Inert radio adapters. These tests do not certify a coordinator or device."""
import asyncio
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from test_engine import ProductError

path=Path(__file__).resolve().parents[1]/'custom_components/vautomate_studio/ha_pairing.py'
spec=importlib.util.spec_from_file_location('studio_product.ha_pairing',path);module=importlib.util.module_from_spec(spec)
class Store:
    def __init__(self,*args):self.value=None
    async def async_load(self):return self.value
    async def async_save(self,value):self.value=value
with patch.dict(sys.modules,{'homeassistant.core':NS(Context=lambda **kw:kw,callback=lambda f:f),'homeassistant.helpers':NS(device_registry=NS(async_get=lambda h:h.devices),entity_registry=NS(async_get=lambda h:h.entities)),'homeassistant.helpers.storage':NS(Store=Store)}):spec.loader.exec_module(module)

class MQTT:
    DATA_MQTT='mqtt'
    def __init__(self):self.connected=True;self.published=[];self.callbacks=[];self.reply=True;self.status='ok'
    def is_connected(self,hass):return self.connected
    async def async_subscribe(self,hass,topic,callback,qos):self.callbacks.append((topic,callback));return lambda:None
    async def async_publish(self,hass,topic,payload,**options):
        data=json.loads(payload);self.published.append((topic,data,options));kind=topic.split('/request/')[1]
        if self.reply:self.callback(NS(topic=topic.replace('/request/','/response/'),payload=json.dumps({'status':self.status,'transaction':data['transaction'],'data':{'healthy':True} if kind=='health_check' else {'time':data['time']}})))

class PairingAdapterTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user=NS(is_active=True,is_admin=True,system_generated=False)
        async def get_user(identity):return self.user
        self.calls=[]
        async def call(*args,**kwargs):self.calls.append((args,kwargs))
        self.entries=[];self.hass=NS(auth=NS(async_get_user=get_user),data={'mqtt':object()},config_entries=NS(async_entries=lambda domain:self.entries),services=NS(has_service=lambda *a:True,async_call=call),devices=NS(devices={}),entities=NS(entities={}),states=NS(get=lambda _:None))
        self.adapter=module.HAPairing(self.hass,NS(options={}));self.mqtt=MQTT();self.mqtt.callback=self.adapter.message;self.adapter.mqtt=lambda:self.mqtt
    def message(self,kind,data):self.adapter.message(NS(topic='zigbee2mqtt/bridge/'+kind,payload=json.dumps(data)))
    async def network(self):
        await self.adapter.observe();self.message('state',{'state':'online'});self.message('devices',[]);return (await self.adapter.controllers())[0]['id']
    async def test_optional_mqtt_failure_does_not_hide_zha(self):
        self.mqtt.connected=False;self.entries=[NS(entry_id='entry',title='Home',state=NS(value='loaded'))]
        self.assertTrue((await self.adapter.controllers())[0]['online']);self.assertEqual(self.mqtt.published,[])
    async def test_zha_only_uses_fixed_permit_service_and_bounded_duration(self):
        self.mqtt.connected=False;self.entries=[NS(entry_id='entry',title='Home',state=NS(value='loaded'))]
        for value in [60,0]:self.assertTrue(await self.adapter.permit('owner','zha:entry',value))
        self.assertEqual([args[:3] for args,kw in self.calls],[('zha','permit',{'duration':60}),('zha','permit',{'duration':0})])
        for value in [-1,254,True,'60']:
            with self.assertRaises(ProductError):await self.adapter.permit('owner','zha:entry',value)
    async def test_mqtt_permit_is_non_retained_qos_zero_and_transaction_matched(self):
        identity=await self.network();self.assertTrue(await self.adapter.permit('owner',identity,60));self.assertTrue(await self.adapter.permit('owner',identity,0))
        self.assertEqual([p[0].split('/')[-1] for p in self.mqtt.published],['health_check','permit_join','permit_join'])
        self.assertTrue(all(p[2]=={'qos':0,'retain':False} for p in self.mqtt.published));self.assertFalse(self.adapter.pending)
    async def test_broker_disconnection_and_admin_revocation_prevent_dispatch(self):
        identity=await self.network();self.mqtt.connected=False
        with self.assertRaises(ProductError):await self.adapter.permit('owner',identity,60)
        self.mqtt.connected=True;self.user.is_admin=False
        with self.assertRaises(ProductError):await self.adapter.permit('owner',identity,0)
        self.assertFalse(self.mqtt.published)
    async def test_bridge_metadata_projects_no_config_or_network_key(self):
        await self.network();self.message('info',{'permit_join':False,'config':{'network_key':'PRIVATE_NETWORK_KEY'},'password':'PRIVATE'})
        self.assertNotIn('PRIVATE',repr(self.adapter.bridges));self.assertNotIn('PRIVATE',str(await self.adapter.controllers()))
    async def test_oversized_or_unknown_inventory_cannot_be_used_as_empty_baseline(self):
        await self.adapter.observe();self.message('state',{'state':'online'});self.assertFalse((await self.adapter.controllers())[0]['online'])
        self.message('devices',[{}]*513);identity=(await self.adapter.controllers())[0]['id'];self.assertFalse((await self.adapter.controllers())[0]['online'])
        with self.assertRaises(ProductError):await self.adapter.devices(identity)
        self.assertTrue(await self.adapter.permit('owner',identity,0),'Closing remains possible even with unusable inventory')
    async def test_stale_or_foreign_responses_never_acknowledge_request(self):
        await self.network();future=asyncio.get_running_loop().create_future();self.adapter.pending[('zigbee2mqtt','response/permit_join','expected')]=future
        self.message('response/permit_join',{'status':'ok','transaction':'stale','data':{'time':60}});self.assertFalse(future.done())
        self.message('response/permit_join',{'status':'error','transaction':'expected','error':'PRIVATE_CONFIG'});self.assertEqual(await future,{'ok':False,'time':None,'healthy':False});self.assertNotIn('PRIVATE',str(future.result()))
    async def test_failed_health_check_never_opens_network(self):
        identity=await self.network();self.mqtt.status='error';self.assertFalse(await self.adapter.permit('owner',identity,60));self.assertEqual(len(self.mqtt.published),1)
    async def test_invalid_private_journal_is_preserved(self):
        self.adapter.store.value={'phase':'requested','baseline':'bad'}
        with self.assertRaises(ProductError):await self.adapter.load()
        self.assertEqual(self.adapter.store.value,{'phase':'requested','baseline':'bad'})
    async def test_observation_is_read_only_idempotent_and_unloads(self):
        await self.adapter.observe();await self.adapter.observe();self.assertEqual(len(self.mqtt.callbacks),5);self.assertFalse(self.mqtt.published)
        await self.adapter.close();self.assertFalse(self.adapter.unsubs);self.assertFalse(self.adapter.bridges)
