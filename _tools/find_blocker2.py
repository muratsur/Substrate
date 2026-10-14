import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

def find(name='', cls=''):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
        'arguments': {'name': name, 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': cls}}})
    try: return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception: return []

M.init()
pawns = find('', '/Script/Engine.Character')
print('pawns:', pawns)
if not pawns:
    sys.exit('no pawn')
pawn = pawns[0]
r = M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform',
                         'arguments': {'actor': {'refPath': pawn}}})
print('raw:', r[:300])
