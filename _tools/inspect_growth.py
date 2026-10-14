import sys, json, math
sys.path.insert(0, '_tools')
import mcpx as M

def find(name='', cls=''):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
        'arguments': {'name': name, 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': cls}}})
    try: return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception: return []

def loc(ref):
    return json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']

def bounds(ref):
    r = M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_bounds',
                             'arguments': {'actor': {'refPath': ref}}})
    return r[:300]

def props(inst, keys):
    r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties',
                             'arguments': {'instance': {'refPath': inst}, 'properties': keys}})
    return r[:500]

M.init()
pawn = (find('', '/Script/Engine.Character') or [None])[0]
p = loc(pawn)['location']
print('player at (%.0f, %.0f, %.0f)' % (p['x'], p['y'], p['z']))

for name in ('BP_GrowthNode_C_1', 'BP_AnomalySocket_C_2'):
    ref = 'PersistentLevel.' + name
    print('\n===', name)
    try: print('  bounds:', bounds(ref))
    except Exception as e: print('  bounds fail:', str(e)[:120])
    try:
        comps = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_components',
            'arguments': {'actor': {'refPath': ref}}}))['returnValue']
        for c in comps[:20]:
            print('   comp:', c['refPath'].split('.')[-1])
    except Exception as e: print('  comps fail:', str(e)[:120])

# everything Spawned by growth/anomaly: check all BP_* anomaly actors near player
print('\n=== spawned growth near player ===')
p2 = loc(pawn)['location'] if True else None
for cls in ('BP_GrowthNode_C', 'BP_AnomalyGrowth_C', 'BP_AnomalAbsence_C', 'BP_Growth_C'):
    for ref in find(cls):
        try:
            l = loc(ref)['location']
        except Exception:
            continue
        d = math.dist((l['x'],l['y'],l['z']), (p2['x'],p2['y'],p2['z']))
        if d < 3000:
            print('%-44s dist=%-7.0f at (%.0f,%.0f,%.0f)' % (ref.split(':')[-1], d, l['x'],l['y'],l['z']))
