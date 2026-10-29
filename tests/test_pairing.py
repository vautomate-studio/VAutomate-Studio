"""Reviewed onboarding policy with inert network and storage adapters."""
import asyncio
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest
from test_engine import Actor,Adapter as EngineAdapter,StudioEngine,ProductError

path=Path(__file__).resolve().parents[1]/'custom_components/vautomate_studio/pairing.py'
spec=importlib.util.spec_from_file_location('studio_product.pairing',path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)


class Adapter:
    def __init__(self):self.record=None;self.calls=[];self.known=[{'id':'old','stage':'ready','entities':[]}];self.allowed=True;self.fail=False;self.disk_failure=False;self.online=True;self.wait=None
    async def authorize(self,identity):
        if not self.allowed:raise ProductError('not_allowed','Revoked')
    async def load(self):return deepcopy(self.record)
    async def save(self,value):
        if self.disk_failure:raise OSError('PRIVATE storage path')
        self.record=deepcopy(value)
    async def controllers(self):return [{'id':'network','name':'Home Zigbee','online':self.online}]
    async def devices(self,identity):return deepcopy(self.known)
    async def permit(self,identity,controller,duration):
        assert self.record is not None,'Must journal before radio admission'
        self.calls.append(duration)
        if self.wait:await self.wait.wait()
        if self.fail:raise RuntimeError('PRIVATE radio key')
        return True


class PairingTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.adapter=Adapter();self.core=EngineAdapter();self.clock=1000.
        document={'revision':2,'layout':{'name':'My home','subtitle':'Welcome.','rooms':[{'id':'living','name':'Living','entities':[]},{'id':'bedroom','name':'Bedroom','entities':[]}],'quick_actions':[]},'routines':[]}
        self.engine=StudioEngine(self.core,document,controls=True);self.service=module.Pairing(self.engine,self.adapter,clock=lambda:self.clock,wall=lambda:self.clock)
        self.admin=Actor('owner','Owner',True,lambda _:True,lambda _:True);self.member=Actor('member','Member',False,lambda _:True,lambda _:True)
    async def review(self):return await self.service.preview(self.admin,{'controller_id':'network','room_id':'living'})
    async def start(self):
        review=await self.review();return await self.service.begin(self.admin,{'approval_nonce':review['approval_nonce'],'ready':True})
    def new_device(self):self.adapter.known.append({'id':'new','name':'New pendant','stage':'ready','entities':[{'entity_id':'light.one','name':'Pendant'}]})
    def assignment(self,**changes):return {'session_id':self.service.session['id'],'device_id':'new','room_id':'living','entities':['light.one'],'revision':2,**changes}
    async def test_members_and_revoked_administrators_cannot_pair(self):
        for operation,payload in [('status',None),('preview',{}),('begin',{}),('cancel',{}),('assign',{})]:
            with self.assertRaises(ProductError):await getattr(self.service,operation)(self.member,*([] if payload is None else [payload]))
        self.adapter.allowed=False
        with self.assertRaises(ProductError):await self.review()
        self.assertEqual(self.adapter.calls,[])
    async def test_review_is_inert_and_readiness_is_required(self):
        review=await self.review();self.assertFalse(review['opens_network']);self.assertEqual(self.adapter.calls,[])
        with self.assertRaises(ProductError):await self.service.begin(self.admin,{'approval_nonce':review['approval_nonce'],'ready':False})
        self.assertEqual(self.adapter.calls,[])
    async def test_duplicate_start_returns_receipt_without_second_admission(self):
        review=await self.review();payload={'approval_nonce':review['approval_nonce'],'ready':True}
        first=await self.service.begin(self.admin,payload);self.assertEqual(await self.service.begin(self.admin,payload),first);self.assertEqual(self.adapter.calls,[60])
    async def test_unknown_result_is_consumed_redacted_and_not_replayed(self):
        self.adapter.fail=True;review=await self.review();payload={'approval_nonce':review['approval_nonce'],'ready':True}
        result=await self.service.begin(self.admin,payload);self.assertEqual(result['status'],'check_required');self.assertNotIn('PRIVATE',str(result));await self.service.begin(self.admin,payload);self.assertEqual(self.adapter.calls,[60])
    async def test_disk_failure_prevents_radio_admission(self):
        self.adapter.disk_failure=True
        with self.assertRaises(OSError):await self.start()
        self.assertEqual(self.adapter.calls,[])
    async def test_restart_never_opens_radio_and_requires_explicit_close(self):
        await self.start();restored=module.Pairing(self.engine,self.adapter);await restored.initialize();self.assertEqual(restored.session['phase'],'interrupted');self.assertEqual(self.adapter.calls,[60])
        result=await restored.cancel(self.admin,{'session_id':restored.session['id']});self.assertEqual(result['status'],'closed');self.assertEqual(self.adapter.calls,[60,0])
    async def test_cancel_remains_available_when_evaluation_controls_disabled(self):
        await self.start();self.engine.controls=False;await self.service.cancel(self.admin,{'session_id':self.service.session['id']});self.assertEqual(self.adapter.calls,[60,0])
        with self.assertRaises(ProductError):await self.review()
    async def test_expired_or_other_actor_review_cannot_open_network(self):
        review=await self.review();payload={'approval_nonce':review['approval_nonce'],'ready':True};other=Actor('other','Other',True,lambda _:True,lambda _:True)
        with self.assertRaises(ProductError):await self.service.begin(other,payload)
        self.clock+=301
        with self.assertRaises(ProductError):await self.service.begin(self.admin,payload)
        self.assertEqual(self.adapter.calls,[])
    async def test_busy_start_is_rejected_instead_of_queued(self):
        first=await self.review();second=await self.review();self.adapter.wait=asyncio.Event();task=asyncio.create_task(self.service.begin(self.admin,{'approval_nonce':first['approval_nonce'],'ready':True}));await asyncio.sleep(0)
        with self.assertRaises(ProductError):await self.service.begin(self.admin,{'approval_nonce':second['approval_nonce'],'ready':True})
        self.adapter.wait.set();await task;self.assertEqual(self.adapter.calls,[60])
    async def test_existing_devices_are_excluded_and_timer_expires(self):
        await self.start();self.new_device();self.clock+=61;report=await self.service.status(self.admin);self.assertEqual(report['session']['phase'],'window_finished');self.assertEqual(report['session']['seconds_remaining'],0);self.assertEqual([d['id'] for d in report['session']['devices']],['new']);self.assertFalse(report['hardware_certified'])
    async def test_room_assignment_is_reviewed_revisioned_and_never_operates_device(self):
        await self.start();self.new_device();result=await self.service.assign(self.admin,self.assignment());self.assertEqual(result['revision'],3);self.assertFalse(result['device_operated']);self.assertEqual(self.core.calls,[]);self.assertEqual(self.adapter.calls,[60]);self.assertEqual(self.engine.document['layout']['rooms'][0]['entities'],['light.one'])
    async def test_existing_device_and_foreign_entity_cannot_be_assigned(self):
        await self.start();self.new_device()
        for changes in [{'device_id':'old'},{'entities':['light.two']},{'entities':[{}]},{'entities':['light.one','light.one']},{'revision':1},{'room_id':'missing'}]:
            with self.assertRaises(ProductError):await self.service.assign(self.admin,self.assignment(**changes))
        self.assertEqual(self.core.saved,[])
    async def test_incomplete_device_is_not_ready_for_assignment(self):
        await self.start();self.new_device();self.adapter.known[-1]['stage']='preparing'
        with self.assertRaises(ProductError):await self.service.assign(self.admin,self.assignment())
    async def test_cross_room_assignment_cannot_silently_move_device(self):
        await self.start();self.new_device();self.engine.document['layout']['rooms'][1]['entities']=['light.one']
        with self.assertRaises(ProductError):await self.service.assign(self.admin,self.assignment())
    async def test_room_changes_and_oversized_network_require_review(self):
        review=await self.review();self.engine.document['layout']['rooms'][0]['name']='Renamed'
        with self.assertRaises(ProductError):await self.service.begin(self.admin,{'approval_nonce':review['approval_nonce'],'ready':True})
        self.adapter.known=[{'id':str(i)} for i in range(513)]
        with self.assertRaises(ProductError):await self.start()
        self.assertEqual(self.adapter.calls,[])
