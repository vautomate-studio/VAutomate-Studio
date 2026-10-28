"""Bounded visual automation contract and compiler. No user code or YAML execution."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import re

from .engine import KEY, ProductError, fail, number, text

ACTION_DOMAINS={"light","cover","switch","fan","climate","media_player","scene","input_boolean"}
NUMERIC_ATTRIBUTES={"temperature","current_temperature","humidity","volume_level","percentage","brightness","current_position","battery_level"}


def exact(value,required,optional=()):
    if not isinstance(value,dict) or set(value)-set(required)-set(optional) or set(required)-set(value):
        fail("invalid_input","Review the automation's fields.")


def clock_text(value):
    if not isinstance(value,str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",value):fail("invalid_input","Choose a valid time.")
    return value


def fingerprint(rule):
    return hashlib.sha256(json.dumps(rule,sort_keys=True,allow_nan=False).encode()).hexdigest()


def references(value):
    """Only semantic entity fields are references; ordinary labels/source strings are not."""
    found=set()
    def walk(node):
        if isinstance(node,list):
            for child in node:walk(child)
        elif isinstance(node,dict):
            for key,item in node.items():
                if key=="entity_id" and isinstance(item,str):found.add(item)
                elif key=="pause_modes" and isinstance(item,list):found.update(item)
                else:walk(item)
    walk(value)
    return found


def services(actions):
    found=[]
    def walk(nodes):
        for node in nodes:
            kind=node["kind"]
            if kind=="service":found.append(node)
            elif kind=="choose":
                for branch in node["branches"]:walk(branch["actions"])
                walk(node["default"])
            elif kind=="repeat":walk(node["actions"])
            elif kind=="parallel":
                for branch in node["branches"]:walk(branch)
    walk(actions)
    return found


class RuleValidator:
    def __init__(self,engine,actor):self.engine=engine;self.actor=actor;self.nodes=0;self.trigger_ids=set()
    def count(self,depth):
        self.nodes+=1
        if self.nodes>120 or depth>6:fail("too_complex","Use at most 120 blocks and six levels of nesting.")
    def entity(self,entity_id,control=False):return self.engine.entity(self.actor,entity_id,control=control)
    def condition(self,value,depth=0):
        self.count(depth)
        if not isinstance(value,dict):fail("invalid_input","Choose a condition.")
        kind=value.get("kind")
        if kind in {"all","any"}:
            exact(value,["kind","conditions"]);items=value["conditions"]
            if not isinstance(items,list) or len(items)>12:fail("invalid_input","Use at most twelve conditions in a group.")
            return {"kind":kind,"conditions":[self.condition(c,depth+1) for c in items]}
        if kind=="not":
            exact(value,["kind","condition"]);return {"kind":kind,"condition":self.condition(value["condition"],depth+1)}
        if kind=="trigger":
            exact(value,["kind","ids"]);ids=value["ids"]
            if not isinstance(ids,list) or not ids or any(not isinstance(i,str) or i not in self.trigger_ids for i in ids):fail("invalid_input","Choose an existing trigger for this branch.")
            return {"kind":kind,"ids":list(dict.fromkeys(ids))}
        if kind=="time":
            exact(value,["kind","after","before"]);return {"kind":kind,"after":clock_text(value["after"]),"before":clock_text(value["before"])}
        if kind=="state":
            exact(value,["kind","entity_id","state"]);self.entity(value["entity_id"]);state=text(value["state"],60)
            if state in {"unknown","unavailable"}:fail("invalid_input","Unknown readings cannot be used as a comfort-control condition.")
            return {"kind":kind,"entity_id":value["entity_id"],"state":state}
        if kind=="numeric":
            exact(value,["kind","entity_id"],["above","below","attribute"]);self.entity(value["entity_id"])
            if "above" not in value and "below" not in value:fail("invalid_input","Choose a numeric threshold.")
            clean={"kind":kind,"entity_id":value["entity_id"]}
            for key in ["above","below"]:
                if key in value:clean[key]=number(value[key],-1e9,1e9)
            if "above" in clean and "below" in clean and clean["above"]>=clean["below"]:fail("invalid_input","The upper threshold must exceed the lower one.")
            if "attribute" in value:
                if value["attribute"] not in NUMERIC_ATTRIBUTES:fail("not_supported","Choose a supported numeric reading.")
                clean["attribute"]=value["attribute"]
            return clean
        fail("not_supported","This condition type is not supported.")
    def trigger(self,value):
        exact(value,["id","kind"],["entity_id","from","to","for_seconds","above","below","at","days","event","offset_minutes"])
        identifier=value["id"]
        if not isinstance(identifier,str) or not KEY.fullmatch(identifier) or identifier in self.trigger_ids:fail("invalid_input","Each trigger needs a unique identity.")
        self.trigger_ids.add(identifier);kind=value["kind"];clean={"id":identifier,"kind":kind}
        if kind in {"state","numeric"}:
            if set(value)-({"id","kind","entity_id","for_seconds","from","to"} if kind=="state" else {"id","kind","entity_id","for_seconds","above","below"}):fail("invalid_input","Review this trigger.")
            self.entity(value.get("entity_id"));clean["entity_id"]=value["entity_id"]
            seconds=value.get("for_seconds",0)
            if type(seconds) is not int or not 0<=seconds<=3600:fail("invalid_input","Choose a confirmation delay up to one hour.")
            clean["for_seconds"]=seconds
            if kind=="state":
                before=text(value.get("from"),60);after=text(value.get("to"),60)
                if before==after or before in {"unknown","unavailable"} or after in {"unknown","unavailable"}:fail("invalid_input","Choose a real change between known states.")
                clean.update({"from":before,"to":after})
            else:
                numeric=self.condition({k:v for k,v in {**value,"kind":"numeric"}.items() if k in {"kind","entity_id","above","below"}})
                clean.update({k:v for k,v in numeric.items() if k in {"above","below"}})
        elif kind=="time":
            exact(value,["id","kind","at","days"]);days=value["days"]
            if not isinstance(days,list) or not days or any(type(d) is not int or d<0 or d>6 for d in days):fail("invalid_input","Choose the days for this trigger.")
            clean.update(at=clock_text(value["at"]),days=sorted(set(days)))
        elif kind=="sun":
            exact(value,["id","kind","event"],["offset_minutes"])
            if value["event"] not in {"sunrise","sunset"}:fail("invalid_input","Choose sunrise or sunset.")
            offset=value.get("offset_minutes",0)
            if type(offset) is not int or not -120<=offset<=120:fail("invalid_input","Use a sun offset within two hours.")
            clean.update(event=value["event"],offset_minutes=offset)
        else:fail("not_supported","This trigger is not supported in the visual editor.")
        return clean
    def sequence(self,value,depth=0):
        if not isinstance(value,list) or len(value)>40:fail("invalid_input","Use at most forty steps in a sequence.")
        clean=[]
        for node in value:
            self.count(depth)
            if not isinstance(node,dict):fail("invalid_input","Choose an action block.")
            kind=node.get("kind")
            if kind=="service":
                exact(node,["kind","entity_id","action","data"])
                if not isinstance(node["entity_id"],str) or node["entity_id"].split(".")[0] not in ACTION_DOMAINS:fail("not_supported","This automation cannot control security, updates or arbitrary backend actions.")
                self.engine.validate_operation(self.actor,node["entity_id"],node["action"],node["data"]);clean.append(deepcopy(node))
            elif kind=="delay":
                exact(node,["kind","seconds"]);seconds=number(node["seconds"],0,3600);clean.append({"kind":kind,"seconds":seconds})
            elif kind=="condition":
                exact(node,["kind","condition"]);clean.append({"kind":kind,"condition":self.condition(node["condition"],depth+1)})
            elif kind=="wait":
                exact(node,["kind","condition","timeout_seconds"]);timeout=number(node["timeout_seconds"],1,3600)
                clean.append({"kind":kind,"condition":self.condition(node["condition"],depth+1),"timeout_seconds":timeout})
            elif kind=="repeat":
                exact(node,["kind","count","actions"])
                if type(node["count"]) is not int or not 1<=node["count"]<=20:fail("invalid_input","Repeat between one and twenty times.")
                clean.append({"kind":kind,"count":node["count"],"actions":self.sequence(node["actions"],depth+1)})
            elif kind=="choose":
                exact(node,["kind","branches","default"])
                if not isinstance(node["branches"],list) or not 1<=len(node["branches"])<=8:fail("invalid_input","Choose between one and eight branches.")
                branches=[]
                for branch in node["branches"]:
                    exact(branch,["condition","actions"]);branches.append({"condition":self.condition(branch["condition"],depth+1),"actions":self.sequence(branch["actions"],depth+1)})
                clean.append({"kind":kind,"branches":branches,"default":self.sequence(node["default"],depth+1)})
            elif kind=="parallel":
                exact(node,["kind","branches"])
                if not isinstance(node["branches"],list) or not 2<=len(node["branches"])<=4:fail("invalid_input","Use two to four parallel branches.")
                clean.append({"kind":kind,"branches":[self.sequence(b,depth+1) for b in node["branches"]]})
            else:fail("not_supported","This action block is not supported.")
        return clean
    def rule(self,value):
        self.engine.admin(self.actor)
        exact(value,["id","name","enabled","mode","room_id","triggers","condition","actions","pause_modes"])
        if not isinstance(value["id"],str) or not KEY.fullmatch(value["id"]):fail("invalid_input","This automation needs an identity.")
        if type(value["enabled"]) is not bool or value["mode"] not in {"single","restart"}:fail("invalid_input","Review the automation's run mode.")
        rooms={r["id"] for r in self.engine.document["layout"]["rooms"]}
        if value["room_id"] is not None and value["room_id"] not in rooms:fail("invalid_input","Choose an existing room.")
        raw=value["triggers"]
        if not isinstance(raw,list) or not 1<=len(raw)<=10:fail("invalid_input","Choose one to ten triggers.")
        triggers=[self.trigger(t) for t in raw]
        modes=value["pause_modes"]
        if not isinstance(modes,list) or len(modes)>8 or any(not isinstance(i,str) for i in modes) or len(set(modes))!=len(modes):fail("invalid_input","Choose up to eight pause helpers.")
        for entity_id in modes:
            self.entity(entity_id)
            if not entity_id.startswith("input_boolean."):fail("invalid_input","Pause modes must be on/off helpers.")
        clean={"id":value["id"],"name":text(value["name"]),"enabled":value["enabled"],"mode":value["mode"],"room_id":value["room_id"],"triggers":triggers,"condition":self.condition(value["condition"]),"actions":self.sequence(value["actions"]),"pause_modes":list(modes)}
        if not services(clean["actions"]):fail("invalid_input","Add at least one device action.")
        cost,duration=sequence_cost(clean["actions"])
        if cost>200 or duration>3600:fail("too_complex","Limit a run to 200 expanded actions and one hour of waits/delays.")
        return clean


def sequence_cost(nodes):
    count=0;duration=0
    for node in nodes:
        kind=node["kind"]
        if kind=="service":count+=1
        elif kind=="delay":duration+=node["seconds"]
        elif kind=="wait":duration+=node["timeout_seconds"]
        elif kind=="repeat":
            n,d=sequence_cost(node["actions"]);count+=n*node["count"];duration+=d*node["count"]
        elif kind=="choose":
            costs=[sequence_cost(b["actions"]) for b in node["branches"]]+[sequence_cost(node["default"])];count+=max(c[0] for c in costs);duration+=max(c[1] for c in costs)
        elif kind=="parallel":
            costs=[sequence_cost(b) for b in node["branches"]];count+=sum(c[0] for c in costs);duration+=max(c[1] for c in costs)
    return count,duration


def evaluate(node,state,trigger_id="",clock="00:00"):
    """Three-valued conditions: Unknown never becomes True merely through NOT."""
    kind=node["kind"]
    if kind in {"all","any"}:
        values=[evaluate(c,state,trigger_id,clock) for c in node["conditions"]]
        if kind=="all":return False if False in values else None if None in values else True
        return True if True in values else None if None in values else False
    if kind=="not":
        if not dependencies_known(node["condition"],state):return None
        value=evaluate(node["condition"],state,trigger_id,clock);return None if value is None else not value
    if kind=="trigger":return trigger_id in node["ids"]
    if kind=="time":return node["after"]<=clock<node["before"] if node["after"]<node["before"] else clock>=node["after"] or clock<node["before"]
    item=state(node["entity_id"])
    if not item or item["state"] in {"unknown","unavailable"}:return None
    if kind=="state":return item["state"]==node["state"]
    raw=item.get("attributes",{}).get(node["attribute"]) if "attribute" in node else item["state"]
    try:
        if isinstance(raw,bool):return None
        number_value=float(raw)
        if not math.isfinite(number_value):return None
    except (TypeError,ValueError):return None
    return ("above" not in node or number_value>node["above"]) and ("below" not in node or number_value<node["below"])


def dependencies_known(node,state):
    if node["kind"] in {"state","numeric"}:return evaluate(node,state) is not None
    if node["kind"] in {"all","any"}:return all(dependencies_known(c,state) for c in node["conditions"])
    if node["kind"]=="not":return dependencies_known(node["condition"],state)
    return True


def known_expression(node):
    kind=node["kind"];q=lambda v:json.dumps(v,ensure_ascii=True)
    if kind in {"all","any"}:return "("+" and ".join(known_expression(c) for c in node["conditions"])+")" if node["conditions"] else "true"
    if kind=="not":return known_expression(node["condition"])
    if kind in {"state","numeric"}:
        entity=q(node["entity_id"]);raw=f"state_attr({entity}, {q(node['attribute'])})" if "attribute" in node else f"states({entity})"
        return f"(has_value({entity}) and is_number({raw}) and {raw} is not boolean)" if kind=="numeric" else f"has_value({entity})"
    return "true"


def condition_expression(node):
    """Only compiler-generated expressions; user text is always JSON escaped."""
    kind=node["kind"];quote=lambda value:json.dumps(value,ensure_ascii=True)
    if kind in {"all","any"}:
        children=[condition_expression(c) for c in node["conditions"]]
        return "("+(" and " if kind=="all" else " or ").join(children)+")" if children else "true" if kind=="all" else "false"
    if kind=="not":
        known=known_expression(node["condition"])
        return f"(({known}) and not ({condition_expression(node['condition'])}))"
    if kind=="trigger":return "(trigger.id in "+quote(node["ids"])+")"
    if kind=="time":
        after=quote(node["after"]);before=quote(node["before"]);current="now().strftime('%H:%M')"
        return f"({after} <= {current} < {before})" if node["after"]<node["before"] else f"({current} >= {after} or {current} < {before})"
    entity_id=quote(node["entity_id"]);known=f"has_value({entity_id})"
    if kind=="state":return f"({known} and is_state({entity_id}, {quote(node['state'])}))"
    raw=f"state_attr({entity_id}, {quote(node['attribute'])})" if "attribute" in node else f"states({entity_id})"
    checks=[known,f"is_number({raw})",f"{raw} is not boolean"]
    for key,op in [("above",">"),("below","<")]:
        if key in node:checks.append(f"({raw} | float) {op} {node[key]}")
    return "("+" and ".join(checks)+")"


def compile_script(rule):
    """Native HA building blocks dispatch only approved steps through a private gate."""
    steps={}
    def compile_nodes(nodes,path="a"):
        result=[]
        for index,node in enumerate(nodes):
            key=f"{path}.{index}";steps[key]=deepcopy(node)
            result.append({"action":"vautomate_studio.execute_step","data":{"execution_id":"{{ studio_execution_id }}","step_id":key}})
            kind=node["kind"]
            if kind=="delay":result.append({"delay":{"seconds":node["seconds"]}})
            elif kind=="wait":result.append({"wait_template":"{{ "+condition_expression(node["condition"])+" }}","timeout":{"seconds":node["timeout_seconds"]},"continue_on_timeout":False})
            elif kind=="condition":result.append({"condition":"template","value_template":"{{ "+condition_expression(node["condition"])+" }}"})
            elif kind=="choose":result.append({"choose":[{"conditions":[{"condition":"template","value_template":"{{ "+condition_expression(b["condition"])+" }}"}],"sequence":compile_nodes(b["actions"],f"{key}.b{n}")} for n,b in enumerate(node["branches"])],"default":compile_nodes(node["default"],key+".default")})
            elif kind=="repeat":result.append({"repeat":{"count":node["count"],"sequence":compile_nodes(node["actions"],key+".repeat")}})
            elif kind=="parallel":result.append({"parallel":[{"sequence":compile_nodes(b,f"{key}.p{n}")} for n,b in enumerate(node["branches"])]})
        return result
    return compile_nodes(rule["actions"]),steps


def simulate(rule,state,trigger_id="",clock="12:00"):
    """A plan, never an execution. Waiting stops the simulation instead of inventing future readings."""
    trace=[]
    if evaluate(rule["condition"],state,trigger_id,clock) is not True:return [{"kind":"condition","result":"not_met_or_unknown"}]
    remaining=250
    def walk(nodes):
        nonlocal remaining
        for node in nodes:
            remaining-=1
            if remaining<0:raise ProductError("too_complex","The simulation reached its step limit.")
            kind=node["kind"]
            if kind=="service":trace.append({"kind":"action","entity_id":node["entity_id"],"action":node["action"],"data":node["data"],"result":"would_request"})
            elif kind=="condition":
                match=evaluate(node["condition"],state,trigger_id,clock) is True;trace.append({"kind":kind,"result":"met" if match else "not_met_or_unknown"})
                if not match:return False
            elif kind=="delay":trace.append({"kind":kind,"seconds":node["seconds"],"result":"would_wait"})
            elif kind=="wait":
                match=evaluate(node["condition"],state,trigger_id,clock) is True;trace.append({"kind":kind,"timeout_seconds":node["timeout_seconds"],"result":"already_met" if match else "awaiting_future_reading"})
                if not match:return False
            elif kind=="repeat":
                for _ in range(node["count"]):
                    if walk(node["actions"]) is False:return False
            elif kind=="choose":
                selected=next((b["actions"] for b in node["branches"] if evaluate(b["condition"],state,trigger_id,clock) is True),node["default"])
                if walk(selected) is False:return False
            elif kind=="parallel":
                trace.append({"kind":kind,"branches":len(node["branches"]),"result":"concurrent_plan"})
                for branch in node["branches"]:walk(branch)
        return True
    walk(rule["actions"])
    return trace
