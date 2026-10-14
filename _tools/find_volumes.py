import sys, json, math
sys.path.insert(0, '_tools')
import mcpx as M
def find(cls):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
        'arguments': {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': cls}}})
    try: return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception: return []
M.init()
pawn = find('/Script/Engine.Character')[0]
def loc(ref):
    return json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']
p = loc(pawn)['location']
for cls in ['/Script/Engine.Volume', '/Script/Engine.TriggerVolume', '/Script/Engine.BlockingVolume']:
    for ref in find(cls):
        t = loc(ref); l = t['location']
        d = math.dist((l['x'], l['y'], l['z']), (p['x'], p['y'], p['z']))
        if d < 1500:
            print(ref.split(':')[-1], round(d), 'at', round(l['x']), round(l['y']), round(l['z']), 'scale', t.get('scale'))
