"""Event triggers and revocable execution permits around HA's native script engine."""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from copy import deepcopy
import hashlib
import math
import secrets
import time

from .engine import ProductError,fail
from .rules import compile_script,evaluate,fingerprint,references,services


def numeric_match(trigger,state):
    if not state or state["state"] in {"unknown","unavailable"}:return False
    try:value=float(state["state"])
    except (TypeError,ValueError):return False
    return math.isfinite(value) and ("above" not in trigger or value>trigger["above"]) and ("below" not in trigger or value<trigger["below"])


def trigger_matches(trigger,state):
    if trigger["kind"]=="numeric":return numeric_match(trigger,state)
    return bool(state and state["state"]==trigger.get("to"))


class AutomationRuntime:
    def __init__(self,engine,resolve_actor,*,create_task=asyncio.create_task):
        self.engine=engine;self.resolve_actor=resolve_actor;self.create_task=create_task
        self.monotonic=getattr(engine.adapter,"monotonic",time.monotonic)
        self.pending={};self.tasks={};self.current={};self.executions=OrderedDict();self.index={};self.signatures={};self.sun_due={};self.last_minute=None;self.closed=False
        engine.runtime=self;self.reconcile()

    def record(self,rule_id):return next((r for r in self.engine.rule_records() if r["rule"]["id"]==rule_id),None)

    def blocked(self,rule):
        engine=self.engine
        if self.closed or not engine.controls or not rule["enabled"]:return True
        room_ids={r["id"] for r in engine.document["layout"]["rooms"]}
        if rule["room_id"] and rule["room_id"] not in room_ids:return True
        pauses=engine.active_room_pauses()
        if rule["room_id"] in pauses:return True
        targets={n["entity_id"] for n in services(rule["actions"])}
        for room in engine.document["layout"]["rooms"]:
            if room["id"] in pauses and targets.intersection(room["entities"]):return True
        # A scene can affect entities beyond its visible target. Be conservative during a hold.
        if pauses and any(i.startswith("scene.") for i in targets):return True
        if not references(rule)<=engine.managed():return True
        for mode in rule["pause_modes"]:
            state=engine.adapter.state(mode)
            if not state or state["state"]!="off":return True
        return False

    def reconcile(self):
        if self.closed:return
        signatures={r["rule"]["id"]:fingerprint(r) for r in self.engine.rule_records()}
        changed={key for key in set(signatures)|set(self.signatures) if signatures.get(key)!=self.signatures.get(key)}
        for key in list(self.pending):
            record=self.record(key[0])
            if key[0] in changed or not record or self.blocked(record["rule"]):self.pending.pop(key,None)
        for rule_id,execution_id in list(self.current.items()):
            record=self.record(rule_id)
            if rule_id in changed or not record or self.blocked(record["rule"]):self.cancel(rule_id)
        self.index={}
        for record in self.engine.rule_records():
            rule=record["rule"]
            if self.blocked(rule):continue
            for entity_id in references(rule):self.index.setdefault(entity_id,set()).add(rule["id"])
            for trigger in rule["triggers"]:
                key=(rule["id"],trigger["id"])
                if trigger["kind"]=="sun" and (key not in self.sun_due or rule["id"] in changed):self.refresh_sun(key,trigger)
        self.sun_due={k:v for k,v in self.sun_due.items() if k[0] in signatures and not self.blocked(self.record(k[0])["rule"])}
        self.signatures=signatures

    def refresh_sun(self,key,trigger):
        provider=getattr(self.engine.adapter,"next_sun",None)
        try:self.sun_due[key]=provider(trigger["event"],trigger["offset_minutes"]) if provider else None
        except Exception:self.sun_due[key]=None

    def cancel(self,rule_id):
        execution_id=self.current.pop(rule_id,None)
        if execution_id and (task:=self.tasks.get(execution_id)):task.cancel()
        for key in list(self.pending):
            if key[0]==rule_id:self.pending.pop(key,None)

    def state_changed(self,entity_id,old,new):
        if self.closed:return
        # An unknown or unavailable sensor invalidates any pending vacancy confirmation.
        for key,pending in list(self.pending.items()):
            if pending["trigger"]["entity_id"]==entity_id and not trigger_matches(pending["trigger"],new):self.pending.pop(key,None)
        for rule_id in list(self.index.get(entity_id,())):
            record=self.record(rule_id)
            if not record:continue
            rule=record["rule"]
            if self.blocked(rule):self.cancel(rule_id);continue
            for trigger in rule["triggers"]:
                if trigger.get("entity_id")!=entity_id:continue
                if trigger["kind"]=="state":cross=bool(old and new and old["state"]==trigger["from"] and new["state"]==trigger["to"])
                elif trigger["kind"]=="numeric":
                    try:known=bool(old and old["state"] not in {"unknown","unavailable"} and math.isfinite(float(old["state"])))
                    except (TypeError,ValueError):known=False
                    cross=known and not numeric_match(trigger,old) and numeric_match(trigger,new)
                else:continue
                if not cross:continue
                delay=trigger.get("for_seconds",0)
                if delay:self.pending[(rule_id,trigger["id"]) ]={"deadline":self.monotonic()+delay,"trigger":deepcopy(trigger),"signature":fingerprint(record)}
                else:self.queue(record,trigger["id"])

    def tick(self,local):
        if self.closed:return
        self.reconcile()
        for key,pending in list(self.pending.items()):
            record=self.record(key[0])
            if not record or self.blocked(record["rule"]) or fingerprint(record)!=pending["signature"]:self.pending.pop(key,None);continue
            if not trigger_matches(pending["trigger"],self.engine.adapter.state(pending["trigger"]["entity_id"])):self.pending.pop(key,None);continue
            if self.monotonic()>=pending["deadline"]:
                self.pending.pop(key,None);self.queue(record,key[1])
        minute=local.strftime("%Y-%m-%dT%H:%M")
        if self.last_minute is None:self.last_minute=minute
        elif minute!=self.last_minute:
            self.last_minute=minute
            for record in self.engine.rule_records():
                if self.blocked(record["rule"]):continue
                for trigger in record["rule"]["triggers"]:
                    if trigger["kind"]=="time" and local.weekday() in trigger["days"] and local.strftime("%H:%M")==trigger["at"]:self.queue(record,trigger["id"],reservation=minute)
        for key,due in list(self.sun_due.items()):
            if due is not None and self.engine.adapter.now()>=due:
                record=self.record(key[0])
                if not record:continue
                trigger=next(t for t in record["rule"]["triggers"] if t["id"]==key[1]);self.refresh_sun(key,trigger)
                self.queue(record,key[1],reservation=local.strftime("%Y-%m-%d")+":"+trigger["event"])

    def queue(self,record,trigger_id,reservation=None):
        rule=record["rule"]
        if self.blocked(rule):return
        if rule["id"] in self.current:
            if rule["mode"]=="single":return
            self.cancel(rule["id"])
        if len(self.tasks)>=8:
            self.engine.audit(type("Actor",(),{"name":"Home automation"})(),"automation_busy",None,"not_queued");return
        execution_id="run-"+secrets.token_hex(16)
        _,steps=compile_script(rule)
        self.executions[execution_id]={"rule_id":rule["id"],"name":rule["name"],"signature":fingerprint(record),"owner_id":record["owner_id"],"rule":deepcopy(rule),"trigger_id":trigger_id,"steps":steps,"counter":0,"started":self.engine.adapter.now(),"status":"starting","trace":[]}
        self.current[rule["id"]]=execution_id
        self.tasks[execution_id]=self.create_task(self.run(execution_id,reservation))
        while len(self.executions)>100:
            removable=next((k for k in self.executions if k not in self.tasks),None)
            if removable is None:break
            self.executions.pop(removable,None)

    def check(self,execution_id):
        execution=self.executions.get(execution_id)
        if not execution:fail("execution_stopped","This automation run no longer exists.")
        record=self.record(execution["rule_id"])
        if not record or fingerprint(record)!=execution["signature"] or self.current.get(execution["rule_id"])!=execution_id or self.blocked(record["rule"]):fail("execution_stopped","This automation was paused, changed or removed.")
        return execution

    def trace(self,execution,kind,**values):
        if len(execution["trace"])<256:execution["trace"].append({"time":self.engine.adapter.now(),"kind":kind,**values})

    async def run(self,execution_id,reservation):
        execution=self.executions[execution_id]
        try:
            self.check(execution_id);actor=await self.resolve_actor(execution["owner_id"]);self.engine.admin(actor);self.check(execution_id)
            for entity_id in references(execution["rule"]):self.engine.entity(actor,entity_id)
            clock=getattr(self.engine.adapter,"local_clock",lambda:"12:00")()
            if evaluate(execution["rule"]["condition"],self.engine.adapter.state,execution["trigger_id"],clock) is not True:
                execution["status"]="conditions_not_met";return
            if reservation:
                async with self.engine.edit_lock:
                    self.check(execution_id);key=execution["rule_id"]+":"+execution["trigger_id"]
                    if self.engine.document.get("automation_runs",{}).get(key)==reservation:execution["status"]="already_ran";return
                    candidate=deepcopy(self.engine.document);candidate.setdefault("automation_runs",{})[key]=reservation;await self.engine.adapter.save(candidate);self.engine.document=candidate
            execution["status"]="running";self.trace(execution,"started",trigger_id=execution["trigger_id"])
            result=await asyncio.wait_for(self.engine.adapter.run_native(execution["rule"],execution["trigger_id"],execution_id),3600)
            execution["status"]="completed" if result is not False else "stopped"
        except asyncio.CancelledError:execution["status"]="cancelled";self.trace(execution,"cancelled");raise
        except asyncio.TimeoutError:execution["status"]="run_limit_reached";self.trace(execution,"run_limit_reached")
        except Exception:execution["status"]="needs_attention";self.trace(execution,"needs_attention")
        finally:
            if self.current.get(execution["rule_id"])==execution_id:self.current.pop(execution["rule_id"],None)
            self.tasks.pop(execution_id,None)
            self.trace(execution,"finished",status=execution["status"])

    async def execute_step(self,execution_id,step_id,user_id):
        execution=self.check(execution_id)
        if user_id!=execution["owner_id"]:fail("not_allowed","This execution belongs to another account.")
        actor=await self.resolve_actor(user_id);self.engine.admin(actor);self.check(execution_id)
        for entity_id in references(execution["rule"]):self.engine.entity(actor,entity_id)
        node=execution["steps"].get(step_id)
        if not node:fail("not_allowed","This step is not part of the approved automation.")
        execution["counter"]+=1
        if execution["counter"]>1200:fail("run_limit_reached","This automation exceeded its step limit.")
        if node["kind"]!="service":self.trace(execution,node["kind"],step=step_id);return
        # The action itself comes from the approved record, never from the private service caller.
        result=await self.engine.command(actor,{"request_id":execution_id+"-"+str(execution["counter"]),"expires_at":self.engine.adapter.now()+15,"entity_id":node["entity_id"],"action":node["action"],"data":node["data"]})
        self.trace(execution,"action",entity_id=node["entity_id"],action=node["action"],status=result["status"])
        if result["status"]!="accepted":fail("action_needs_attention","An action needs checking. Future steps were stopped.")

    def public_traces(self,actor):
        self.engine.admin(actor)
        return [{"id":hashlib.sha256(key.encode()).hexdigest()[:16],"rule_id":v["rule_id"],"name":v["name"],"started":v["started"],"status":v["status"],"trace":deepcopy(v["trace"])} for key,v in reversed(self.executions.items())]

    async def close(self):
        self.closed=True;self.pending.clear()
        tasks=list(self.tasks.values())
        for task in tasks:task.cancel()
        if tasks:await asyncio.gather(*tasks,return_exceptions=True)
