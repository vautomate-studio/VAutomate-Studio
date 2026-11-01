"""Setup approvals and session ownership use an inert native-flow adapter."""
import asyncio
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest
import test_engine as fixtures

path=Path(__file__).resolve().parents[1]/'custom_components/vautomate_studio/integration_setup.py';spec=importlib.util.spec_from_file_location('studio_product.integration_setup',path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)

class Adapter:
    def __init__(self):self.allowed=True;self.calls=[];self.existing=[];self.fail=False;self.wait=None
    async def authorize(self,identity):
        if not self.allowed:raise fixtures.ProductError('not_allowed','Revoked')
    async def status(self):return {'integrations':self.existing,'supervised':True,'serial_ports':[],'apps':[]}
    async def begin(self,kind):self.calls.append(('begin',kind));return 'owned-native-flow',{'type':'form','fields':[{'name':'path','type':'string'}]}
    async def step(self,kind,handle,values):
        self.calls.append(('step',kind,handle))
        if self.wait:await self.wait.wait()
        if self.fail:raise RuntimeError('PRIVATE MQTT PASSWORD')
        return {'type':'complete','name':'Configured'}
    async def cancel(self,kind,handle):self.calls.append(('cancel',kind,handle))

class IntegrationTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        fixtures.EngineTest.setUp(self);self.native=Adapter();self.clock=1000.;self.service=module.IntegrationSetup(self.engine,self.native,clock=lambda:self.clock)
    async def begin(self,kind='zha'):
        review=await self.service.preview(self.admin,{'kind':kind});return await self.service.begin(self.admin,{'approval_nonce':review['approval_nonce'],'confirmed':True,'radio_detection_approved':True,'coordinator_history':'unknown'})
    def payload(self,setup,**changes):return {'session_id':setup['session_id'],'generation':setup['generation'],'input':{'path':'selected-port'},'request_id':'request-12345678',**changes}
    async def test_completed_setup_capacity_is_reclaimed_without_radio_calls(self):
        self.service.sessions={str(i):{'id':str(i),'actor':'old-owner','phase':'complete'} for i in range(32)}
        setup=await self.begin()
        self.assertEqual(setup['type'],'form')
        self.assertEqual(len(self.service.sessions),32)
        self.assertEqual(self.native.calls,[('begin','zha')])

    async def test_preview_is_inert_and_only_known_integrations_exist(self):
        review=await self.service.preview(self.admin,{'kind':'zigbee2mqtt'});self.assertTrue(review['third_party_software']);self.assertFalse(review['writes']);self.assertEqual(self.native.calls,[])
        for kind in ['arbitrary',[],{},None]:
            with self.assertRaises(fixtures.ProductError):await self.service.preview(self.admin,{'kind':kind})
    async def test_member_cannot_read_or_modify_setup(self):
        for op,arg in [('status',None),('preview',{'kind':'zha'}),('begin',{}),('step',{}),('cancel',{})]:
            with self.assertRaises(fixtures.ProductError):await getattr(self.service,op)(self.member,*([] if arg is None else [arg]))
    async def test_read_only_requires_commissioning_before_any_setup(self):
        self.engine.controls=False
        with self.assertRaises(fixtures.ProductError):await self.service.preview(self.admin,{'kind':'zha'})
        self.assertEqual(self.native.calls,[])
    async def test_approval_requires_current_actor_ack_and_expiry(self):
        review=await self.service.preview(self.admin,{'kind':'zha'})
        with self.assertRaises(fixtures.ProductError):await self.service.begin(self.admin,{'approval_nonce':review['approval_nonce'],'confirmed':False})
        self.clock+=301
        with self.assertRaises(fixtures.ProductError):await self.service.begin(self.admin,{'approval_nonce':review['approval_nonce'],'confirmed':True})
    async def test_existing_zha_is_not_replaced(self):
        self.native.existing=[{'domain':'zha'}]
        with self.assertRaises(fixtures.ProductError):await self.service.preview(self.admin,{'kind':'zha'})
    async def test_native_session_is_owned_and_only_current_generation_can_submit(self):
        setup=await self.begin();other=fixtures.Actor('other','Other',True,lambda _:True,lambda _:True)
        with self.assertRaises(fixtures.ProductError):await self.service.step(other,self.payload(setup))
        with self.assertRaises(fixtures.ProductError):await self.service.step(self.admin,self.payload(setup,generation=0))
        result=await self.service.step(self.admin,self.payload(setup));self.assertEqual(result['type'],'complete');self.assertEqual(len(self.native.calls),2)
    async def test_duplicate_step_never_replays_native_setup(self):
        setup=await self.begin();payload=self.payload(setup);first=await self.service.step(self.admin,payload);self.assertEqual(await self.service.step(self.admin,payload),first);self.assertEqual(len(self.native.calls),2)
    async def test_unknown_result_is_redacted_and_consumed(self):
        setup=await self.begin();self.native.fail=True;payload=self.payload(setup)
        with self.assertRaises(fixtures.ProductError) as raised:await self.service.step(self.admin,payload)
        self.assertNotIn('PRIVATE',str(raised.exception));self.assertEqual((await self.service.step(self.admin,payload))['type'],'check_required');self.assertEqual(len(self.native.calls),2)
    async def test_working_setup_is_resumable_without_restarting_or_resubmitting(self):
        setup=await self.begin();self.native.wait=asyncio.Event();task=asyncio.create_task(self.service.step(self.admin,self.payload(setup)));await asyncio.sleep(0);report=await self.service.status(self.admin);self.assertEqual(report['setups'][0]['type'],'working');self.native.wait.set();await task
    async def test_cancel_aborts_only_own_pending_flow_and_no_created_entry(self):
        setup=await self.begin();await self.service.cancel(self.admin,{'session_id':setup['session_id']});self.assertEqual(self.native.calls[-1],('cancel','zha','owned-native-flow'));self.assertEqual((await self.service.status(self.admin))['setups'],[])
    async def test_revocation_is_rechecked_for_native_steps(self):
        setup=await self.begin();self.native.allowed=False
        with self.assertRaises(fixtures.ProductError):await self.service.step(self.admin,self.payload(setup))
        self.assertEqual(len(self.native.calls),1)


class CoordinatorProtectionTest(unittest.IsolatedAsyncioTestCase):
    setUp=IntegrationTest.setUp
    begin=IntegrationTest.begin
    payload=IntegrationTest.payload
    async def test_radio_begin_requires_specific_detection_consent(self):
        plan=await self.service.preview(self.admin,{'kind':'zha'})
        with self.assertRaises(fixtures.ProductError) as error:
            await self.service.begin(self.admin,{'approval_nonce':plan['approval_nonce'],'confirmed':True})
        self.assertEqual(error.exception.code,'confirmation_required');self.assertEqual(self.native.calls,[])
    async def test_used_coordinator_cannot_create_initial_network(self):
        setup=await self.begin()
        with self.assertRaises(fixtures.ProductError) as error:
            await self.service.step(self.admin,self.payload(setup,input={'next_step_id':'form_initial_network'}))
        self.assertEqual(error.exception.code,'network_review_required');self.assertEqual(len(self.native.calls),1)
    async def test_reuse_is_the_only_network_choice_for_used_coordinator(self):
        setup=await self.begin();session=self.service.sessions[setup['session_id']]
        result=self.service.present(session,{'type':'menu','options':['reuse_settings','form_initial_network']})
        self.assertEqual(result['options'],['reuse_settings'])
        result=self.service.present(session,{'type':'menu','options':['form_initial_network']})
        self.assertEqual(result['type'],'check_required')
    async def test_unknown_or_used_z2m_needs_migration_review(self):
        for history in ['used','unknown']:
            plan=await self.service.preview(self.admin,{'kind':'zigbee2mqtt'})
            with self.assertRaises(fixtures.ProductError) as error:
                await self.service.begin(self.admin,{'approval_nonce':plan['approval_nonce'],'confirmed':True,'radio_detection_approved':True,'coordinator_history':history})
            self.assertEqual(error.exception.code,'network_review_required')
        self.assertEqual(self.native.calls,[])
    async def test_new_unused_z2m_can_begin_after_review(self):
        plan=await self.service.preview(self.admin,{'kind':'zigbee2mqtt'})
        setup=await self.service.begin(self.admin,{'approval_nonce':plan['approval_nonce'],'confirmed':True,'radio_detection_approved':True,'coordinator_history':'unused'})
        self.assertEqual(setup['type'],'form');self.assertEqual(self.native.calls,[('begin','zigbee2mqtt')])
