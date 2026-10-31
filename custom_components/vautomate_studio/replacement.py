"""Reviewed migration of Studio-owned references only; never radio or HA config edits."""
from __future__ import annotations
from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
import secrets

from .engine import ProductError,StudioEngine
from .rules import references,RuleValidator


def remap(value,mapping):
    if isinstance(value,list):return [remap(v,mapping) for v in value]
    if isinstance(value,dict):
        return {k:mapping.get(v,v) if k=='entity_id' and isinstance(v,str) else [mapping.get(i,i) for i in v] if k=='pause_modes' and isinstance(v,list) else remap(v,mapping) for k,v in value.items()}
    return deepcopy(value)


def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()


class Replacement:
    def __init__(self,engine,authorize):self.engine=engine;self.authorize=authorize;self.reviews=OrderedDict()

    async def admin(self,actor):self.engine.admin(actor);await self.authorize(actor.id)

    def binding(self,candidate,pairs):
        fields={'friendly_name','device_class','unit_of_measurement','supported_features','supported_color_modes','min_color_temp_kelvin','max_color_temp_kelvin','min_temp','max_temp','hvac_modes','source_list'}
        identities=sorted({p[k] for p in pairs for k in ['from','to']});devices={}
        for identity in identities:
            state=self.engine.adapter.state(identity)
            devices[identity]=None if state is None else {k:v for k,v in state.get('attributes',{}).items() if k in fields}
        return fingerprint({'document':candidate,'devices':devices})

    async def status(self,actor):
        await self.admin(actor)
        return {'entities':[{'entity_id':i,'name':str((self.engine.adapter.state(i) or {}).get('attributes',{}).get('friendly_name') or i),'missing':self.engine.adapter.state(i) is None} for i in sorted(self.engine.managed())],
                'scope':'VAutomate rooms, Home buttons, schedules and visual automations only. Home Assistant scenes and external automations are not changed.','operates_devices':False}

    def prepare(self,actor,pairs):
        if not isinstance(pairs,list) or not 1<=len(pairs)<=32:raise ProductError('invalid_input','Choose one to 32 device controls to replace.')
        mapping={};targets=set();managed=self.engine.managed()
        for pair in pairs:
            if not isinstance(pair,dict) or set(pair)!={'from','to'} or any(not isinstance(pair[k],str) for k in pair):raise ProductError('invalid_input','Choose an old and a replacement control.')
            old,new=pair['from'],pair['to']
            if old not in managed or old in mapping or new in managed or new in targets or old.split('.')[0]!=new.split('.')[0]:raise ProductError('invalid_input','Use a distinct new control of the same type. Add the replacement through this review before assigning it elsewhere.')
            if not actor.read(old):raise ProductError('not_allowed','This account cannot access the old control.')
            target=self.engine.entity(actor,new,discover=True)
            if target['state'] in {'unavailable','unknown'}:raise ProductError('device_offline','The replacement must be connected before review.')
            source=self.engine.adapter.state(old)
            if source:
                for key in ['device_class','unit_of_measurement']:
                    if source.get('attributes',{}).get(key)!=target.get('attributes',{}).get(key):raise ProductError('incompatible_device','Choose a replacement with the same reading type and unit. Existing thresholds must remain meaningful.')
            mapping[old]=new;targets.add(new)
        candidate=deepcopy(self.engine.document);changes={'rooms':[],'home_buttons':[],'schedules':[],'automations':[]}
        for room in candidate['layout']['rooms']:
            if set(room['entities'])&mapping.keys():
                room['entities']=[mapping.get(i,i) for i in room['entities']];changes['rooms'].append({'id':room['id'],'name':room['name']})
        for item in candidate['layout']['quick_actions']:
            if item['entity_id'] in mapping:item['entity_id']=mapping[item['entity_id']];changes['home_buttons'].append(item['label'])
        view=StudioEngine(self.engine.adapter,candidate,controls=False)
        candidate['layout']=view.validate_layout(actor,candidate['layout'])
        for routine in candidate.get('routines',[]):
            if not (references(routine['actions'])&mapping.keys()):continue
            routine['actions']=remap(routine['actions'],mapping);routine['enabled']=False
            view.validate_routine(actor,{k:routine[k] for k in ['id','name','time','days','enabled','actions']})
            if routine.get('origin'):routine['origin']['customized']=True
            changes['schedules'].append({'id':routine['id'],'name':routine['name'],'enabled':False})
        for record in candidate.get('automations',[]):
            if not (references(record['rule'])&mapping.keys()):continue
            record['rule']=remap(record['rule'],mapping);record['rule']['enabled']=False
            record['rule']=RuleValidator(view,actor).rule(record['rule'])
            if record.get('origin'):record['origin']['customized']=True
            changes['automations'].append({'id':record['rule']['id'],'name':record['rule']['name'],'enabled':False})
        # Historical approval receipts must not re-enable old actions on a duplicate approval.
        for record in candidate.get('automations',[]):
            if any(i['id']==record['rule']['id'] for i in changes['automations']):record.pop('approval_keys',None)
        candidate['revision']+=1
        return candidate,changes,any(self.engine.adapter.state(old) is None for old in mapping)

    async def preview(self,actor,payload):
        await self.admin(actor)
        if not isinstance(payload,dict) or set(payload)!={'replacements','revision'}:raise ProductError('invalid_input','Review your replacement selections.')
        if type(payload['revision']) is not int or payload['revision']!=self.engine.document['revision']:raise ProductError('revision_conflict','Refresh your home before reviewing a replacement.')
        candidate,changes,unverified=self.prepare(actor,payload['replacements'])
        for record in candidate.get('automations',[]):
            if any(c['id']==record['rule']['id'] for c in changes['automations']):
                validate=getattr(self.engine.adapter,'validate_native',None)
                if validate:await validate(record['rule'])
        now=self.engine.adapter.now()
        for key in list(self.reviews):
            if self.reviews[key]['expires']<now:self.reviews.pop(key)
        if len(self.reviews)>=32:raise ProductError('busy','Finish a replacement review before opening another.')
        nonce=secrets.token_urlsafe(32);key=hashlib.sha256(nonce.encode()).hexdigest()
        self.reviews[key]={'actor':actor.id,'expires':now+300,'revision':payload['revision'],'pairs':deepcopy(payload['replacements']),'fingerprint':self.binding(candidate,payload['replacements']),'changes':changes}
        return {'approval_nonce':nonce,'changes':changes,'replacements':deepcopy(payload['replacements']),'missing_original':unverified,'affected_rules_stay_paused':True,'writes':False,'operates_devices':False,'external_configuration_changed':False}

    async def approve(self,actor,payload):
        await self.admin(actor)
        if not isinstance(payload,dict) or set(payload)!={'approval_nonce','confirmed','external_scope_ack'} or payload['confirmed'] is not True or payload['external_scope_ack'] is not True or not isinstance(payload['approval_nonce'],str):raise ProductError('confirmation_required','Confirm the replacement and the configuration outside VAutomate that needs separate review.')
        key=hashlib.sha256(payload['approval_nonce'].encode()).hexdigest()
        async with self.engine.edit_lock:
            await self.admin(actor)
            receipt=next((r for r in self.engine.document.get('replacement_receipts',[]) if r['key']==key and r['actor']==actor.id),None)
            if receipt:return {'status':'saved','revision':self.engine.document['revision'],'replayed':False,'affected_rules_stay_paused':True}
            review=self.reviews.get(key)
            if not review or review['actor']!=actor.id or review['expires']<self.engine.adapter.now():raise ProductError('approval_expired','Review this replacement again.')
            if self.engine.document['revision']!=review['revision']:raise ProductError('revision_conflict','Your home changed. Review the replacement again.')
            candidate,changes,_=self.prepare(actor,review['pairs'])
            if self.binding(candidate,review['pairs'])!=review['fingerprint']:raise ProductError('state_changed','The replacement changed. Review it again.')
            candidate['replacement_receipts']=(candidate.get('replacement_receipts',[])+[{'key':key,'actor':actor.id}])[-64:]
            await self.engine.adapter.save(candidate)
            self.engine.document=candidate;self.engine.notify_change();self.reviews.pop(key,None)
        self.engine.audit(actor,'device_references_replaced',None,'saved_rules_paused')
        return {'status':'saved','revision':candidate['revision'],'replayed':False,'affected_rules_stay_paused':True}
