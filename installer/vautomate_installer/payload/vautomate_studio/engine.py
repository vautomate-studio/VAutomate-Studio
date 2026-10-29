"""Versioned product policy, independent of Home Assistant implementation details."""
from __future__ import annotations

import asyncio
from collections import OrderedDict, deque
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import hmac
import json
import math
import re
import secrets
import uuid
import time
from typing import Any

from .bundles import BUNDLES
from .rule_store import RuleStore

API_VERSION = 1
BRIDGE_VERSION = "0.4.0-alpha.4"
PREFIX = "vautomate_studio/v1/"
DOMAINS = {"light", "cover", "switch", "fan", "climate", "media_player", "alarm_control_panel", "scene", "input_boolean", "binary_sensor", "sensor", "camera", "person", "weather"}
INFORMATIONAL = {"binary_sensor", "sensor", "camera", "person", "weather"}
SAFE_ATTRIBUTES = {"friendly_name", "unit_of_measurement", "device_class", "supported_features", "supported_color_modes", "brightness", "color_temp_kelvin", "min_color_temp_kelvin", "max_color_temp_kelvin", "current_position", "percentage", "temperature", "current_temperature", "min_temp", "max_temp", "target_temp_step", "hvac_modes", "hvac_action", "volume_level", "is_volume_muted", "source", "source_list", "media_title", "media_artist", "code_format", "code_arm_required", "temperature_unit", "humidity", "battery_level"}
ENTITY = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")
KEY = re.compile(r"^[a-zA-Z0-9_-]{1,80}$")


class ProductError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def fail(code: str, message: str):
    raise ProductError(code, message)


def text(value: Any, maximum: int = 80) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        fail("invalid_input", "Please check the name or description.")
    return value.strip()


def number(value: Any, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        fail("invalid_input", "The value is outside this device's supported range.")
    return value


def capabilities(state: dict, has_service) -> dict[str, list[str]]:
    """Only expose operations backed by both an entity feature and a real action."""
    entity_id = state["entity_id"]
    domain = entity_id.split(".")[0]
    attr = state.get("attributes", {})
    features = attr.get("supported_features", 0)
    features = features if isinstance(features, int) else 0
    operations: dict[str, list[str]] = {}
    def add(action, fields=(), bit=None):
        if (bit is None or features & bit) and has_service(domain, action):
            operations[action] = list(fields)
    if domain in {"light", "switch", "input_boolean"}:
        add("turn_on"); add("turn_off")
        modes = set(attr.get("supported_color_modes") or [])
        if domain == "light" and modes - {"onoff", "unknown"} and "turn_on" in operations:
            operations["turn_on"].append("brightness_pct")
        if domain == "light" and "color_temp" in modes and "turn_on" in operations:
            operations["turn_on"].append("color_temp_kelvin")
    elif domain == "fan":
        add("turn_on", bit=32); add("turn_off", bit=16); add("set_percentage", ["percentage"], 1)
    elif domain == "cover":
        for action, bit in [("open_cover", 1), ("close_cover", 2), ("stop_cover", 8)]: add(action, bit=bit)
        add("set_cover_position", ["position"], 4)
    elif domain == "media_player":
        for action, bit in [("turn_on",128),("turn_off",256),("media_play",16384),("media_pause",1),("media_stop",4096),("media_next_track",32),("media_previous_track",16)]: add(action, bit=bit)
        add("volume_set", ["volume_level"], 4); add("volume_mute", ["is_volume_muted"], 8); add("select_source", ["source"], 2048)
    elif domain == "alarm_control_panel":
        add("alarm_disarm", ["code"])
        for action, bit in [("alarm_arm_home",1),("alarm_arm_away",2),("alarm_arm_night",4)]: add(action, ["code"], bit)
    elif domain == "climate":
        if attr.get("hvac_modes"): add("set_hvac_mode", ["hvac_mode"])
        add("set_temperature", ["temperature"], 1)
    elif domain == "scene":
        add("turn_on")
    return operations


@dataclass
class Actor:
    id: str
    name: str
    admin: bool
    read: Any
    control: Any


class StudioEngine(RuleStore):
    """Only this service can publish Studio layout or dispatch product commands."""
    def __init__(self, adapter, document=None, *, controls=False):
        self.adapter = adapter
        self.document = deepcopy(document or {"revision": 0, "layout": {"name": "My home", "subtitle": "Your home, beautifully connected.", "rooms": [], "quick_actions": []}, "routines": []})
        self.installation_id = self.document.get("installation_id") or str(uuid.uuid4())
        self.controls = controls
        self.edit_lock = asyncio.Lock()
        self.room_locks: dict[str, asyncio.Lock] = {}
        self.requests: OrderedDict = OrderedDict()
        self.secret = secrets.token_bytes(32)
        self.rates: dict = {}
        self.activity = deque(maxlen=200)
        self.approvals: OrderedDict[str, dict] = OrderedDict()

    def admin(self, actor):
        if not actor.admin: fail("not_allowed", "An administrator must make this change.")

    def managed(self):
        return {entity_id for room in self.document["layout"]["rooms"] for entity_id in room["entities"]} | {q["entity_id"] for q in self.document["layout"]["quick_actions"]}

    def visible(self, actor):
        return {entity_id for entity_id in self.managed() if actor.read(entity_id)}

    def entity(self, actor, entity_id, *, control=False, discover=False):
        if not isinstance(entity_id, str) or not ENTITY.fullmatch(entity_id) or entity_id.split(".")[0] not in DOMAINS:
            fail("not_supported", "This device type is not supported in this edition.")
        if not actor.read(entity_id) or (control and not actor.control(entity_id)):
            fail("not_allowed", "This account cannot access this device.")
        if not discover and entity_id not in self.managed(): fail("not_allowed", "Ask your installer to add this device to your home.")
        state = self.adapter.state(entity_id)
        if not state: fail("device_missing", "This device is no longer available. Ask your installer to check it.")
        return state

    def snapshot(self, actor, *, discover=False):
        if discover: self.admin(actor)
        ids = self.adapter.entity_ids() if discover else sorted(self.visible(actor))
        output = []
        for entity_id in ids:
            if not ENTITY.fullmatch(entity_id) or entity_id.split(".")[0] not in DOMAINS or not actor.read(entity_id): continue
            state = self.adapter.state(entity_id)
            if not state: continue
            attrs = {key: deepcopy(value) for key, value in state.get("attributes", {}).items() if key in SAFE_ATTRIBUTES}
            # Codes, media URLs, signed camera URLs, GPS and integration-specific secrets never cross this API.
            output.append({"entity_id": entity_id, "state": state["state"], "attributes": attrs, "last_changed": state.get("last_changed"), "operations": capabilities(state, self.adapter.has_service) if actor.control(entity_id) else {}})
        return output

    def layout(self, actor):
        layout = deepcopy(self.document["layout"])
        visible = self.visible(actor)
        for room in layout["rooms"]: room["entities"] = [i for i in room["entities"] if i in visible]
        layout["rooms"] = [r for r in layout["rooms"] if r["entities"] or actor.admin]
        layout["quick_actions"] = [q for q in layout["quick_actions"] if q["entity_id"] in visible]
        return layout

    def bootstrap(self, actor):
        return {"api_version": API_VERSION, "bridge_version": BRIDGE_VERSION, "server_time":self.adapter.now(), "core_version": self.adapter.version, "compatibility": {"status":"evaluation", "certified":False, "message":"This release requires hardware and HAOS acceptance testing."}, "user": {"id": actor.id, "name": actor.name, "role": "administrator" if actor.admin else "member", "can_edit":actor.admin}, "read_only": not self.controls, "revision": self.document["revision"], "layout": self.layout(actor), "entities": self.snapshot(actor), "routines": self.routines(actor), "automations":self.automation_rules(actor), "room_pauses":self.active_room_pauses(actor), "features": {"lights":True,"curtains":True,"security":True,"media":True,"climate":True,"pairing":actor.admin,"updates":False,"backup_restore":actor.admin,"visual_automations":True,"room_pauses":True}}

    def validate_layout(self, actor, value):
        self.admin(actor)
        if not isinstance(value, dict) or set(value) - {"name","subtitle","rooms","quick_actions"}: fail("invalid_input", "Check the home layout.")
        rooms, quick = value.get("rooms"), value.get("quick_actions", [])
        if not isinstance(rooms, list) or len(rooms) > 80 or not isinstance(quick, list) or len(quick) > 4: fail("invalid_input", "Choose up to 80 rooms and four Home buttons.")
        result={"name":text(value.get("name")),"subtitle":text(value.get("subtitle", "Your home, beautifully connected."),160),"rooms":[],"quick_actions":[]}
        used=set(); names=set(); entity_count=0
        for room in rooms:
            if not isinstance(room,dict) or set(room)-{"id","name","entities"} or not isinstance(room.get("id"),str) or not KEY.fullmatch(room["id"]) or room["id"] in used: fail("invalid_input", "Each room needs a unique identity.")
            used.add(room["id"]); ids=room.get("entities")
            if not isinstance(ids,list) or len(ids)>200 or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids): fail("invalid_input","Review this room's devices.")
            for entity_id in ids:self.entity(actor,entity_id,discover=True)
            entity_count+=len(ids)
            name=text(room.get("name"))
            if name.casefold() in names:fail("invalid_input","Give each room a different name.")
            names.add(name.casefold())
            result["rooms"].append({"id":room["id"],"name":name,"entities":list(ids)})
        if entity_count>2000:fail("invalid_input","This home has too many dashboard selections.")
        quick_seen=set()
        for q in quick:
            if not isinstance(q,dict) or set(q)-{"entity_id","label"}:fail("invalid_input","Review the Home buttons.")
            entity_id=q.get("entity_id"); self.entity(actor,entity_id,discover=True)
            if entity_id.split(".")[0] not in {"scene","input_boolean"} or entity_id in quick_seen: fail("invalid_input","Choose distinct scenes or home modes for the four Home buttons.")
            quick_seen.add(entity_id);result["quick_actions"].append({"entity_id":entity_id,"label":text(q.get("label"))})
        return result

    async def publish(self, actor, value, revision):
        clean=self.validate_layout(actor,value)
        async with self.edit_lock:
            if type(revision) is not int or revision!=self.document["revision"]:fail("revision_conflict","This home was edited elsewhere. Refresh before saving again.")
            candidate=deepcopy(self.document);candidate.update(revision=revision+1,layout=clean);candidate.setdefault("installation_id",self.installation_id)
            # Disk commit must succeed before shared in-memory state changes.
            await self.adapter.save(candidate)
            self.document=candidate;self.notify_change()
        self.audit(actor,"layout_saved",None,"saved")
        return {"revision":self.document["revision"],"layout":self.layout(actor)}

    def audit(self, actor, action, entity_id, outcome):
        self.activity.appendleft({"time":self.adapter.now(),"actor":actor.name,"action":action,"entity_id":entity_id,"outcome":outcome})

    def rate(self, actor, security=False):
        now=self.adapter.now();key=(actor.id,security)
        if len(self.rates)>2048:self.rates={k:v for k,v in self.rates.items() if v and now-v[-1]<60}
        times=self.rates.setdefault(key,deque());window,limit=(60,5) if security else (10,40)
        while times and times[0]<now-window:times.popleft()
        if len(times)>=limit:fail("rate_limited","Please wait a moment before trying again.")
        times.append(now)

    def validate_operation(self, actor, entity_id, action, data):
        state=self.entity(actor,entity_id,control=True)
        if state["state"] in {"unknown","unavailable"}: fail("device_offline","This device is offline. Check its power or connection.")
        operations=capabilities(state,self.adapter.has_service)
        if action not in operations or not isinstance(data,dict) or set(data)-set(operations[action]): fail("not_supported","This device does not support that control.")
        attr=state.get("attributes",{});domain=entity_id.split(".")[0]
        required={"set_cover_position":"position","set_percentage":"percentage","volume_set":"volume_level","volume_mute":"is_volume_muted","select_source":"source","set_temperature":"temperature","set_hvac_mode":"hvac_mode"}.get(action)
        if required and required not in data:fail("invalid_input","Choose a value for this control.")
        for field,value in data.items():
            if field in {"brightness_pct","percentage","position"}:number(value,0,100)
            elif field=="volume_level":number(value,0,1)
            elif field=="is_volume_muted" and not isinstance(value,bool):fail("invalid_input","Choose mute on or off.")
            elif field=="color_temp_kelvin":number(value,attr.get("min_color_temp_kelvin",2000),attr.get("max_color_temp_kelvin",6500))
            elif field=="temperature":number(value,attr.get("min_temp",7),attr.get("max_temp",35))
            elif field=="source" and value not in attr.get("source_list",[]):fail("invalid_input","Choose one of this device's sources.")
            elif field=="hvac_mode" and value not in attr.get("hvac_modes",[]):fail("invalid_input","Choose one of this device's modes.")
            elif field=="code" and (not isinstance(value,str) or not 1<=len(value)<=64):fail("invalid_input","Enter a valid security code.")
        if domain=="alarm_control_panel" and (action=="alarm_disarm" or attr.get("code_arm_required",True)) and attr.get("code_format") and not data.get("code"):
            fail("code_required","Enter your security code to continue.")
        return domain

    async def command(self, actor, payload):
        if not self.controls:fail("read_only","This installation is in read-only evaluation mode.")
        if not isinstance(payload,dict) or set(payload)-{"request_id","expires_at","entity_id","action","data","expected_state","room_id","category"}:fail("invalid_input","Check this home command.")
        request_id=payload.get("request_id")
        if not isinstance(request_id,str) or not KEY.fullmatch(request_id) or len(request_id)<16:fail("invalid_input","This command needs a unique request identity.")
        now=self.adapter.now();expires=payload.get("expires_at")
        number(expires,now-1,now+30)
        if expires<=now:fail("command_expired","This command expired. Check the current state before trying again.")
        fingerprint=hmac.new(self.secret,json.dumps(payload,sort_keys=True,allow_nan=False).encode(),hashlib.sha256).digest();key=(actor.id,request_id)
        if key in self.requests:
            digest,result,_=self.requests[key]
            if not hmac.compare_digest(digest,fingerprint):fail("request_reused","This request identity was already used for another command.")
            return deepcopy(result)
        if len(self.requests)>=2048:
            # Never discard a running request in order to accept a new command.
            removable=next((k for k,(_,v,expiry) in self.requests.items() if v["status"]!="pending" and expiry<now),None)
            if removable is None:fail("busy","Your home is busy. Please check its status shortly.")
            self.requests.pop(removable)
        if payload.get("room_id") is not None:
            room=next((r for r in self.document["layout"]["rooms"] if r["id"]==payload["room_id"]),None)
            category=payload.get("category")
            if not room or category not in {"light","fan","switch"} or any(k in payload for k in {"entity_id","action","data","expected_state"}):fail("invalid_input","Choose a room control.")
            lock=self.room_locks.setdefault(room["id"]+":"+category,asyncio.Lock())
            if lock.locked():fail("busy","That room is already responding. Please wait for its status.")
            targets=[i for i in room["entities"] if i.startswith(category+".") and actor.read(i)]
            if not targets:fail("device_missing","There are no controls in this room.")
            # All members are checked before any device is operated.
            snapshots=[self.entity(actor,i,control=True) for i in targets]
            if any(s["state"] in {"unknown","unavailable"} for s in snapshots):fail("device_offline","A device in this room is offline. Use individual controls until it reconnects.")
            action="turn_off" if any(s["state"]=="on" for s in snapshots) else "turn_on"
            calls=[(i,action,{}) for i in targets]
        else:
            calls=[(payload.get("entity_id"),payload.get("action"),payload.get("data",{}))];lock=asyncio.Lock()
            if "expected_state" in payload and self.entity(actor,payload.get("entity_id"),control=True)["state"]!=payload["expected_state"]:fail("state_changed","The device changed. Check its current status and try again.")
        for entity_id,action,data in calls:self.validate_operation(actor,entity_id,action,data)
        self.rate(actor,any(i.startswith("alarm_control_panel.") for i,_,_ in calls))
        result={"request_id":request_id,"status":"pending","devices":[]};self.requests[key]=(fingerprint,result,expires)
        async with lock:
            for entity_id,action,data in calls:
                try:
                    if self.adapter.now()>expires:raise ProductError("command_expired","Command expired before dispatch.")
                    # Revalidate authorization and capability immediately before dispatch.
                    self.validate_operation(actor,entity_id,action,data)
                    await asyncio.wait_for(self.adapter.call(actor,entity_id,action,data),12)
                    outcome="accepted"
                except asyncio.CancelledError:
                    result["devices"].append({"entity_id":entity_id,"status":"unknown"});result["status"]="check_required";self.audit(actor,action,entity_id,"interrupted_check_state");raise
                except asyncio.TimeoutError:outcome="unknown"
                except Exception:outcome="failed"
                result["devices"].append({"entity_id":entity_id,"status":outcome})
                self.audit(actor,action,entity_id,outcome)
            result["status"]="accepted" if all(d["status"]=="accepted" for d in result["devices"]) else "check_required"
        return deepcopy(result)

    def routines(self, actor):
        visible=self.visible(actor)
        items=[]
        for routine in self.document.get("routines",[]):
            if not all(a["entity_id"] in visible for a in routine["actions"]):continue
            clean={key:deepcopy(routine[key]) for key in ["id","name","time","days","enabled","actions"]}
            if "origin" in routine:clean["origin"]={key:routine["origin"][key] for key in ["bundle_id","bundle_version","customized"]}
            items.append(clean)
        return items

    def validate_routine(self, actor, value):
        self.admin(actor)
        if not isinstance(value,dict) or set(value)-{"id","name","time","days","enabled","actions"}:fail("invalid_input","Review this routine.")
        if not isinstance(value.get("id"),str) or not KEY.fullmatch(value["id"]):fail("invalid_input","This routine needs an identity.")
        when=value.get("time")
        if not isinstance(when,str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",when):fail("invalid_input","Choose a time for this routine.")
        days=value.get("days")
        if not isinstance(days,list) or not days or any(type(d) is not int or d<0 or d>6 for d in days) or len(set(days))!=len(days):fail("invalid_input","Choose the days for this routine.")
        actions=value.get("actions")
        if not isinstance(actions,list) or not 1<=len(actions)<=20:fail("invalid_input","Choose one to twenty routine actions.")
        clean=[]
        for a in actions:
            if not isinstance(a,dict) or set(a)!={"entity_id","action","data"}:fail("invalid_input","Review this routine's actions.")
            # Unattended security/lock operations and secrets are deliberately excluded.
            if str(a.get("entity_id","")).split(".")[0] not in {"light","cover","switch","fan","climate","media_player","input_boolean"}:fail("not_supported","Security commands cannot be scheduled in this edition.")
            self.validate_operation(actor,a["entity_id"],a["action"],a["data"]);clean.append(deepcopy(a))
        if type(value.get("enabled")) is not bool:fail("invalid_input","Choose whether this routine is enabled.")
        return {"id":value["id"],"name":text(value.get("name")),"time":when,"days":days,"enabled":value["enabled"],"actions":clean,"owner_id":actor.id}

    async def save_routine(self, actor, value, revision):
        routine=self.validate_routine(actor,value)
        async with self.edit_lock:
            if type(revision) is not int or revision!=self.document["revision"]:fail("revision_conflict","Refresh this home before saving the routine.")
            previous=next((r for r in self.document.get("routines",[]) if r["id"]==routine["id"]),None)
            if previous and "origin" in previous:
                routine["origin"]={**deepcopy(previous["origin"]),"customized":True}
                if "approval_key" in previous:routine["approval_key"]=previous["approval_key"]
            candidate=deepcopy(self.document);items=[r for r in candidate.get("routines",[]) if r["id"]!=routine["id"]]
            if len(items)>=100:fail("invalid_input","This home already has 100 routines.")
            candidate.update(revision=revision+1,routines=items+[routine]);await self.adapter.save(candidate);self.document=candidate;self.notify_change()
        self.audit(actor,"routine_saved",None,"saved")
        return {"revision":self.document["revision"],"routines":self.routines(actor)}

    def bundle_library(self,actor):
        return {"bundles":deepcopy(list(BUNDLES)),"can_create":actor.admin,"automatic_installation":False}

    def preview_bundle(self,actor,bundle_id,inputs,revision):
        self.admin(actor)
        if type(revision) is not int or revision!=self.document["revision"]:fail("revision_conflict","Refresh this home before reviewing a routine.")
        bundle=next((b for b in BUNDLES if b["id"]==bundle_id),None)
        if not bundle:fail("not_supported","This bundled routine is not available in this version.")
        if not isinstance(inputs,dict) or set(inputs)-{"name","time","days","targets"}:fail("invalid_input","Review the routine's choices.")
        targets=inputs.get("targets")
        if not isinstance(targets,dict) or set(targets)-{s["id"] for s in bundle["slots"]}:fail("invalid_input","Choose devices for this routine.")
        actions=[]
        for slot in bundle["slots"]:
            ids=targets.get(slot["id"],[])
            if not isinstance(ids,list) or len(ids)>20 or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids) or (slot["required"] and not ids):fail("invalid_input","Review: "+slot["label"])
            for entity_id in ids:
                if entity_id.split(".")[0]!=slot["domain"]:fail("invalid_input","Choose a matching device for "+slot["label"])
                actions.append({"entity_id":entity_id,"action":slot["action"],"data":{}})
        routine=self.validate_routine(actor,{"id":"bundle-"+secrets.token_hex(12),"name":inputs.get("name",bundle["name"]),"time":inputs.get("time",bundle["default_time"]),"days":inputs.get("days",list(range(7))),"actions":actions,"enabled":False})
        now=self.adapter.now()
        for key in list(self.approvals):
            if self.approvals[key]["expires_at"]<now:self.approvals.pop(key)
        if len(self.approvals)>=128:fail("busy","Too many routine reviews are open. Please finish one or try again later.")
        nonce=secrets.token_urlsafe(24);key=hashlib.sha256(nonce.encode()).hexdigest()
        self.approvals[key]={"actor_id":actor.id,"routine":routine,"revision":revision,"expires_at":now+300,"bundle_id":bundle["id"],"bundle_version":bundle["version"]}
        public={k:deepcopy(v) for k,v in routine.items() if k!="owner_id"}
        return {"approval_nonce":nonce,"expires_at":now+300,"routine":public,"bundle_id":bundle["id"],"bundle_version":bundle["version"],"writes":False,"executes_devices":False}

    async def approve_bundle(self,actor,nonce,enabled=False):
        self.admin(actor)
        if not isinstance(nonce,str) or not 20<=len(nonce)<=100 or type(enabled) is not bool:fail("invalid_input","Review and approve the routine before creating it.")
        if enabled and not self.controls:fail("read_only","Create this routine paused while the home is in read-only evaluation.")
        key=hashlib.sha256(nonce.encode()).hexdigest()
        async with self.edit_lock:
            # Repeating a submitted approval returns its receipt, never another automation.
            previous=next((r for r in self.document.get("routines",[]) if r.get("approval_key")==key and r.get("origin",{}).get("approved_by")==actor.id),None)
            if previous:
                return {"revision":self.document["revision"],"routine_id":previous["id"],"created":False,"enabled":previous["enabled"]}
            approval=self.approvals.get(key)
            if not approval or approval.get("kind") not in {None,"routine"} or approval["actor_id"]!=actor.id:fail("approval_required","Review this routine on your own account before creating it.")
            if approval["expires_at"]<self.adapter.now():fail("approval_expired","This review expired. Review the current devices and approve again.")
            if approval["revision"]!=self.document["revision"]:fail("revision_conflict","The home changed after this review. Please review the routine again.")
            # Capabilities and permissions may have changed while the review was open.
            value={k:deepcopy(v) for k,v in approval["routine"].items() if k!="owner_id"};value["enabled"]=enabled
            routine=self.validate_routine(actor,value)
            routine["approval_key"]=key
            routine["origin"]={"bundle_id":approval["bundle_id"],"bundle_version":approval["bundle_version"],"customized":False,"approved_by":actor.id,"approved_at":self.adapter.now()}
            candidate=deepcopy(self.document)
            if len(candidate.get("routines",[]))>=100:fail("invalid_input","This home already has 100 routines.")
            candidate.setdefault("routines",[]).append(routine);candidate["revision"]+=1
            await self.adapter.save(candidate);self.document=candidate;self.notify_change();self.approvals.pop(key,None)
        self.audit(actor,"bundled_routine_approved",None,"created_enabled" if enabled else "created_paused")
        return {"revision":self.document["revision"],"routine_id":routine["id"],"created":True,"enabled":enabled}

    async def remove_routine(self,actor,routine_id,revision):
        self.admin(actor)
        if not isinstance(routine_id,str) or not KEY.fullmatch(routine_id):fail("invalid_input","Choose a routine to remove.")
        async with self.edit_lock:
            if type(revision) is not int or revision!=self.document["revision"]:fail("revision_conflict","Refresh this home before removing a routine.")
            candidate=deepcopy(self.document);items=candidate.get("routines",[])
            if not any(r["id"]==routine_id for r in items):fail("not_found","This routine was already removed.")
            candidate.update(revision=revision+1,routines=[r for r in items if r["id"]!=routine_id]);candidate.get("routine_runs",{}).pop(routine_id,None)
            await self.adapter.save(candidate);self.document=candidate;self.notify_change()
        self.audit(actor,"routine_removed",None,"saved")
        return {"revision":self.document["revision"],"routines":self.routines(actor)}
