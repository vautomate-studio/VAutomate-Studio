"""Native-flow projection and fixed app operations; no real installs or radios."""
from copy import deepcopy
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import sys
import unittest
from unittest.mock import patch
from test_engine import ProductError

class Store:
    def __init__(self,*a):self.value=None
    async def async_load(self):return deepcopy(self.value)
    async def async_save(self,v):self.value=deepcopy(v)

path=Path(__file__).resolve().parents[1]/'custom_components/vautomate_studio/ha_integrations.py';spec=importlib.util.spec_from_file_location('studio_product.ha_integrations',path);module=importlib.util.module_from_spec(spec)
with patch.dict(sys.modules,{'homeassistant.helpers.storage':NS(Store=Store)}):spec.loader.exec_module(module)

class Flow:
    def __init__(self):self.calls=[];self.aborted=[]
    async def async_init(self,kind,**kw):self.calls.append(('init',kind));return {'flow_id':'owned','type':'menu','menu_options':['broker','addon']}
    async def async_configure(self,identity,values):self.calls.append(('step',identity,deepcopy(values)));return {'type':'create_entry','title':'Connected','data':{'password':'PRIVATE'}} if values and 'broker' in values else {'type':'form','flow_id':'owned','data_schema':None}
    def async_progress(self):return [{'flow_id':'owned','handler':'zha'}]
    def async_abort(self,identity):self.aborted.append(identity)

class HAIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def test_unrenderable_initial_flow_aborts_only_its_new_flow(self):
        with patch.object(self.adapter,'serialize',side_effect=ValueError('unsupported schema')):
            with self.assertRaises(ValueError):await self.adapter.begin('zha')
        self.assertEqual(self.flow.aborted,['owned'])
        self.assertFalse(self.adapter.owned)

    def test_native_form_allows_explicit_null_errors(self):
        adapter=module.HAIntegrations(NS(),None)
        result=adapter.serialize({'type':'form','step_id':'choose_serial_port','errors':None,'data_schema':None})
        self.assertEqual(result['errors'],{})
        self.assertEqual(result['fields'],[])

    def setUp(self):
        self.flow=Flow();self.entries=[];self.hass=NS(config=NS(components={'hassio'}),config_entries=NS(flow=self.flow,async_entries=lambda kind:self.entries))
        async def authorize(_):pass
        self.adapter=module.HAIntegrations(self.hass,authorize);self.calls=[]
        async def supervisor(endpoint,method='get',payload=None,**kwargs):
            self.calls.append((endpoint,method,deepcopy(payload)))
            return {'repositories':[{'source':module.Z2M_REPOSITORY}]} if endpoint=='/store' else {'addons':[]} if endpoint=='/addons' else {'options':{}} if endpoint.endswith('/info') else {'host':'core-mosquitto','port':1883,'username':'addons','password':'PRIVATE'} if endpoint=='/services/mqtt' else {}
        self.adapter.supervisor=supervisor
        async def ports():return [{'value':'/dev/ttyUSB_TEST','label':'Test USB coordinator'}]
        self.adapter.serial_ports=ports
    async def test_native_create_entry_projects_no_credentials_or_entry_data(self):
        result=self.adapter.serialize({'type':'create_entry','flow_id':'owned','title':'Home','data':{'password':'PRIVATE'},'result':object()});self.assertEqual(result['type'],'complete');self.assertNotIn('PRIVATE',repr(result));self.assertNotIn('data',result)
    async def test_destructive_zha_menu_is_not_offered(self):
        result=self.adapter.serialize({'type':'menu','menu_options':['setup_strategy_recommended','setup_strategy_advanced','form_new_network','reuse_settings']});self.assertEqual(result['options'],['setup_strategy_advanced','reuse_settings'])
    async def test_password_suggestions_are_removed_recursively(self):
        fields=[{'name':'password','default':'PRIVATE','description':{'suggested_value':'PRIVATE'}},{'name':'other_settings','schema':[{'name':'proxy_password','default':'PRIVATE'}]}]
        with patch.dict(sys.modules,{'probatio':NS(to_field_list=lambda *a,**kw:deepcopy(fields)),'homeassistant.helpers':NS(config_validation=NS(custom_serializer=None))}):result=self.adapter.serialize({'type':'form','data_schema':object()})
        self.assertNotIn('PRIVATE',repr(result))
    async def test_non_owned_native_flow_cannot_be_submitted_or_aborted(self):
        with self.assertRaises(ProductError):await self.adapter.step('zha','foreign',{})
        await self.adapter.cancel('zha','foreign');self.assertFalse(self.flow.aborted)
    async def test_zigbee2mqtt_install_does_not_start_radio_and_keeps_manual_updates(self):
        await self.adapter.z2m_install({'install_broker':True,'software_approved':True});paths=[p[0] for p in self.calls];self.assertIn('/addons/'+module.Z2M_SLUG+'/install',paths);self.assertNotIn('/addons/'+module.Z2M_SLUG+'/start',paths);self.assertTrue(any(p[2]=={'auto_update':False} for p in self.calls));self.assertEqual(self.adapter.store.value['stage'],'installed')
    async def test_existing_zha_blocks_competing_network_install(self):
        self.entries=[NS(entry_id='zha',domain='zha',title='Existing',state='loaded')]
        with self.assertRaises(ProductError):await self.adapter.z2m_install({'install_broker':False,'software_approved':True})
        self.assertFalse(any(c[1]=='post' for c in self.calls))
    async def test_loopback_or_unknown_usb_port_cannot_be_used(self):
        self.adapter.store.value={'installed_by_studio':True,'configured':False,'stage':'installed'}
        for port in ['tcp://127.0.0.1:6638','/dev/arbitrary','http://router:80','tcp://8.8.8.8:6638']:
            with self.assertRaises(ProductError):await self.adapter.z2m_configure({'port':port,'adapter':'ember','baudrate':115200,'broker_mode':'managed'})
        self.assertFalse(any(c[1]=='post' for c in self.calls))
    async def test_managed_broker_credentials_stay_backend_and_radio_starts_only_after_configuration(self):
        self.adapter.store.value={'installed_by_studio':True,'configured':False,'stage':'installed'}
        result=await self.adapter.z2m_configure({'port':'/dev/ttyUSB_TEST','adapter':'ember','baudrate':115200,'broker_mode':'managed'});self.assertEqual(result['type'],'complete');self.assertNotIn('PRIVATE',repr(result));options=next(p[2]['options'] for p in self.calls if p[0]=='/addons/'+module.Z2M_SLUG+'/options');self.assertEqual(options['mqtt']['password'],'PRIVATE');self.assertEqual(options['data_path'],'/config/vautomate_studio_zigbee2mqtt');self.assertEqual(self.calls[-1][0],'/addons/'+module.Z2M_SLUG+'/start');self.assertTrue(self.adapter.store.value['configured'])
