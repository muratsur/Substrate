import sys, json, math
sys.path.insert(0, '_tools')
import mcpx as M
def find(name, cls=''):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
        'arguments': {'name': name, 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': cls}}})
    try: return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception as e: return []
def loc(ref):
    return json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']
M.init()
pawn = find('BP_FirstPersonCharacter')
p = loc(pawn[0])['location'] if pawn else None
print('player', p and (round(p['x']), round(p['y']), round(p['z'])))
seen = set()
for q in ['Airlock', 'WestGate', 'Block']:
    for ref in find(q):
        if ref in seen: continue
        seen.add(ref)
        t = loc(ref); l = t['location']
        d = math.dist((l['x'],l['y'],l['z']), (p['x'],p['y'],p['z'])) if p else -1
        print(ref.split(':')[-1], 'dist', round(d), 'at', round(l['x']), round(l['y']), round(l['z']), 'scale', t.get('scale'))
