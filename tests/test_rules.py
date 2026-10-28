import asyncio
from copy import deepcopy
import json
import unittest
import test_engine as fixtures
from test_engine import Actor,module
from studio_product.rules import RuleValidator,compile_script,evaluate,simulate,condition_expression,sequence_cost
from studio_product.rule_templates import prepare,library


class RulesTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        fixtures.EngineTest.setUp(self)
        for identifier,kind,value in [('binary_sensor.presence','occupancy','off'),('binary_sensor.motion','motion','off'),('sensor.humidity','humidity','50'),('input_boolean.sleep',None,'off')]:
            self.adapter.states[identifier]={'entity_id':identifier,'state':value,'attributes':{'device_class':kind}}
            self.engine.document['layout']['rooms'][0]['entities'].append(identifier)
    def rule(self,**updates):
        return {'id':'rule-custom-01','name':'My room','enabled':False,'mode':'restart','room_id':'living','triggers':[{'id':'entry','kind':'state','entity_id':'binary_sensor.presence','from':'off','to':'on','for_seconds':0}],'condition':{'kind':'all','conditions':[]},'actions':[{'kind':'service','entity_id':'light.one','action':'turn_on','data':{}}],'pause_modes':['input_boolean.sleep'],**updates}
    async def expect(self,code,awaitable):
        with self.assertRaises(module.ProductError) as caught:await awaitable
        self.assertEqual(caught.exception.code,code)
    async def test_seven_templates_are_entity_bound_and_inert(self):
        self.assertEqual(len(library()),7)
        rule,origin=prepare(self.engine,self.admin,'room_presence',{'room_id':'living','targets':{'sensor':'binary_sensor.presence','lights':['light.one']}})
        self.assertFalse(rule['enabled']);self.assertEqual(rule['triggers'][1]['for_seconds'],120);self.assertEqual(origin['template_version'],1);self.assertFalse(self.adapter.saved);self.assertFalse(self.adapter.calls)
    async def test_bathroom_requires_coverage_and_presence_not_motion(self):
        with self.assertRaises(module.ProductError):prepare(self.engine,self.admin,'bathroom_presence',{'room_id':'living','targets':{'sensor':'binary_sensor.motion','lights':['light.one']},'coverage_confirmed':True})
        with self.assertRaises(module.ProductError):prepare(self.engine,self.admin,'bathroom_presence',{'room_id':'living','targets':{'sensor':'binary_sensor.presence','lights':['light.one']}})
        rule,_=prepare(self.engine,self.admin,'bathroom_presence',{'room_id':'living','targets':{'sensor':'binary_sensor.presence','lights':['light.one']},'coverage_confirmed':True})
        self.assertEqual(rule['triggers'][1]['for_seconds'],300)
    async def test_fan_hysteresis_and_scene_mode_templates(self):
        rule,_=prepare(self.engine,self.admin,'bathroom_fan',{'room_id':'living','targets':{'sensor':'sensor.humidity','fans':['fan.ceiling']}})
        self.assertEqual(rule['triggers'][0]['above'],65);self.assertEqual(rule['triggers'][1]['below'],55);self.assertEqual(rule['triggers'][1]['for_seconds'],600)
        with self.assertRaises(module.ProductError):prepare(self.engine,self.admin,'bathroom_fan',{'room_id':'living','targets':{'sensor':'sensor.humidity','fans':['fan.ceiling']},'humidity_high':50,'humidity_low':60})
        rule,_=prepare(self.engine,self.admin,'mode_scenes',{'targets':{'mode':'input_boolean.sleep','on_scene':'scene.cinema'}})
        self.assertEqual(rule['room_id'],None);self.assertEqual(rule['actions'][0]['branches'][1]['actions'],[])
    async def test_template_cannot_select_device_from_another_room(self):
        self.engine.document['layout']['rooms'].append({'id':'other','name':'Other','entities':['light.two']});self.engine.document['layout']['rooms'][0]['entities'].remove('light.two')
        with self.assertRaises(module.ProductError):prepare(self.engine,self.admin,'room_presence',{'room_id':'living','targets':{'sensor':'binary_sensor.presence','lights':['light.two']}})
    async def test_permission_and_security_update_actions_rejected(self):
        for entity,action in [('alarm_control_panel.home','alarm_disarm'),('update.core','install'),('camera.secret','record')]:
            with self.assertRaises(module.ProductError):RuleValidator(self.engine,self.admin).rule(self.rule(actions=[{'kind':'service','entity_id':entity,'action':action,'data':{}}]))
        with self.assertRaises(module.ProductError):RuleValidator(self.engine,self.member).rule(self.rule())
    async def test_nested_choose_repeat_parallel_and_wait_compile_to_private_gate(self):
        action=self.rule()['actions'][0]
        value=self.rule(actions=[{'kind':'choose','branches':[{'condition':{'kind':'trigger','ids':['entry']},'actions':[{'kind':'parallel','branches':[[deepcopy(action)],[{'kind':'repeat','count':2,'actions':[deepcopy(action)]}]]}]}],'default':[]},{'kind':'wait','condition':{'kind':'state','entity_id':'light.two','state':'on'},'timeout_seconds':60}])
        clean=RuleValidator(self.engine,self.admin).rule(value);sequence,steps=compile_script(clean)
        self.assertEqual(sequence_cost(clean['actions']),(3,60));self.assertEqual(sequence[1]['choose'][0]['conditions'][0]['condition'],'template')
        self.assertIn('wait_template',sequence[-1]);self.assertEqual(sum(s['kind']=='service' for s in steps.values()),2)
        def action_calls(v):
            if isinstance(v,list):return sum((action_calls(n) for n in v),[])
            if isinstance(v,dict):return ([v['action']] if 'action' in v and isinstance(v['action'],str) else [])+sum((action_calls(n) for n in v.values()),[])
            return []
        self.assertTrue(all(a=='vautomate_studio.execute_step' for a in action_calls(sequence)))
    async def test_limits_unknown_fields_and_arbitrary_code_rejected(self):
        action=self.rule()['actions'][0]
        for value in [self.rule(script='arbitrary'),self.rule(mode='unbounded'),self.rule(actions=[{'kind':'template','code':'do anything'}]),self.rule(actions=[{'kind':'repeat','count':20,'actions':[{'kind':'repeat','count':20,'actions':[action]}]}])]:
            with self.assertRaises(module.ProductError):RuleValidator(self.engine,self.admin).rule(value)
    async def test_unknown_or_non_numeric_never_passes_not(self):
        self.adapter.states['sensor.humidity']['state']='unavailable';condition={'kind':'not','condition':{'kind':'numeric','entity_id':'sensor.humidity','above':60}}
        self.assertIsNone(evaluate(condition,self.adapter.state));self.assertIn('is_number',condition_expression(condition))
        self.adapter.states['sensor.humidity']['state']='not numeric';self.assertIsNone(evaluate(condition,self.adapter.state))
    async def test_not_of_group_with_an_unknown_dependency_is_conservative(self):
        self.adapter.states['sensor.humidity']['state']='unknown'
        cond={'kind':'not','condition':{'kind':'all','conditions':[{'kind':'state','entity_id':'light.one','state':'off'},{'kind':'numeric','entity_id':'sensor.humidity','above':60}]}}
        self.assertIsNone(evaluate(cond,self.adapter.state))
    async def test_simulation_never_dispatches_or_invents_future_waits(self):
        action=self.rule()['actions'][0];rule=RuleValidator(self.engine,self.admin).rule(self.rule(actions=[{'kind':'wait','condition':{'kind':'state','entity_id':'light.two','state':'on'},'timeout_seconds':30},action]))
        trace=simulate(rule,self.adapter.state,'entry');self.assertEqual(trace[0]['result'],'awaiting_future_reading');self.assertEqual(len(trace),1);self.assertFalse(self.adapter.calls)
    async def test_custom_preview_approval_and_user_acknowledgement(self):
        review=await self.engine.preview_automation(self.admin,self.rule(),2);self.assertFalse(review['writes']);self.assertFalse(self.adapter.saved)
        await self.expect('shared_home_ack_required',self.engine.approve_automation(self.admin,review['approval_nonce']))
        result=await self.engine.approve_automation(self.admin,review['approval_nonce'],shared_home_ack=True)
        self.assertTrue(result['created']);self.assertFalse(result['enabled']);self.assertFalse(self.adapter.calls)
        receipt=await self.engine.approve_automation(self.admin,review['approval_nonce'],enabled=True,shared_home_ack=True)
        self.assertFalse(receipt['created']);self.assertFalse(receipt['enabled']);self.assertEqual(len(self.engine.rule_records()),1)
    async def test_conflicts_require_a_separate_review_acknowledgement(self):
        self.engine.document['routines']=[{'id':'old','name':'Existing evening','enabled':True,'actions':[{'entity_id':'light.one','action':'turn_off','data':{}}]}]
        review=await self.engine.preview_automation(self.admin,self.rule(),2);self.assertEqual(review['conflicts'][0]['name'],'Existing evening')
        await self.expect('conflict_review_required',self.engine.approve_automation(self.admin,review['approval_nonce'],shared_home_ack=True))
        await self.engine.approve_automation(self.admin,review['approval_nonce'],shared_home_ack=True,conflicts_ack=True)
        self.assertTrue(self.engine.document['routines'][0]['enabled'],'Other rules are not silently disabled')
    async def test_approval_is_bound_to_user_revision_and_kind(self):
        review=await self.engine.preview_automation(self.admin,self.rule(),2);other=Actor('other','Other',True,lambda _:True,lambda _:True)
        await self.expect('approval_required',self.engine.approve_automation(other,review['approval_nonce'],shared_home_ack=True))
        await self.expect('approval_required',self.engine.approve_bundle(self.admin,review['approval_nonce']))
        self.engine.document['revision']+=1
        await self.expect('revision_conflict',self.engine.approve_automation(self.admin,review['approval_nonce'],shared_home_ack=True))
    async def test_disk_failure_keeps_draft_and_previous_document(self):
        review=await self.engine.preview_automation(self.admin,self.rule(),2);before=deepcopy(self.engine.document);self.adapter.disk_failure=True
        with self.assertRaises(OSError):await self.engine.approve_automation(self.admin,review['approval_nonce'],shared_home_ack=True)
        self.assertEqual(before,self.engine.document);self.adapter.disk_failure=False
        await self.engine.approve_automation(self.admin,review['approval_nonce'],shared_home_ack=True);self.assertEqual(len(self.engine.rule_records()),1)
    async def test_room_hold_persists_expires_and_keeps_manual_control(self):
        result=await self.engine.set_room_pause(self.member,'living',900);self.assertIn('living',result['room_pauses'])
        self.assertTrue(self.engine.actions_held([{'entity_id':'light.one'}]));self.assertTrue(self.engine.actions_held([{'entity_id':'scene.cinema'}]))
        result=await self.engine.command(self.member,self.request());self.assertEqual(result['status'],'accepted')
        self.adapter.clock+=901;self.assertFalse(self.engine.active_room_pauses());self.assertFalse(self.engine.actions_held([{'entity_id':'light.one'}]))
    def request(self):return {'request_id':'manual-request-123456789','expires_at':1015,'entity_id':'light.one','action':'turn_off','data':{}}
    async def test_room_hold_denies_read_only_member(self):
        actor=Actor('read','Viewer',False,lambda _:True,lambda _:False)
        await self.expect('not_allowed',self.engine.set_room_pause(actor,'living',3600));self.assertFalse(self.adapter.saved)
    async def test_interrupted_device_request_does_not_remain_pending(self):
        self.adapter.wait=asyncio.Event();task=asyncio.create_task(self.engine.command(self.admin,self.request()));await asyncio.sleep(0);task.cancel()
        with self.assertRaises(asyncio.CancelledError):await task
        result=await self.engine.command(self.admin,self.request());self.assertEqual(result['status'],'check_required');self.assertEqual(len(self.adapter.calls),1)


if __name__=='__main__':unittest.main()
