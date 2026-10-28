"""Persistence and deliberate approval for visual automations and room holds."""
from copy import deepcopy
import hashlib
import secrets


class RuleStore:
    def notify_change(self):
        runtime=getattr(self,"runtime",None)
        if runtime:runtime.reconcile()

    def rule_records(self):return self.document.get("automations",[])

    def automation_rules(self,actor):
        from .rules import references
        visible=self.visible(actor);items=[]
        for record in self.rule_records():
            if not references(record["rule"])<=visible:continue
            item=deepcopy(record["rule"])
            if record.get("origin"):item["origin"]={k:v for k,v in record["origin"].items() if k in {"template_id","template_version","customized"}}
            items.append(item)
        return items

    def automation_conflicts(self,rule):
        from .rules import services
        targets={s["entity_id"] for s in services(rule["actions"])};items=[]
        for record in self.rule_records():
            other=record["rule"]
            if not other["enabled"] or other["id"]==rule["id"]:continue
            overlap=targets & {s["entity_id"] for s in services(other["actions"])}
            if overlap:items.append({"id":other["id"],"name":other["name"],"entities":sorted(overlap),"kind":"possible_overlap"})
        for routine in self.document.get("routines",[]):
            overlap=targets & {a["entity_id"] for a in routine["actions"]}
            if routine["enabled"] and overlap:items.append({"id":routine["id"],"name":routine["name"],"entities":sorted(overlap),"kind":"scheduled_overlap"})
        return items

    async def preview_automation(self,actor,value,revision,*,template_id=None,inputs=None):
        from .engine import fail
        from .rules import RuleValidator,simulate
        from .rule_templates import prepare
        self.admin(actor)
        if type(revision) is not int or revision!=self.document["revision"]:fail("revision_conflict","The home changed. Refresh before reviewing an automation.")
        if template_id is not None:rule,origin=prepare(self,actor,template_id,inputs)
        else:
            rule=RuleValidator(self,actor).rule(value)
            previous=next((r for r in self.rule_records() if r["rule"]["id"]==rule["id"]),None)
            origin={**deepcopy(previous.get("origin") or {}),"customized":True} if previous else None
        rule["enabled"]=False
        validator=getattr(self.adapter,"validate_native",None)
        if validator:await validator(rule)
        now=self.adapter.now()
        for key in list(self.approvals):
            if self.approvals[key]["expires_at"]<now:self.approvals.pop(key)
        if len(self.approvals)>=128:fail("busy","Too many reviews are open. Finish a review before starting another.")
        nonce=secrets.token_urlsafe(24);key=hashlib.sha256(nonce.encode()).hexdigest();conflicts=self.automation_conflicts(rule)
        self.approvals[key]={"kind":"automation","actor_id":actor.id,"rule":rule,"origin":origin,"revision":revision,"expires_at":now+300,"conflicts":conflicts,"custom":template_id is None}
        clock=getattr(self.adapter,"local_clock",lambda:"12:00")()
        traces={t["id"]:simulate(rule,self.adapter.state,t["id"],clock) for t in rule["triggers"]}
        return {"approval_nonce":nonce,"expires_at":now+300,"rule":deepcopy(rule),"origin":origin,"conflicts":conflicts,"simulation":traces,"shared_home_ack_required":template_id is None,"writes":False,"executes_devices":False,"conflict_scope":"VAutomate-managed rules and schedules; external automations are not included."}

    async def approve_automation(self,actor,nonce,*,enabled=False,shared_home_ack=False,conflicts_ack=False):
        from .engine import fail
        from .rules import RuleValidator
        self.admin(actor)
        if not isinstance(nonce,str) or not 20<=len(nonce)<=100 or type(enabled) is not bool:fail("invalid_input","Review the automation before approving it.")
        key=hashlib.sha256(nonce.encode()).hexdigest()
        async with self.edit_lock:
            receipt=next((r for r in self.rule_records() if r.get("approved_by")==actor.id and key in r.get("approval_keys",[])),None)
            if receipt:return {"revision":self.document["revision"],"rule_id":receipt["rule"]["id"],"created":False,"enabled":receipt["rule"]["enabled"]}
            approval=self.approvals.get(key)
            if not approval or approval.get("kind")!="automation" or approval["actor_id"]!=actor.id:fail("approval_required","Review this automation on your own account first.")
            if approval["expires_at"]<self.adapter.now():fail("approval_expired","This review expired. Review the current devices again.")
            if approval["revision"]!=self.document["revision"]:fail("revision_conflict","The home changed after this review. Please review again.")
            if approval["custom"] and shared_home_ack is not True:fail("shared_home_ack_required","Consider the effect on everyone at home before approving a custom automation.")
            if approval["conflicts"] and conflicts_ack is not True:fail("conflict_review_required","Review the other automations controlling these devices before enabling or saving.")
            if enabled and not self.controls:fail("read_only","Create this automation paused while the home is in read-only evaluation.")
            rule=RuleValidator(self,actor).rule(approval["rule"]);rule["enabled"]=enabled
            validator=getattr(self.adapter,"validate_native",None)
            if validator:await validator(rule)
            previous=next((r for r in self.rule_records() if r["rule"]["id"]==rule["id"]),None)
            record={"rule":rule,"owner_id":actor.id,"approved_by":actor.id,"approved_at":self.adapter.now(),"origin":deepcopy(approval["origin"]),"approval_keys":((previous or {}).get("approval_keys",[])+[key])[-8:]}
            candidate=deepcopy(self.document);items=[r for r in candidate.get("automations",[]) if r["rule"]["id"]!=rule["id"]]
            if len(items)>=100:fail("invalid_input","This home already has 100 visual automations.")
            candidate.update(revision=candidate["revision"]+1,automations=items+[record]);await self.adapter.save(candidate);self.document=candidate;self.approvals.pop(key,None);self.notify_change()
        self.audit(actor,"automation_approved",None,"created_enabled" if enabled else "created_paused")
        return {"revision":self.document["revision"],"rule_id":rule["id"],"created":previous is None,"enabled":enabled}

    async def remove_automation(self,actor,rule_id,revision):
        from .engine import fail
        self.admin(actor)
        async with self.edit_lock:
            if type(revision) is not int or revision!=self.document["revision"]:fail("revision_conflict","Refresh the home before removing an automation.")
            records=self.rule_records()
            if not any(r["rule"]["id"]==rule_id for r in records):fail("not_found","This automation was already removed.")
            candidate=deepcopy(self.document);candidate.update(revision=candidate["revision"]+1,automations=[r for r in records if r["rule"]["id"]!=rule_id]);await self.adapter.save(candidate);self.document=candidate;self.notify_change()
        self.audit(actor,"automation_removed",None,"removed")
        return {"revision":self.document["revision"]}

    async def pause_automation(self,actor,rule_id,revision):
        from .engine import fail
        self.admin(actor)
        async with self.edit_lock:
            if type(revision) is not int or revision!=self.document["revision"]:fail("revision_conflict","Refresh before pausing this automation.")
            candidate=deepcopy(self.document);record=next((r for r in candidate.get("automations",[]) if r["rule"]["id"]==rule_id),None)
            if not record:fail("not_found","This automation no longer exists.")
            record["rule"]["enabled"]=False;candidate["revision"]+=1;await self.adapter.save(candidate);self.document=candidate;self.notify_change()
        self.audit(actor,"automation_paused",None,"paused")
        return {"revision":self.document["revision"]}

    def active_room_pauses(self,actor=None):
        rooms={r["id"] for r in (self.layout(actor) if actor else self.document["layout"])["rooms"]};now=self.adapter.now()
        return {key:{"until":value["until"],"by":value.get("by","Home member")} for key,value in self.document.get("room_pauses",{}).items() if key in rooms and value["until"]>now}

    def actions_held(self,actions):
        pauses=self.active_room_pauses();targets={a["entity_id"] for a in actions}
        if pauses and any(i.startswith("scene.") for i in targets):return True
        return any(r["id"] in pauses and targets.intersection(r["entities"]) for r in self.document["layout"]["rooms"])

    async def set_room_pause(self,actor,room_id,seconds):
        from .engine import fail
        from .rules import ACTION_DOMAINS
        room=next((r for r in self.document["layout"]["rooms"] if r["id"]==room_id),None)
        if not room or type(seconds) is not int or seconds not in {0,900,1800,3600,14400}:fail("invalid_input","Choose a room and a hold of 15 minutes to four hours.")
        targets=[i for i in room["entities"] if i.split(".")[0] in ACTION_DOMAINS]
        if not targets or any(not actor.read(i) or not actor.control(i) for i in targets):fail("not_allowed","This account cannot pause this room's controls.")
        async with self.edit_lock:
            candidate=deepcopy(self.document);pauses=self.active_room_pauses()
            if seconds:pauses[room_id]={"until":self.adapter.now()+seconds,"by":actor.name}
            else:pauses.pop(room_id,None)
            candidate.update(revision=candidate["revision"]+1,room_pauses=pauses);await self.adapter.save(candidate);self.document=candidate;self.notify_change()
        self.audit(actor,"room_automation_hold" if seconds else "room_automation_resume",None,"saved")
        return {"revision":self.document["revision"],"room_pauses":self.active_room_pauses(actor)}
