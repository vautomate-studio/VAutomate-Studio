import asyncio
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest

path=Path(__file__).resolve().parents[1]/"custom_components/vautomate_studio/engine.py"
package=types.ModuleType("studio_product");package.__path__=[str(path.parent)];sys.modules["studio_product"]=package
spec=importlib.util.spec_from_file_location("studio_product.engine",path)
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
Actor,StudioEngine,ProductError=module.Actor,module.StudioEngine,module.ProductError


class Adapter:
    version="2026.10.2"
    def __init__(self):
        self.clock=1000.;self.calls=[];self.saved=[];self.disk_failure=False;self.call_failure=False;self.wait=None
        self.states={
            "light.one":{"entity_id":"light.one","state":"on","attributes":{"friendly_name":"Pendant","supported_color_modes":["brightness"],"password":"NEVER_RETURN","entity_picture":"http://private/?token=secret"}},
            "light.two":{"entity_id":"light.two","state":"off","attributes":{}},
            "cover.blind":{"entity_id":"cover.blind","state":"open","attributes":{"supported_features":3}},
            "fan.ceiling":{"entity_id":"fan.ceiling","state":"off","attributes":{"supported_features":49}},
            "alarm_control_panel.home":{"entity_id":"alarm_control_panel.home","state":"armed_away","attributes":{"supported_features":3,"code_format":"number","code_arm_required":True}},
            "sensor.temperature":{"entity_id":"sensor.temperature","state":"24","attributes":{"unit_of_measurement":"°C"}},
            "scene.cinema":{"entity_id":"scene.cinema","state":"2026-10-27T12:00:00","attributes":{}},
            "media_player.tv":{"entity_id":"media_player.tv","state":"idle","attributes":{"supported_features":2052,"source_list":["HDMI 1","HDMI 2"]}},
        }
    def state(self,i):return deepcopy(self.states.get(i))
    def entity_ids(self):return list(self.states)
    def has_service(self,d,a):return True
    def now(self):return self.clock
    async def save(self,data):
        if self.disk_failure:raise OSError("disk unavailable")
        self.saved.append(deepcopy(data))
    async def call(self,actor,entity_id,action,data):
        self.calls.append((actor.id,entity_id,action,deepcopy(data)))
        if self.wait:await self.wait.wait()
        if self.call_failure:raise RuntimeError("service failed with password=SECRET")


class EngineTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.adapter=Adapter();self.admin=Actor("owner","Owner",True,lambda _:True,lambda _:True)
        self.member=Actor("member","Family",False,lambda _:True,lambda _:True)
        self.document={"revision":2,"layout":{"name":"My home","subtitle":"Welcome home.","rooms":[{"id":"living","name":"Living","entities":list(self.adapter.states)}],"quick_actions":[]},"routines":[]}
        self.engine=StudioEngine(self.adapter,self.document,controls=True)
    def request(self,**values):return {"request_id":"request-1234567890","expires_at":1015,"entity_id":"light.one","action":"turn_off","data":{},**values}
    async def error(self,code,awaitable):
        with self.assertRaises(ProductError) as caught:await awaitable
        self.assertEqual(caught.exception.code,code)

    async def test_default_is_read_only(self):
        engine=StudioEngine(self.adapter,self.document)
        await self.error("read_only",engine.command(self.admin,self.request()));self.assertFalse(self.adapter.calls)
    async def test_member_cannot_publish_or_discover(self):
        await self.error("not_allowed",self.engine.publish(self.member,self.document["layout"],2))
        with self.assertRaises(ProductError):self.engine.snapshot(self.member,discover=True)
        self.assertFalse(self.adapter.saved)
    async def test_permissions_are_intersection_not_admin_override(self):
        restricted=Actor("restricted","Restricted",True,lambda _:True,lambda _:False)
        await self.error("not_allowed",self.engine.command(restricted,self.request()));self.assertFalse(self.adapter.calls)
    async def test_snapshot_filters_permissions_and_secrets(self):
        restricted=Actor("x","Guest",False,lambda i:i=="light.one",lambda _:False)
        data=self.engine.bootstrap(restricted);self.assertEqual(len(data["entities"]),1)
        self.assertEqual(data["entities"][0]["operations"],{});self.assertNotIn("NEVER_RETURN",json.dumps(data));self.assertNotIn("entity_picture",json.dumps(data));self.assertFalse(data["user"]["can_edit"])
    async def test_supported_flags_not_fake_sliders(self):
        caps=module.capabilities(self.adapter.state("cover.blind"),self.adapter.has_service)
        self.assertNotIn("set_cover_position",caps);self.assertNotIn("stop_cover",caps)
        await self.error("not_supported",self.engine.command(self.admin,self.request(entity_id="cover.blind",action="set_cover_position",data={"position":50})))
        self.assertFalse(self.adapter.calls)
    async def test_missing_service_is_not_exposed(self):
        self.assertFalse(module.capabilities(self.adapter.state("light.one"),lambda *_:False))
    async def test_no_arbitrary_service_target_or_payload(self):
        await self.error("not_supported",self.engine.command(self.admin,self.request(action="toggle")))
        await self.error("not_supported",self.engine.command(self.admin,self.request(data={"entity_id":"all"})))
        await self.error("invalid_input",self.engine.command(self.admin,self.request(target={"area_id":"all"})))
        self.assertFalse(self.adapter.calls)
    async def test_unmanaged_control_rejected(self):
        self.engine.document["layout"]["rooms"][0]["entities"].remove("light.one")
        await self.error("not_allowed",self.engine.command(self.member,self.request()))
    async def test_numeric_values_strict(self):
        for value in [True,-1,101,float("nan"),"50"]:
            with self.assertRaises((ProductError,ValueError)):await self.engine.command(self.admin,self.request(action="turn_on",data={"brightness_pct":value}))
        self.assertFalse(self.adapter.calls)
    async def test_offline_and_stale_state_rejected(self):
        await self.error("state_changed",self.engine.command(self.member,self.request(expected_state="off")))
        self.adapter.states["light.one"]["state"]="unavailable"
        await self.error("device_offline",self.engine.command(self.member,self.request()));self.assertFalse(self.adapter.calls)
    async def test_expired_not_queued(self):
        await self.error("command_expired",self.engine.command(self.admin,self.request(expires_at=1000)))
        self.assertFalse(self.adapter.calls)
    async def test_duplicate_request_dispatched_once(self):
        first=await self.engine.command(self.member,self.request());second=await self.engine.command(self.member,self.request())
        self.assertEqual(first,second);self.assertEqual(len(self.adapter.calls),1)
        await self.error("request_reused",self.engine.command(self.member,self.request(action="turn_on")))
    async def test_inflight_duplicate_returns_pending(self):
        self.adapter.wait=asyncio.Event();task=asyncio.create_task(self.engine.command(self.member,self.request()))
        await asyncio.sleep(0)
        result=await self.engine.command(self.member,self.request());self.assertEqual(result["status"],"pending")
        self.adapter.wait.set();await task;self.assertEqual(len(self.adapter.calls),1)
    async def test_room_any_on_turns_every_member_off(self):
        result=await self.engine.command(self.member,{"request_id":"room-request-12345678","expires_at":1015,"room_id":"living","category":"light"})
        self.assertEqual(result["status"],"accepted");self.assertEqual([c[2] for c in self.adapter.calls],["turn_off","turn_off"])
    async def test_room_all_off_turns_all_on(self):
        self.adapter.states["light.one"]["state"]="off"
        await self.engine.command(self.member,{"request_id":"room-request-12345678","expires_at":1015,"room_id":"living","category":"light"})
        self.assertEqual([c[2] for c in self.adapter.calls],["turn_on","turn_on"])
    async def test_room_preflight_prevents_partial_permission_failure(self):
        restricted=Actor("x","Family",False,lambda _:True,lambda i:i!="light.two")
        await self.error("not_allowed",self.engine.command(restricted,{"request_id":"room-request-12345678","expires_at":1015,"room_id":"living","category":"light"}));self.assertFalse(self.adapter.calls)
    async def test_alarm_code_required_not_logged_or_persisted(self):
        await self.error("code_required",self.engine.command(self.member,self.request(entity_id="alarm_control_panel.home",action="alarm_disarm")))
        await self.engine.command(self.member,self.request(entity_id="alarm_control_panel.home",action="alarm_disarm",data={"code":"987654"}))
        self.assertNotIn("987654",str(self.engine.requests));self.assertNotIn("987654",json.dumps(list(self.engine.activity)));self.assertFalse(self.adapter.saved)
    async def test_service_error_redacted_and_not_retried(self):
        self.adapter.call_failure=True;result=await self.engine.command(self.member,self.request())
        self.assertEqual(result["status"],"check_required");self.assertNotIn("SECRET",json.dumps(result));await self.engine.command(self.member,self.request());self.assertEqual(len(self.adapter.calls),1)
    async def test_source_values_limited_to_device_choices(self):
        await self.error("invalid_input",self.engine.command(self.member,self.request(entity_id="media_player.tv",action="select_source",data={"source":"http://unsafe"})))
    async def test_revision_conflict_never_overwrites(self):
        await self.error("revision_conflict",self.engine.publish(self.admin,self.document["layout"],1));self.assertFalse(self.adapter.saved)
        result=await self.engine.publish(self.admin,self.document["layout"],2);self.assertEqual(result["revision"],3)
    async def test_failed_disk_commit_keeps_previous_layout(self):
        self.adapter.disk_failure=True;value=deepcopy(self.document["layout"]);value["name"]="Changed"
        with self.assertRaises(OSError):await self.engine.publish(self.admin,value,2)
        self.assertEqual(self.engine.document,self.document)
    async def test_layout_input_limits_and_duplicates(self):
        value=deepcopy(self.document["layout"]);value["rooms"].append(value["rooms"][0])
        await self.error("invalid_input",self.engine.publish(self.admin,value,2))
    async def test_request_cache_does_not_evict_unexpired_commands(self):
        self.engine.requests.update({("other",str(i)):(b"",{"status":"accepted"},1010) for i in range(2048)})
        await self.error("busy",self.engine.command(self.member,self.request()));self.assertFalse(self.adapter.calls)
    async def test_routine_removal_admin_and_revision_enforced(self):
        self.engine.document['routines']=[{"id":"evening","actions":[]}]
        await self.error("not_allowed",self.engine.remove_routine(self.member,"evening",2))
        await self.error("revision_conflict",self.engine.remove_routine(self.admin,"evening",1))
        result=await self.engine.remove_routine(self.admin,"evening",2);self.assertEqual(result['routines'],[]);self.assertEqual(result['revision'],3);self.assertFalse(self.adapter.calls)
    async def test_routines_are_backend_validated_and_no_alarm_codes(self):
        routine={"id":"sleep","name":"Sleep lights","time":"23:00","days":[0,1,2,3,4,5,6],"enabled":True,"actions":[{"entity_id":"light.one","action":"turn_off","data":{}}]}
        await self.error("not_allowed",self.engine.save_routine(self.member,routine,2))
        result=await self.engine.save_routine(self.admin,routine,2);self.assertEqual(result["revision"],3);self.assertFalse(self.adapter.calls)
        routine["actions"]=[{"entity_id":"alarm_control_panel.home","action":"alarm_disarm","data":{"code":"secret"}}]
        await self.error("not_supported",self.engine.save_routine(self.admin,routine,3));self.assertNotIn("secret",json.dumps(self.adapter.saved))

    def bundle_preview(self,actor=None,**extra):
        return self.engine.preview_bundle(actor or self.admin,"evening_comfort",{"targets":{"lights":["light.one"],"curtains":["cover.blind"]},"time":"19:30","days":[0,1,2,3,4,5,6],**extra},self.engine.document['revision'])
    async def test_bundles_are_inert_and_do_not_auto_create(self):
        result=self.engine.bundle_library(self.admin);self.assertEqual(len(result['bundles']),4);self.assertFalse(result['automatic_installation']);self.engine.bootstrap(self.admin)
        self.assertEqual(self.engine.document['routines'],[]);self.assertFalse(self.adapter.saved);self.assertFalse(self.adapter.calls)
    async def test_bundle_preview_is_read_only_and_approval_creates_paused(self):
        preview=self.bundle_preview();self.assertFalse(preview['writes']);self.assertFalse(preview['executes_devices']);self.assertFalse(self.adapter.saved)
        result=await self.engine.approve_bundle(self.admin,preview['approval_nonce']);self.assertTrue(result['created']);self.assertFalse(result['enabled']);self.assertFalse(self.adapter.calls)
        routine=self.engine.document['routines'][0];self.assertEqual(len(routine['actions']),2);self.assertEqual(routine['origin']['approved_by'],'owner');self.assertEqual(routine['origin']['bundle_version'],1)
        self.assertNotIn(preview['approval_nonce'],json.dumps(self.adapter.saved));self.assertNotIn('approval_key',json.dumps(self.engine.routines(self.member)))
    async def test_bundle_approval_requires_own_admin_review(self):
        with self.assertRaises(ProductError):self.bundle_preview(self.member)
        preview=self.bundle_preview();other=Actor('other','Other administrator',True,lambda _:True,lambda _:True)
        await self.error('approval_required',self.engine.approve_bundle(other,preview['approval_nonce']))
        await self.error('not_allowed',self.engine.approve_bundle(self.member,preview['approval_nonce']))
        await self.error('approval_required',self.engine.approve_bundle(self.admin,'invented-review-identity-123456'))
    async def test_bundle_approval_expired_or_revision_stale(self):
        preview=self.bundle_preview();self.adapter.clock+=301
        await self.error('approval_expired',self.engine.approve_bundle(self.admin,preview['approval_nonce']))
        self.adapter.clock=1000;preview=self.bundle_preview();self.engine.document['revision']+=1
        await self.error('revision_conflict',self.engine.approve_bundle(self.admin,preview['approval_nonce']));self.assertFalse(self.adapter.saved)
    async def test_bundle_approval_rechecks_capability_and_permission(self):
        preview=self.bundle_preview();self.adapter.states['cover.blind']['attributes']['supported_features']=1
        await self.error('not_supported',self.engine.approve_bundle(self.admin,preview['approval_nonce']));self.assertFalse(self.adapter.saved)
    async def test_bundle_approval_failure_can_retry_without_duplicates(self):
        preview=self.bundle_preview();self.adapter.disk_failure=True
        with self.assertRaises(OSError):await self.engine.approve_bundle(self.admin,preview['approval_nonce'])
        self.assertFalse(self.engine.document['routines']);self.adapter.disk_failure=False
        first=await self.engine.approve_bundle(self.admin,preview['approval_nonce']);second=await self.engine.approve_bundle(self.admin,preview['approval_nonce'])
        self.assertEqual(first['routine_id'],second['routine_id']);self.assertFalse(second['created']);self.assertEqual(len(self.engine.document['routines']),1)
    async def test_bundle_enable_is_explicit_and_user_changes_are_preserved(self):
        preview=self.bundle_preview();result=await self.engine.approve_bundle(self.admin,preview['approval_nonce'],True);self.assertTrue(result['enabled'])
        routine=self.engine.routines(self.admin)[0];routine.pop('origin');routine['name']='My own evening';routine['time']='20:15'
        await self.engine.save_routine(self.admin,routine,self.engine.document['revision']);saved=self.engine.document['routines'][0]
        self.assertEqual(saved['name'],'My own evening');self.assertTrue(saved['origin']['customized']);self.engine.bundle_library(self.admin);self.assertEqual(self.engine.document['routines'][0]['time'],'20:15')
    async def test_bundle_invalid_targets_and_unknown_parameters_rejected(self):
        with self.assertRaises(ProductError):self.bundle_preview(targets={'lights':['alarm_control_panel.home']})
        with self.assertRaises(ProductError):self.bundle_preview(secret='never accepted')
        self.assertFalse(self.adapter.saved);self.assertFalse(self.adapter.calls)


if __name__=="__main__":unittest.main()
