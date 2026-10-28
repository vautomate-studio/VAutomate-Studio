"""Admin-only onboarding suggestions. Never pair, rename or operate a device."""
from copy import deepcopy
import uuid


def status(engine, actor):
    from .engine import BRIDGE_VERSION
    engine.admin(actor)
    layout = engine.document['layout']
    entities = engine.snapshot(actor)
    offline = sum(s['state'] in {'unknown','unavailable'} for s in entities)
    return {
        'schema_version':1,
        'checked_at':int(engine.adapter.now()),
        'installation_id':engine.installation_id,
        'release':BRIDGE_VERSION,
        'core_version':engine.adapter.version,
        'production_ready':False,
        'layout_revision':engine.document['revision'],
        'room_count':len(layout['rooms']),
        'device_count':len(entities),
        'offline_count':offline,
        'checks':[
            {'id':'layout','label':'Rooms and controls selected','status':'ready' if layout['rooms'] and entities else 'needs_setup'},
            {'id':'devices','label':'Selected devices reachable','status':'needs_attention' if offline else ('ready' if entities else 'needs_setup')},
            {'id':'controls','label':'Device controls','status':'evaluation_enabled' if engine.controls else 'read_only'},
            {'id':'backup','label':'Independent backup and restore drill','status':'not_verified'},
            {'id':'physical','label':'Physical device and safety checks','status':'not_verified'},
            {'id':'handover','label':'Customer sign-in and recovery','status':'not_verified'},
        ],
        'automatic_updates':False,
        'update_policy_scope':'Studio has no updater; platform and phone settings require separate verification',
        'remote_support_enabled':False,
    }


def suggest(engine, actor, discovery):
    engine.admin(actor)
    if engine.document['layout']['rooms']:
        from .engine import ProductError
        raise ProductError('already_configured','Your home already has rooms. Use Personalize to edit them without replacing your selections.')
    states = {s['entity_id']:s for s in engine.snapshot(actor,discover=True)}
    devices = {d['id']:d for d in discovery['devices']}
    registries = {r['entity_id']:r for r in discovery['registry']}
    areas = {a['id']:a for a in discovery['areas']}
    groups,unassigned = {},0
    preferred = {'light','fan','switch','cover','media_player','alarm_control_panel','climate','camera'}
    informative = {'temperature','humidity','illuminance','motion','occupancy','presence','door','window','opening','smoke','moisture','carbon_monoxide'}
    for entity_id,s in states.items():
        domain = entity_id.split('.')[0]
        registry = registries.get(entity_id,{})
        if registry.get('disabled') or registry.get('diagnostic'):
            continue
        if domain not in preferred and not (domain in {'sensor','binary_sensor'} and s.get('attributes',{}).get('device_class') in informative):
            continue
        area = registry.get('area_id') or devices.get(registry.get('device_id'),{}).get('area_id')
        if area not in areas:
            unassigned += 1
            continue
        if sum(len(ids) for ids in groups.values()) >= 2000:
            break
        ids = groups.setdefault(area,[])
        if len(ids) < 200:
            ids.append(entity_id)
    # Preserve registry order; future device state changes cannot reorder cards.
    layout = deepcopy(engine.document['layout'])
    used_names = set()
    for area,ids in list(groups.items())[:80]:
        base = str(areas[area]['name'])[:70].strip() or 'Room'
        name = base
        suffix = 2
        while name.casefold() in used_names:
            name = f'{base} {suffix}'
            suffix += 1
        used_names.add(name.casefold())
        layout['rooms'].append({'id':'room-'+uuid.uuid4().hex[:12],'name':name,'entities':ids})
    return {'layout':engine.validate_layout(actor,layout),'revision':engine.document['revision'],
            'unassigned_count':unassigned,'writes':False,'devices_operated':False,
            'message':'Review every room and device before publishing. Devices without a room can be added manually.'}
