"""Entity-bound room/comfort recipes. Definitions never create an automation."""
from copy import deepcopy
import secrets
from .engine import fail,number,text
from .rules import RuleValidator


def entity_slot(identifier,label,domain,*,classes=(),multiple=False,action=None,required=True):
    return {"id":identifier,"label":label,"domain":domain,"classes":list(classes),"multiple":multiple,"action":action,"required":required}


OCCUPANCY=entity_slot("sensor","Presence sensor","binary_sensor",classes=["occupancy","presence"])
LIGHTS=entity_slot("lights","Lights to control","light",multiple=True,action="turn_on")
RULE_TEMPLATES=(
 {"id":"room_presence","version":1,"name":"Room entrance & exit","description":"Lights on for presence, off after confirmed vacancy.","requires_room":True,"slots":[OCCUPANCY,LIGHTS],"defaults":{"absence_seconds":120}},
 {"id":"room_exit","version":1,"name":"Room exit lights off","description":"Turn selected lights off after the room becomes vacant.","requires_room":True,"slots":[OCCUPANCY,{**LIGHTS,"action":"turn_off"}],"defaults":{"absence_seconds":180}},
 {"id":"bathroom_presence","version":1,"name":"Bathroom entrance & exit","description":"Presence-based lighting with a longer vacancy delay. Verify shower and stationary-person coverage.","requires_room":True,"requires_coverage_confirmation":True,"slots":[OCCUPANCY,LIGHTS],"defaults":{"absence_seconds":300}},
 {"id":"hallway_motion","version":1,"name":"Hallway motion lighting","description":"Motion lighting with a no-motion delay. This is not proof that a stationary person has left.","requires_room":True,"slots":[entity_slot("sensor","Motion sensor","binary_sensor",classes=["motion"]),LIGHTS],"defaults":{"absence_seconds":120}},
 {"id":"bathroom_fan","version":1,"name":"Bathroom ventilation","description":"Start fans above the high humidity level; stop after sustained lower humidity.","requires_room":True,"slots":[entity_slot("sensor","Humidity sensor","sensor",classes=["humidity"]),entity_slot("fans","Fans","fan",multiple=True,action="turn_on")],"defaults":{"humidity_high":65,"humidity_low":55,"dry_seconds":600}},
 {"id":"sunset_curtains","version":1,"name":"Sunset curtains","description":"Close selected curtains at sunset, respecting pause modes and room holds.","requires_room":True,"slots":[entity_slot("curtains","Curtains to close","cover",multiple=True,action="close_cover")],"defaults":{"offset_minutes":0}},
 {"id":"mode_scenes","version":1,"name":"Dawat, Cinema & home modes","description":"Apply your selected scene when a home mode changes. Choose an optional scene for leaving the mode.","requires_room":False,"slots":[entity_slot("mode","Home mode helper","input_boolean"),entity_slot("on_scene","Scene when mode turns on","scene",action="turn_on"),entity_slot("off_scene","Scene when mode turns off · optional","scene",action="turn_on",required=False)],"defaults":{}},
)


def library():return deepcopy(list(RULE_TEMPLATES))


def prepare(engine,actor,template_id,inputs):
    engine.admin(actor)
    template=next((t for t in RULE_TEMPLATES if t["id"]==template_id),None)
    if not template:fail("not_supported","Choose an available automation template.")
    optional=set(template["defaults"])
    if template.get("requires_coverage_confirmation"):optional.add("coverage_confirmed")
    if not isinstance(inputs,dict) or set(inputs)-{"name","room_id","targets","pause_modes"}-optional:fail("invalid_input","Review the template's choices.")
    targets=inputs.get("targets")
    if not isinstance(targets,dict) or set(targets)-{s["id"] for s in template["slots"]}:fail("invalid_input","Choose the required devices.")
    room_id=inputs.get("room_id")
    room=next((r for r in engine.document["layout"]["rooms"] if r["id"]==room_id),None)
    if template["requires_room"] and not room:fail("invalid_input","Choose the room for this automation.")
    if not template["requires_room"] and room_id is not None:fail("invalid_input","This home-mode recipe uses a whole-home scope.")
    selected={}
    for slot in template["slots"]:
        value=targets.get(slot["id"],[] if slot["multiple"] else "")
        ids=value if slot["multiple"] else [value] if value else []
        if not isinstance(ids,list) or len(ids)>20 or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids) or slot["required"] and not ids:fail("invalid_input","Review: "+slot["label"])
        for entity_id in ids:
            state=engine.entity(actor,entity_id,control=bool(slot["action"]))
            if entity_id.split(".")[0]!=slot["domain"] or slot["classes"] and state.get("attributes",{}).get("device_class") not in slot["classes"]:fail("invalid_input","Choose a compatible device for "+slot["label"])
            if room and entity_id not in room["entities"]:fail("invalid_input","Select devices already added to this room.")
        selected[slot["id"]]=ids
    if template.get("requires_coverage_confirmation") and inputs.get("coverage_confirmed") is not True:fail("coverage_required","Verify that the bathroom sensor detects a stationary person in the occupied areas before approving.")
    rule={"id":"rule-"+secrets.token_hex(12),"name":text(inputs.get("name",template["name"])),"enabled":False,"mode":"restart","room_id":room_id,"triggers":[],"condition":{"kind":"all","conditions":[]},"actions":[],"pause_modes":inputs.get("pause_modes",[])}
    def service(ids,action):return [{"kind":"service","entity_id":i,"action":action,"data":{}} for i in ids]
    def branch(trigger,actions):return {"condition":{"kind":"trigger","ids":[trigger]},"actions":actions}
    def choose(branches):return [{"kind":"choose","branches":branches,"default":[]}]
    if template_id in {"room_presence","room_exit","bathroom_presence","hallway_motion"}:
        delay=inputs.get("absence_seconds",template["defaults"]["absence_seconds"])
        if type(delay) is not int or not 30<=delay<=3600:fail("invalid_input","Use a vacancy delay between 30 seconds and one hour.")
        sensor=selected["sensor"][0]
        if template_id!="room_exit":rule["triggers"].append({"id":"entered","kind":"state","entity_id":sensor,"from":"off","to":"on","for_seconds":0})
        rule["triggers"].append({"id":"vacant","kind":"state","entity_id":sensor,"from":"on","to":"off","for_seconds":delay})
        branches=[]
        if template_id!="room_exit":branches.append(branch("entered",service(selected["lights"],"turn_on")))
        branches.append(branch("vacant",service(selected["lights"],"turn_off")));rule["actions"]=choose(branches)
    elif template_id=="bathroom_fan":
        high=number(inputs.get("humidity_high",65),20,100);low=number(inputs.get("humidity_low",55),10,95);delay=inputs.get("dry_seconds",600)
        if high<=low or type(delay) is not int or not 60<=delay<=3600:fail("invalid_input","Use a higher start humidity than stop humidity, and a dry-out delay of one to sixty minutes.")
        sensor=selected["sensor"][0]
        rule["triggers"]=[{"id":"humid","kind":"numeric","entity_id":sensor,"above":high,"for_seconds":0},{"id":"dry","kind":"numeric","entity_id":sensor,"below":low,"for_seconds":delay}]
        rule["actions"]=choose([branch("humid",service(selected["fans"],"turn_on")),branch("dry",service(selected["fans"],"turn_off"))])
    elif template_id=="sunset_curtains":
        offset=inputs.get("offset_minutes",0)
        rule["triggers"]=[{"id":"sunset","kind":"sun","event":"sunset","offset_minutes":offset}];rule["actions"]=service(selected["curtains"],"close_cover")
    elif template_id=="mode_scenes":
        mode=selected["mode"][0]
        if mode in rule["pause_modes"]:fail("invalid_input","A mode cannot pause the automation that responds to its own switch.")
        rule["triggers"]=[{"id":"mode_on","kind":"state","entity_id":mode,"from":"off","to":"on","for_seconds":0},{"id":"mode_off","kind":"state","entity_id":mode,"from":"on","to":"off","for_seconds":0}]
        rule["actions"]=choose([branch("mode_on",service(selected["on_scene"],"turn_on")),branch("mode_off",service(selected["off_scene"],"turn_on"))])
    return RuleValidator(engine,actor).rule(rule),{"template_id":template["id"],"template_version":template["version"],"customized":False}
