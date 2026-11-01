"""VAutomate Studio: a scoped, versioned compatibility service."""
from __future__ import annotations

from datetime import timedelta
import base64
import asyncio
import time
from collections import OrderedDict
import logging
from pathlib import Path
from aiohttp import web

try:
    import probatio as vol
except ImportError:
    import voluptuous as vol

from homeassistant.auth.permissions.const import POLICY_CONTROL, POLICY_READ
from homeassistant.components import websocket_api
from homeassistant.components.http import StaticPathConfig, HomeAssistantView
from homeassistant.components.http.const import KEY_HASS_USER, KEY_HASS
from homeassistant.const import __version__ as CORE_VERSION, EVENT_STATE_CHANGED
from homeassistant.core import Context,callback
from homeassistant.helpers import entity_registry as er, device_registry as dr, area_registry as ar
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .engine import Actor, StudioEngine, ProductError, PREFIX, BRIDGE_VERSION, number
from .rule_runtime import AutomationRuntime
from . import commissioning
from .rules import compile_script
from .rule_templates import library as rule_library
from .home_backups import HomeBackups,backup_id
from .ha_backups import HABackups
from .household import Household
from .ha_household import HAHousehold
from .pairing import Pairing
from .ha_pairing import HAPairing
from .replacement import Replacement
from .compatibility import status as compatibility_status,guard as compatibility_guard
from .document import normalize as normalize_document
from .integration_setup import IntegrationSetup
from .ha_integrations import HAIntegrations
from .remote_access import RemoteAccess,HARemote

DOMAIN="vautomate_studio"
_LOGGER=logging.getLogger(__name__)


def actor_for(user):
    if user is None or not user.is_active or user.system_generated:
        raise ProductError("not_allowed","Sign in with an active home account.")
    return Actor(user.id,user.name or "Home member",user.is_admin,lambda entity_id:user.permissions.check_entity(entity_id,POLICY_READ),lambda entity_id:user.permissions.check_entity(entity_id,POLICY_CONTROL))


class HAAdapter:
    def __init__(self,hass,store):
        self.hass=hass;self.store=store;self.version=CORE_VERSION;self.time_zone=hass.config.time_zone
        self.history_jobs=asyncio.Semaphore(2);self.camera_jobs=asyncio.Semaphore(2);self.camera_cache=OrderedDict()
    def weather_daylight(self):
        from homeassistant.helpers.sun import is_up
        try:return is_up(self.hass)
        except (ValueError,TypeError):return None

    def state(self,entity_id):
        state=self.hass.states.get(entity_id)
        return state.as_dict() if state else None
    def entity_ids(self):return self.hass.states.async_entity_ids()
    def has_service(self,domain,action):return self.hass.services.has_service(domain,action)
    def now(self):return dt_util.utcnow().timestamp()
    def monotonic(self):return time.monotonic()
    def local_clock(self):return dt_util.now().strftime("%H:%M")
    def next_sun(self,event,offset_minutes):
        from homeassistant.helpers.sun import get_astral_event_next
        return get_astral_event_next(self.hass,event,offset=timedelta(minutes=offset_minutes)).timestamp()
    async def save(self,document):await self.store.async_save(normalize_document(document))
    async def validate_native(self,rule):
        from homeassistant.helpers import config_validation as cv,script
        sequence,_=compile_script(rule)
        return await script.async_validate_actions_config(self.hass,cv.SCRIPT_SCHEMA(sequence))
    async def run_native(self,rule,trigger_id,execution_id):
        from homeassistant.helpers.script import Script
        sequence=await self.validate_native(rule)
        execution=self.hass.data[DOMAIN]["runtime"].check(execution_id)
        program=Script(self.hass,sequence,rule["name"],DOMAIN,script_mode="single",log_exceptions=False,logger=_LOGGER)
        try:
            result=await program.async_run({"studio_execution_id":execution_id,"trigger":{"id":trigger_id}},context=Context(user_id=execution["owner_id"]))
            return result is not None
        finally:await asyncio.shield(program.async_unload())
    async def call(self,actor,entity_id,action,data):
        compatibility_guard(CORE_VERSION,'command')
        # Permissions can be revoked after bootstrap. Re-read identity for every dispatch.
        user=await self.hass.auth.async_get_user(actor.id);current=actor_for(user)
        if not current.control(entity_id):raise ProductError("not_allowed","This account can no longer control this device.")
        await self.hass.services.async_call(entity_id.split(".")[0],action,dict(data),target={"entity_id":entity_id},blocking=True,context=Context(user_id=actor.id))
    def is_system_entity(self,entity_id):
        entry=er.async_get(self.hass).async_get(entity_id)
        return bool(entry and (entry.entity_category or entry.disabled_by))

    async def discover(self,actor):
        entities=er.async_get(self.hass);devices=dr.async_get(self.hass);areas=ar.async_get(self.hass)
        return {"areas":[{"id":a.id,"name":a.name} for a in areas.async_list_areas()],"devices":[{"id":d.id,"name":d.name_by_user or d.name or "Device","area_id":d.area_id,"manufacturer":d.manufacturer,"model":d.model} for d in devices.devices.values()],"registry":[{"entity_id":e.entity_id,"device_id":e.device_id,"area_id":e.area_id,"disabled":bool(e.disabled_by),"diagnostic":bool(e.entity_category),"name":e.name} for e in entities.entities.values() if actor.read(e.entity_id)]}
    async def history(self,entity_id,hours):
        if "recorder" not in self.hass.config.components:raise ProductError("not_supported","Recording is not configured for this home.")
        from homeassistant.components.recorder import get_instance,history
        from homeassistant.const import COMPRESSED_STATE_STATE,COMPRESSED_STATE_LAST_UPDATED
        end=dt_util.utcnow()
        def read():
            values=history.get_significant_states(self.hass,end-timedelta(hours=hours),end,[entity_id],None,True,False,False,True,True).get(entity_id,[])
            # Bound the response and retain the final reading.
            step=max(1,(len(values)+1998)//1999);sample=values[::step]
            if values and (not sample or sample[-1] is not values[-1]):sample.append(values[-1])
            return [{"time":s[COMPRESSED_STATE_LAST_UPDATED],"value":s[COMPRESSED_STATE_STATE]} for s in sample]
        if self.history_jobs.locked():raise ProductError("busy","History is busy. Please try again shortly.")
        async with self.history_jobs:return {"points":await get_instance(self.hass).async_add_executor_job(read)}
    async def camera(self,entity_id):
        from homeassistant.components.camera import async_get_image
        cached=self.camera_cache.get(entity_id)
        if cached and self.now()-cached[0]<3:return cached[1]
        if self.camera_jobs.locked():raise ProductError("busy","Camera previews are busy. Please try again shortly.")
        async with self.camera_jobs:
            image=await async_get_image(self.hass,entity_id,timeout=10)
            if image.content_type not in {"image/jpeg","image/png","image/webp"} or len(image.content)>5_000_000:
                raise ProductError("not_supported","This camera did not provide a supported preview image.")
            result={"content_type":image.content_type,"image":base64.b64encode(image.content).decode("ascii")}
            self.camera_cache[entity_id]=(self.now(),result)
            while len(self.camera_cache)>4:self.camera_cache.popitem(last=False)
            return result


async def async_setup(hass,config):return True


class StudioHealthView(HomeAssistantView):
    url="/api/vautomate_studio/v1/health"
    name="api:vautomate_studio:health"
    requires_auth=True

    async def get(self,request):
        user=request[KEY_HASS_USER]
        if not user.is_active or not user.is_admin:
            raise web.HTTPForbidden()
        return web.json_response({"api_version":1,"bridge_version":BRIDGE_VERSION,"initialized":DOMAIN in request.app[KEY_HASS].data})


class StudioBackupExportView(HomeAssistantView):
    url="/api/vautomate_studio/v1/backups/export"
    name="api:vautomate_studio:backups:export"
    requires_auth=True

    async def post(self,request):
        try:
            actor=actor_for(await request.app[KEY_HASS].auth.async_get_user(request[KEY_HASS_USER].id))
            if not actor.admin:raise web.HTTPForbidden()
            current=request.app[KEY_HASS].data.get(DOMAIN)
            if not current:raise web.HTTPServiceUnavailable()
            if request.content_length is None or request.content_length>1024:raise web.HTTPBadRequest()
            payload=await request.json()
            if not isinstance(payload,dict) or set(payload)!={"backup_id"}:raise web.HTTPBadRequest()
            identity=backup_id(payload["backup_id"])
            token=await current["backups"].prepare_download(actor,identity)
            path="/api/vautomate_studio/v1/backups/download/"+identity
            response=web.json_response({"download":path})
            response.set_cookie("va_backup",token,path=path,max_age=300,httponly=True,secure=request.secure,samesite="Strict")
            response.headers["Cache-Control"]="no-store"
            return response
        except ProductError as error:
            return web.json_response({"code":error.code,"message":str(error)},status=403 if error.code=="not_allowed" else 400)
        except (ValueError,TypeError):
            raise web.HTTPBadRequest() from None


class StudioBackupDownloadView(HomeAssistantView):
    url="/api/vautomate_studio/v1/backups/download/{identity}"
    name="api:vautomate_studio:backups:download"
    requires_auth=False

    async def get(self,request,identity):
        current=request.app[KEY_HASS].data.get(DOMAIN)
        if not current:raise web.HTTPServiceUnavailable()
        try:
            result=await current["backups"].download(request.cookies.get("va_backup"),identity)
            response=result if isinstance(result,web.StreamResponse) else web.StreamResponse(headers=result["headers"])
            response.del_cookie("va_backup",path="/api/vautomate_studio/v1/backups/download/"+identity)
            if isinstance(result,dict):
                stream=result["stream"]
                try:
                    await response.prepare(request)
                    async for chunk in stream:await response.write(chunk)
                    await response.write_eof()
                finally:
                    if hasattr(stream,"aclose"):await stream.aclose()
            return response
        except ProductError:
            raise web.HTTPForbidden() from None


class StudioBackupUploadView(HomeAssistantView):
    url="/api/vautomate_studio/v1/backups/import"
    name="api:vautomate_studio:backups:import"
    requires_auth=True

    async def post(self,request):
        user=await request.app[KEY_HASS].auth.async_get_user(request[KEY_HASS_USER].id)
        try:actor=actor_for(user)
        except ProductError:raise web.HTTPForbidden() from None
        if not actor.admin:raise web.HTTPForbidden()
        try:compatibility_guard(CORE_VERSION,'backups/import')
        except ProductError:raise web.HTTPConflict(reason='Install a compatible VAutomate release before importing a backup.') from None
        current=request.app[KEY_HASS].data.get(DOMAIN)
        if not current:raise web.HTTPServiceUnavailable()
        # Reject unsupported/unbounded requests before handing a stream to the manager.
        if request.content_length is None or request.content_length>4*1024**3:raise web.HTTPRequestEntityTooLarge(max_size=4*1024**3,actual_size=request.content_length or 0)
        try:
            reader=await request.multipart()
            contents=await reader.next()
            if contents is None or contents.name!="file" or not contents.filename or not contents.filename.lower().endswith(".tar"):
                raise web.HTTPBadRequest()
            await current["backups"].adapter.authorize(actor.id)
            identity=await current["backups"].adapter.receive(contents)
            return web.json_response({"backup_id":identity,"restored":False},status=201,headers={"Cache-Control":"no-store"})
        except web.HTTPException:raise
        except Exception:
            return web.json_response({"code":"import_failed","message":"The copy could not be imported. Check recovery status, available storage and that you selected a Home Assistant backup archive."},status=400)


async def async_setup_entry(hass,entry):
    store=Store(hass,1,"vautomate_studio.commercial.v1")
    document=await store.async_load()
    if document is not None:document=normalize_document(document)
    adapter=HAAdapter(hass,store)
    engine=StudioEngine(adapter,document,controls=entry.options.get("allow_evaluation_controls",False) and compatibility_status(CORE_VERSION)['writes_allowed'])
    if "installation_id" not in engine.document:
        engine.document["installation_id"]=engine.installation_id
        await store.async_save(engine.document)
    hass.data[DOMAIN]={"engine":engine,"entry":entry,"last_tick":None,"backups":HomeBackups(HABackups(hass)),"household":Household(HAHousehold(hass))}
    pairing=Pairing(engine,HAPairing(hass,entry))
    hass.data[DOMAIN]['replacements']=Replacement(engine,pairing.adapter.authorize)
    integration_adapter=HAIntegrations(hass,pairing.adapter.authorize)
    hass.data[DOMAIN]['integrations']=IntegrationSetup(engine,integration_adapter)
    hass.data[DOMAIN]['remote']=RemoteAccess(engine,HARemote(hass,integration_adapter))
    try:
        await pairing.initialize()
        hass.data[DOMAIN]["pairing"]=pairing
    except Exception:
        # Keep device controls and recovery available if the separate journal is damaged.
        _LOGGER.error("VAutomate pairing records need recovery; the stored record was kept")
    if not hass.data.get(DOMAIN+"_registered"):
        hass.http.register_view(StudioHealthView)
        hass.http.register_view(StudioBackupExportView)
        hass.http.register_view(StudioBackupDownloadView)
        hass.http.register_view(StudioBackupUploadView)
        await hass.http.async_register_static_paths([StaticPathConfig("/vautomate-studio",str(Path(__file__).parent/"www"),cache_headers=False)])
        websocket_api.async_register_command(hass,studio_request)
        hass.data[DOMAIN+"_registered"]=True

    async def resolve_actor(user_id):return actor_for(await hass.auth.async_get_user(user_id))
    runtime=AutomationRuntime(engine,resolve_actor,create_task=lambda coro:hass.async_create_background_task(coro,"VAutomate automation run"))
    hass.data[DOMAIN]["runtime"]=runtime

    async def execute_step(call):
        current=hass.data.get(DOMAIN)
        if not current:raise ProductError("unavailable","Studio is not running.")
        await current["runtime"].execute_step(call.data["execution_id"],call.data["step_id"],call.context.user_id)
    hass.services.async_register(DOMAIN,"execute_step",execute_step,schema=vol.Schema({vol.Required("execution_id"):str,vol.Required("step_id"):str}))

    @callback
    def on_state(event):
        if not hass.data.get(DOMAIN):return
        old=event.data.get("old_state");new=event.data.get("new_state")
        runtime.state_changed(event.data["entity_id"],old.as_dict() if old else None,new.as_dict() if new else None)
    entry.async_on_unload(hass.bus.async_listen(EVENT_STATE_CHANGED,on_state))

    @callback
    def automation_tick(now):runtime.tick(dt_util.as_local(now))
    entry.async_on_unload(async_track_time_interval(hass,automation_tick,timedelta(seconds=1)))

    async def run_due(now):
        engine=hass.data[DOMAIN]["engine"]
        if not engine.controls:return
        local=dt_util.as_local(now);minute=local.strftime("%Y-%m-%dT%H:%M")
        if hass.data[DOMAIN]["last_tick"]==minute:return
        hass.data[DOMAIN]["last_tick"]=minute
        for routine in list(engine.document.get("routines",[])):
            if not routine["enabled"] or engine.actions_held(routine["actions"]) or local.weekday() not in routine["days"] or local.strftime("%H:%M")!=routine["time"]:continue
            try:
                owner=actor_for(await hass.auth.async_get_user(routine["owner_id"]));engine.admin(owner)
                # Persist reservation first: a restart must not replay this minute's routine.
                async with engine.edit_lock:
                    current=next((r for r in engine.document.get("routines",[]) if r["id"]==routine["id"]),None)
                    if not current or not current["enabled"] or current!=routine:continue
                    if engine.document.get("routine_runs",{}).get(routine["id"])==minute:continue
                    from copy import deepcopy
                    candidate=deepcopy(engine.document);candidate.setdefault("routine_runs",{})[routine["id"]]=minute
                    await adapter.save(candidate);engine.document=candidate
                for index,action in enumerate(routine["actions"]):
                    if engine.actions_held(routine["actions"]) or not any(r["id"]==routine["id"] and r["enabled"] for r in engine.document.get("routines",[])):break
                    await engine.command(owner,{"request_id":f"routine-{routine['id']}-{minute}-{index}".replace(":","_")[:80],"expires_at":adapter.now()+15,**action})
            except Exception:
                # Never include the original request or service exception (which may contain secrets).
                engine.audit(Actor("system","Home routine",True,lambda _:False,lambda _:False),"routine_needs_attention",None,"check_required")

    entry.async_on_unload(async_track_time_interval(hass,run_due,timedelta(seconds=15)))
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass,entry):await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass,entry):
    current=hass.data.get(DOMAIN)
    if current:await current["runtime"].close()
    if current and "remote" in current:await current["remote"].shutdown()
    if current and "pairing" in current:await current["pairing"].adapter.close()
    if current and "integrations" in current:await current['integrations'].close()
    hass.services.async_remove(DOMAIN,"execute_step")
    hass.data.pop(DOMAIN,None)
    return True


@websocket_api.websocket_command({vol.Required("type"):PREFIX+"request",vol.Required("operation"):str,vol.Optional("payload",default={}):dict})
@websocket_api.async_response
async def studio_request(hass,connection,msg):
    """No arbitrary HA command proxy. All mutations terminate in product policy."""
    if DOMAIN not in hass.data:
        connection.send_error(msg["id"],"unavailable","The VAutomate service is not running.");return
    engine=hass.data[DOMAIN]["engine"]
    try:
        user=await hass.auth.async_get_user(connection.user.id) if connection.user else None
        actor=actor_for(user);op=msg["operation"];payload=msg["payload"]
        compatibility_guard(CORE_VERSION,op)
        if op=="bootstrap":result=engine.bootstrap(actor)
        elif op=="compatibility/status":result=compatibility_status(CORE_VERSION)
        elif op in {'integrations/status','integrations/preview','integrations/begin','integrations/step','integrations/cancel'}:
            manager=hass.data[DOMAIN]['integrations']
            if op=='integrations/status':result=await manager.status(actor)
            elif op=='integrations/preview':result=await manager.preview(actor,payload)
            elif op=='integrations/begin':result=await manager.begin(actor,payload)
            elif op=='integrations/step':result=await manager.step(actor,payload)
            else:result=await manager.cancel(actor,payload)
        elif op in {'remote/status','remote/preview','remote/enable','remote/signin','remote/disable'}:
            manager=hass.data[DOMAIN]['remote']
            if op=='remote/status':result=await manager.status(actor)
            elif op=='remote/preview':result=await manager.preview(actor,payload)
            elif op=='remote/enable':result=await manager.enable(actor,payload)
            elif op=='remote/signin':result=await manager.signin(actor,payload)
            else:result=await manager.disable(actor,payload)
        elif op=='registry/rename':
            engine.admin(actor);await hass.data[DOMAIN]['integrations'].adapter.authorize(actor.id)
            if set(payload)!={'entity_id','name','expected_name'} or not isinstance(payload['name'],str) or not 1<=len(payload['name'].strip())<=80:raise ProductError('invalid_input','Choose a name with one to 80 characters.')
            engine.entity(actor,payload['entity_id'],discover=True)
            registry=er.async_get(hass);entity=registry.async_get(payload['entity_id'])
            if entity is None:raise ProductError('not_supported','This integration does not register editable entity names.')
            if entity.name!=payload['expected_name']:raise ProductError('state_changed','This name changed. Open the device again before editing it.')
            registry.async_update_entity(entity.entity_id,name=payload['name'].strip());result={'saved':True}
        elif op=="replacements/status":result=await hass.data[DOMAIN]['replacements'].status(actor)
        elif op=="replacements/preview":result=await hass.data[DOMAIN]['replacements'].preview(actor,payload)
        elif op=="replacements/approve":result=await hass.data[DOMAIN]['replacements'].approve(actor,payload)
        elif op=="snapshot":result={"entities":engine.snapshot(actor),"revision":engine.document["revision"]}
        elif op=="discover":
            engine.admin(actor);result={"entities":engine.snapshot(actor,discover=True),**await engine.adapter.discover(actor)}
        elif op=="commissioning/status":result=commissioning.status(engine,actor)
        elif op=="commissioning/propose":
            engine.admin(actor);result=commissioning.suggest(engine,actor,await engine.adapter.discover(actor))
        elif op=="backups/status":result=await hass.data[DOMAIN]["backups"].status(actor)
        elif op=="backups/preview":result=await hass.data[DOMAIN]["backups"].preview(actor,payload)
        elif op=="backups/approve":result=await hass.data[DOMAIN]["backups"].approve(actor,payload)
        elif op=="accounts/me":result=await hass.data[DOMAIN]["household"].me(actor)
        elif op=="accounts/list":result=await hass.data[DOMAIN]["household"].people(actor)
        elif op=="accounts/preview":result=await hass.data[DOMAIN]["household"].preview(actor,payload)
        elif op=="accounts/approve":result=await hass.data[DOMAIN]["household"].approve(actor,payload)
        elif op=="accounts/password":result=await hass.data[DOMAIN]["household"].own_password(actor,payload)
        elif op in {"pairing/status","pairing/preview","pairing/begin","pairing/cancel","pairing/assign"}:
            engine.admin(actor)
            pairing=hass.data[DOMAIN].get("pairing")
            if pairing is None:raise ProductError("storage_attention","Pairing needs installer recovery. Your other home controls remain available.")
            if op=="pairing/status":result=await pairing.status(actor)
            elif op=="pairing/preview":result=await pairing.preview(actor,payload)
            elif op=="pairing/begin":result=await pairing.begin(actor,payload)
            elif op=="pairing/cancel":result=await pairing.cancel(actor,payload)
            else:result=await pairing.assign(actor,payload)
        elif op=="layout/preview":
            result={"layout":engine.validate_layout(actor,payload.get("layout")),"writes":False}
        elif op=="layout/publish":result=await engine.publish(actor,payload.get("layout"),payload.get("revision"))
        elif op=="command":result=await engine.command(actor,payload)
        elif op=="routine/save":result=await engine.save_routine(actor,payload.get("routine"),payload.get("revision"))
        elif op=="routine/remove":result=await engine.remove_routine(actor,payload.get("routine_id"),payload.get("revision"))
        elif op=="bundles/list":result=engine.bundle_library(actor)
        elif op=="bundles/preview":result=engine.preview_bundle(actor,payload.get("bundle_id"),payload.get("inputs"),payload.get("revision"))
        elif op=="bundles/approve":result=await engine.approve_bundle(actor,payload.get("approval_nonce"),payload.get("enabled",False))
        elif op=="automations/library":result={"templates":rule_library(),"can_create":actor.admin,"automatic_installation":False}
        elif op=="automations/preview":result=await engine.preview_automation(actor,payload.get("rule"),payload.get("revision"),template_id=payload.get("template_id"),inputs=payload.get("inputs"))
        elif op=="automations/approve":result=await engine.approve_automation(actor,payload.get("approval_nonce"),enabled=payload.get("enabled",False),shared_home_ack=payload.get("shared_home_ack",False),conflicts_ack=payload.get("conflicts_ack",False))
        elif op=="automations/remove":result=await engine.remove_automation(actor,payload.get("rule_id"),payload.get("revision"))
        elif op=="automations/pause":result=await engine.pause_automation(actor,payload.get("rule_id"),payload.get("revision"))
        elif op=="automations/traces":result={"runs":hass.data[DOMAIN]["runtime"].public_traces(actor)}
        elif op=="rooms/pause":result=await engine.set_room_pause(actor,payload.get("room_id"),payload.get("seconds"))
        elif op=="history":
            engine.entity(actor,payload.get("entity_id"));engine.rate(actor)
            hours=number(payload.get("hours",24),1,24)
            result=await engine.adapter.history(payload["entity_id"],hours)
        elif op=="camera/snapshot":
            entity=engine.entity(actor,payload.get("entity_id"));engine.rate(actor)
            if not entity["entity_id"].startswith("camera."):raise ProductError("not_supported","Choose a camera for the preview.")
            result=await engine.adapter.camera(entity["entity_id"])
        elif op=="activity":
            visible=engine.visible(actor);result={"items":[e for e in engine.activity if actor.admin or e["entity_id"] in visible]}
        elif op=="care":
            engine.admin(actor);result={"core_version":CORE_VERSION,"bridge_version":BRIDGE_VERSION,"read_only":not engine.controls,"checks":[{"name":"Home connection","status":"ok"},{"name":"Compatibility certification","status":"pending"},{"name":"Backup restore validation","status":"not_tested"},{"name":"Approved hardware","status":"pending"}],"offline":[s["entity_id"] for s in engine.snapshot(actor) if s["state"] in {"unavailable","unknown"}]}
        else:raise ProductError("not_supported","This feature is not available in this release.")
        connection.send_result(msg["id"],result)
    except ProductError as error:connection.send_error(msg["id"],error.code,str(error))
    except Exception:
        _LOGGER.error("A Studio operation failed; request details were withheld")
        connection.send_error(msg["id"],"home_error","Your home could not complete this request. Check its status before trying again.")
