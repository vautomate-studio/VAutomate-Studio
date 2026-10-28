"""Native Core script test with simulated device effects, inside an official HA container.

This does not certify HAOS, radios or physical devices. No home-server address is used.
"""
import asyncio
from copy import deepcopy
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from homeassistant.core import HomeAssistant
from custom_components.vautomate_studio import HAAdapter,DOMAIN

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
import test_engine as fixtures
from studio_product.rules import RuleValidator
from studio_product.rule_runtime import AutomationRuntime


async def main():
    with tempfile.TemporaryDirectory(prefix='vautomate-core-') as directory:
        hass=HomeAssistant(directory)
        adapter=fixtures.Adapter();adapter.hass=hass
        adapter.validate_native=lambda rule:HAAdapter.validate_native(adapter,rule)
        adapter.run_native=lambda rule,trigger,execution:HAAdapter.run_native(adapter,rule,trigger,execution)
        actor=fixtures.Actor('owner','Owner',True,lambda _:True,lambda _:True)
        document={'revision':1,'layout':{'name':'Native test','subtitle':'Isolated','rooms':[{'id':'living','name':'Living','entities':list(adapter.states)}],'quick_actions':[]},'routines':[]}
        engine=fixtures.StudioEngine(adapter,document,controls=True)
        async def resolve(_):return actor
        runtime=AutomationRuntime(engine,resolve)
        hass.data[DOMAIN]={'runtime':runtime}
        async def execute(call):await runtime.execute_step(call.data['execution_id'],call.data['step_id'],call.context.user_id)
        hass.services.async_register(DOMAIN,'execute_step',execute)
        for id,state in adapter.states.items():hass.states.async_set(id,state['state'],state['attributes'])
        service=lambda id:{'kind':'service','entity_id':id,'action':'turn_on','data':{}}
        condition={'kind':'state','entity_id':'light.one','state':'on'}
        rule={'id':'native-script-test','name':'Native blocks','enabled':True,'mode':'single','room_id':'living','triggers':[{'id':'entered','kind':'time','at':'08:00','days':[0]}],'condition':{'kind':'all','conditions':[]},'pause_modes':[],
              'actions':[{'kind':'choose','branches':[{'condition':condition,'actions':[{'kind':'repeat','count':2,'actions':[service('light.one')]}]}],'default':[service('light.two')]},
                         {'kind':'parallel','branches':[[{'kind':'condition','condition':{'kind':'not','condition':{'kind':'numeric','entity_id':'sensor.temperature','above':30}}},service('light.two')],[{'kind':'wait','condition':condition,'timeout_seconds':1},{'kind':'delay','seconds':0},service('fan.ceiling')]]}]}
        try:
            rule=RuleValidator(engine,actor).rule(rule)
            await adapter.validate_native(rule)
            record={'rule':rule,'owner_id':actor.id};engine.document['automations']=[record];runtime.reconcile();runtime.queue(record,'entered')
            await asyncio.wait_for(asyncio.gather(*list(runtime.tasks.values())),10)
            execution=list(runtime.executions.values())[-1]
            assert execution['status']=='completed',runtime.public_traces(actor)
            assert sorted((id,action) for _,id,action,_ in adapter.calls)==sorted([('light.one','turn_on'),('light.one','turn_on'),('light.two','turn_on'),('fan.ceiling','turn_on')]),adapter.calls
            # Missing readings must fail closed even under a NOT condition in native Jinja.
            hass.states.async_set('sensor.temperature','unavailable');adapter.states['sensor.temperature']['state']='unavailable';adapter.calls.clear()
            runtime.queue(record,'entered');await asyncio.wait_for(asyncio.gather(*list(runtime.tasks.values())),10)
            assert not any(id=='light.two' for _,id,_,_ in adapter.calls),adapter.calls
            print('PASS: native Core validation, choose/repeat/parallel/wait, private dispatch and unknown-reading guard. Device effects simulated.')
        finally:
            await runtime.close()
            await hass.async_stop(force=True)


asyncio.run(main())
