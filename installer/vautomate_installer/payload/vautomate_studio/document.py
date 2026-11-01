"""Non-destructive storage envelope. Never guess at a newer document's meaning."""
from copy import deepcopy
import json
import math
import re

SCHEMA_VERSION=1
KEY=re.compile(r'[A-Za-z0-9_-]{1,80}\Z')
ENTITY=re.compile(r'[a-z_]+\.[a-z0-9_]+\Z')


def normalize(value):
    """Validate before runtime access, migrate a copy, and preserve the source."""
    if not isinstance(value,dict):raise ValueError('Studio storage needs recovery; its source was kept')
    version=value.get('schema_version',0)
    if type(version) is not int or version not in {0,SCHEMA_VERSION}:raise ValueError('Studio storage uses an unsupported schema; install a compatible release')
    count=0
    def walk(node,depth=0):
        nonlocal count
        count+=1
        if depth>40 or count>150_000:raise ValueError('Studio storage exceeds supported bounds')
        if isinstance(node,dict):
            if any(not isinstance(k,str) or len(k)>160 for k in node):raise ValueError('Invalid storage key')
            for item in node.values():walk(item,depth+1)
        elif isinstance(node,list):
            for item in node:walk(item,depth+1)
        elif isinstance(node,str):
            if len(node)>16_000:raise ValueError('Invalid storage text')
        elif type(node) in {int,float}:
            if not math.isfinite(node):raise ValueError('Invalid storage number')
        elif node is not None and type(node) is not bool:raise ValueError('Invalid storage value')
    walk(value)
    if len(json.dumps(value,allow_nan=False).encode('utf-8'))>4*1024**2:raise ValueError('Studio storage exceeds supported size')
    if type(value.get('revision')) is not int or value['revision']<0:raise ValueError('Invalid storage revision')
    layout=value.get('layout')
    if not isinstance(layout,dict) or any(not isinstance(layout.get(k),str) or not layout[k].strip() for k in ['name','subtitle']):raise ValueError('Invalid stored layout')
    rooms=layout.get('rooms');quick=layout.get('quick_actions')
    if not isinstance(rooms,list) or len(rooms)>80 or not isinstance(quick,list) or len(quick)>4:raise ValueError('Invalid stored rooms')
    seen=set()
    def ids(items):return isinstance(items,list) and all(isinstance(i,str) and ENTITY.fullmatch(i) for i in items) and len(set(items))==len(items)
    for room in rooms:
        if not isinstance(room,dict) or not isinstance(room.get('id'),str) or not KEY.fullmatch(room['id']) or room['id'] in seen or not isinstance(room.get('name'),str) or not room['name'].strip() or not ids(room.get('entities')) or len(room['entities'])>200:raise ValueError('Invalid stored room')
        seen.add(room['id'])
    for item in quick:
        if not isinstance(item,dict) or not isinstance(item.get('entity_id'),str) or not ENTITY.fullmatch(item['entity_id']) or not isinstance(item.get('label'),str):raise ValueError('Invalid stored Home button')
    if 'cards' in layout:
        cards=layout['cards']
        if not isinstance(cards,list) or len(cards)>40:raise ValueError('Invalid stored dashboard cards')
        for card in cards:
            if not isinstance(card,dict) or card.get('kind') not in {'entity','room'} or not isinstance(card.get('id'),str) or not KEY.fullmatch(card['id']) or type(card.get('span')) is not int or card['span'] not in {1,2,3}:raise ValueError('Invalid stored dashboard card')
            if card['kind']=='entity' and (not isinstance(card.get('entity_id'),str) or not ENTITY.fullmatch(card['entity_id'])):raise ValueError('Invalid stored card selection')
            if card['kind']=='room' and card.get('room_id') not in seen:raise ValueError('Invalid stored room card')
    for key in ['routines','automations','replacement_receipts']:
        if key in value and (not isinstance(value[key],list) or any(not isinstance(i,dict) for i in value[key])):raise ValueError('Invalid stored collection')
    for routine in value.get('routines',[]):
        if not all(k in routine for k in ['id','name','time','days','actions','enabled']) or not isinstance(routine['actions'],list) or any(not isinstance(a,dict) or set(a)!={'entity_id','action','data'} for a in routine['actions']) or type(routine['enabled']) is not bool:raise ValueError('Invalid stored routine')
    for record in value.get('automations',[]):
        rule=record.get('rule')
        if not isinstance(rule,dict) or not {'id','name','enabled','mode','room_id','triggers','condition','actions','pause_modes'}<=set(rule) or type(rule['enabled']) is not bool or not isinstance(rule['actions'],list) or not isinstance(rule['triggers'],list):raise ValueError('Invalid stored automation')
    for key in ['room_pauses','routine_runs','automation_runs']:
        if key in value and not isinstance(value[key],dict):raise ValueError('Invalid stored runtime collection')
    for pause in value.get('room_pauses',{}).values():
        if not isinstance(pause,dict) or type(pause.get('until')) not in {int,float}:raise ValueError('Invalid stored room hold')
    result=deepcopy(value);result['schema_version']=SCHEMA_VERSION
    return result
