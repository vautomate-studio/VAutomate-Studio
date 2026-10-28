"""Runtime orchestration tests; native HA Script execution is separately gated."""
import asyncio
from copy import deepcopy
from datetime import datetime,timedelta
import unittest
import test_engine as fixtures
from studio_product.rule_templates import prepare
from studio_product.rule_runtime import AutomationRuntime


class RuntimeTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        fixtures.EngineTest.setUp(self)
        for id,kind,value in [('binary_sensor.presence','occupancy','off'),('input_boolean.sleep',None,'off')]:
            self.adapter.states[id]={'entity_id':id,'state':value,'attributes':{'device_class':kind}}
            self.engine.document['layout']['rooms'][0]['entities'].append(id)
        rule,_=prepare(self.engine,self.admin,'room_presence',{'room_id':'living','targets':{'sensor':'binary_sensor.presence','lights':['light.one']},'pause_modes':['input_boolean.sleep']})
        rule['enabled']=True;self.record={'rule':rule,'owner_id':'owner'};self.engine.document['automations']=[self.record]
        self.actor=self.admin;self.runs=[];self.gate=None
        self.adapter.monotonic=lambda:self.adapter.clock
        async def resolve(_):return self.actor
        async def native(rule,trigger,execution):
            self.runs.append(trigger)
            if self.gate:await self.gate.wait()
            # Model the selected recipe branch, then exercise the real dispatch gate.
            step='a.0.b'+('0' if trigger=='entered' else '1')+'.0'
            await self.runtime.execute_step(execution,step,self.actor.id)
            return True
        self.adapter.run_native=native
        self.runtime=AutomationRuntime(self.engine,resolve)
    async def asyncTearDown(self):await self.runtime.close()
    async def settle(self):
        for _ in range(20):await asyncio.sleep(0)
    def change(self,id,value):
        before=self.adapter.state(id);self.adapter.states[id]['state']=value
        self.runtime.state_changed(id,before,self.adapter.state(id))
    def tick(self,seconds=0):
        self.adapter.clock+=seconds;self.runtime.tick(datetime(2026,10,28,12,0)+timedelta(seconds=seconds))
    async def test_entry_and_confirmed_vacancy(self):
        self.change('binary_sensor.presence','on');await self.settle()
        self.assertEqual(self.runs,['entered']);self.assertEqual(self.adapter.calls[-1][2],'turn_on')
        self.change('binary_sensor.presence','off');self.tick(119);await self.settle();self.assertEqual(len(self.runs),1)
        self.tick(1);await self.settle();self.assertEqual(self.runs,['entered','vacant']);self.assertEqual(self.adapter.calls[-1][2],'turn_off')
    async def test_reentry_resets_vacancy_timer(self):
        self.change('binary_sensor.presence','on');await self.settle();self.change('binary_sensor.presence','off');self.tick(60)
        self.change('binary_sensor.presence','on');await self.settle();self.tick(90);await self.settle()
        self.assertNotIn('vacant',self.runs)
    async def test_unavailable_cancels_dwell_and_recovery_does_not_trigger(self):
        self.change('binary_sensor.presence','on');await self.settle();self.change('binary_sensor.presence','off')
        self.change('binary_sensor.presence','unavailable');self.tick(200);await self.settle();self.change('binary_sensor.presence','off');self.tick(200);await self.settle()
        self.assertEqual(self.runs,['entered'])
    async def test_hold_and_mode_cancel_without_resume_replay(self):
        self.change('binary_sensor.presence','on');await self.settle();self.change('binary_sensor.presence','off')
        await self.engine.set_room_pause(self.member,'living',900);self.tick(1000);await self.settle();self.assertEqual(self.runs,['entered'])
        self.change('input_boolean.sleep','on');self.change('binary_sensor.presence','on');await self.settle();self.assertEqual(self.runs,['entered'])
        self.change('input_boolean.sleep','off');self.tick();await self.settle();self.assertEqual(self.runs,['entered'])
    async def test_pause_cancels_running_run(self):
        self.gate=asyncio.Event();self.change('binary_sensor.presence','on');await self.settle()
        await self.engine.pause_automation(self.admin,self.record['rule']['id'],self.engine.document['revision']);await self.settle()
        self.assertFalse(self.adapter.calls);self.assertEqual(list(self.runtime.executions.values())[-1]['status'],'cancelled')
    async def test_permission_revocation_stops_dispatch(self):
        self.gate=asyncio.Event();self.change('binary_sensor.presence','on');await self.settle()
        self.actor=fixtures.Actor('owner','Owner',False,lambda _:True,lambda _:True);self.gate.set();await self.settle()
        self.assertFalse(self.adapter.calls);self.assertEqual(list(self.runtime.executions.values())[-1]['status'],'needs_attention')
    async def test_private_step_is_account_bound_and_trace_redacted(self):
        self.gate=asyncio.Event();self.change('binary_sensor.presence','on');await self.settle();execution=next(iter(self.runtime.executions))
        with self.assertRaises(fixtures.ProductError):await self.runtime.execute_step(execution,'a.0.b0.0','intruder')
        with self.assertRaises(fixtures.ProductError):self.runtime.public_traces(self.member)
        self.assertNotIn(execution,str(self.runtime.public_traces(self.admin)));self.assertFalse(self.adapter.calls)
    async def test_single_and_restart_modes(self):
        self.record['rule']['mode']='single';self.runtime.reconcile();self.gate=asyncio.Event()
        self.change('binary_sensor.presence','on');await self.settle();self.change('binary_sensor.presence','off');self.change('binary_sensor.presence','on');await self.settle();self.assertEqual(len(self.runs),1)
        self.record['rule']['mode']='restart';self.runtime.reconcile();await self.settle();self.change('binary_sensor.presence','off');self.change('binary_sensor.presence','on');await self.settle();self.assertEqual(len(self.runs),2)
    async def test_time_reservation_survives_restart(self):
        self.record['rule']['triggers']=[{'id':'entered','kind':'time','at':'12:01','days':[2]}];self.runtime.reconcile()
        self.runtime.tick(datetime(2026,10,28,12,0));self.runtime.tick(datetime(2026,10,28,12,1));await self.settle();self.assertEqual(len(self.runs),1)
        self.runtime.last_minute=None;self.runtime.tick(datetime(2026,10,28,12,0));self.runtime.tick(datetime(2026,10,28,12,1));await self.settle();self.assertEqual(len(self.runs),1)
    async def test_startup_never_replays_current_occupancy(self):
        self.adapter.states['binary_sensor.presence']['state']='on';self.runtime.reconcile();self.tick();await self.settle();self.assertFalse(self.runs)
