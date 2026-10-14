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
M.init()
pawn = find('', '/Script/Engine.Character')
p = loc(pawn[0])['location'] if pawn else None
print('player', p and (round(p['x']), round(p['y']), round(p['z'])))
hits = []
seen = set()
for q in ['Anomaly', 'Growth', 'Door', 'Gate', 'BP_Airlock']:
    for ref in find(q):
        key = ref.split(':')[-1]
        if key in seen: continue
        seen.add(key)
        try:
            t = loc(ref); l = t['location']
        except Exception:
            continue
        d = math.dist((l['x'],l['y'],l['z']), (p['x'],p['y'],p['z'])) if p else -1
        hits.append((d, key, l, t.get('scale')))
hits.sort()
for d, key, l, s in hits:
    if d < 6000:
        print('%-40s dist=%-6.0f at (%.0f, %.0f, %.0f) scale=%s' % (key, d, l['x'], l['y'], l['z'], s))
print('total candidates found:', len(hits))
