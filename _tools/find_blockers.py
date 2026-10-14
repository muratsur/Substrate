import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
AT = M.ACT
def find(cls):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
        'arguments': {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': cls}}})
    try: return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception: return []
M.init()
pawn = (find('/Script/Engine.Character') or [None])[0]
p = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': pawn}}}))['returnValue']['location']
print('player', round(p['x']), round(p['y']), round(p['z']))
for ref in find('/Engine/Engine.BlockingVolume') or find('/Script/Engine.BlockingVolume'):
    t = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']
    l, s = t['location'], t.get('scale', {})
    print(ref.split(':')[-1], 'loc', round(l['x']), round(l['y']), round(l['z']), 'scale', s.get('x'), s.get('y'), s.get('z'))
