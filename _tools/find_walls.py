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
hits = []
for ref in find('/Script/Engine.StaticMeshActor'):
    t = loc(ref); l = t['location']
    d = math.dist((l['x'], l['y'], l['z']), (p['x'], p['y'], p['z']))
    if d < 700:
        hits.append((round(d), ref.split(':')[-1], round(l['x']), round(l['y']), round(l['z']), t.get('scale')))
hits.sort()
for h in hits[:20]: print(*h)
print('count', len(hits))
