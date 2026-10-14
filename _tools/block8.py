import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
SCN=M.SCN; ACT=M.ACT

def scn(name, args=None):
    return M.call('call_tool', {'toolset_name': SCN, 'tool_name': name, 'arguments': args or {}})
def act(name, args=None):
    return M.call('call_tool', {'toolset_name': ACT, 'tool_name': name, 'arguments': args or {}})

def bounds(ref):
    bb = json.loads(act('get_actor_bounds', {'actor': {'refPath': ref}, 'only_colliding': True}))['returnValue']
    return bb

# 1) all airlock actors
r = scn('find_actors', {'name': 'airlock', 'tag': '', 'collision_channels': []})
print('AIRLOCK ACTORS:')
for h in json.loads(r)['returnValue']:
    ref = h['refPath']; bb = bounds(ref)
    print('  %-44s x[%.0f..%.0f] y[%.0f..%.0f] z[%.0f..%.0f]' % (ref.split(':PersistentLevel.')[-1][:44],
        bb['min']['x'],bb['max']['x'],bb['min']['y'],bb['max']['y'],bb['min']['z'],bb['max']['z']))

# 2) pawn-blocking anything in a WIDE box north of the stop (any x in lane, y 1760..2400)
b = {'min': {'x': -400, 'y': 1760, 'z': 200}, 'max': {'x': 400, 'y': 2400, 'z': 600}, 'isValid': True}
r = scn('find_actors', {'name': '', 'tag': '', 'collision_channels': ['ObjectTypeQuery3'], 'bounds': b})
print('PAWN-BLOCK colliders y1760-2400:', [(h['refPath'].split(':PersistentLevel.')[-1]) for h in json.loads(r)['returnValue']])
