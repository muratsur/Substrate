import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
SCN=M.SCN; ACT=M.ACT

def scn(name, args=None):
    return M.call('call_tool', {'toolset_name': SCN, 'tool_name': name, 'arguments': args or {}})
def act(name, args=None):
    return M.call('call_tool', {'toolset_name': ACT, 'tool_name': name, 'arguments': args or {}})

# Plane the pawn stops at: y ~ 1775-ish face. Probe box straddling it, full walk heights.
b = {'min': {'x': -60, 'y': 1740, 'z': 250}, 'max': {'x': 60, 'y': 1820, 'z': 500}, 'isValid': True}
r = scn('find_actors', {'name': '', 'tag': '', 'collision_channels': ['ObjectTypeQuery3'], 'bounds': b})
hits = json.loads(r)['returnValue']
print('pawn-channel hits at y-plane 1740-1820:', len(hits))
for h in hits:
    ref = h['refPath']
    bb = json.loads(act('get_actor_bounds', {'actor': {'refPath': ref}, 'only_colliding': True}))['returnValue']
    print(' ', ref.split('.')[-1], ref.split('/')[-1][:40])
    print('    bounds min=(%.0f,%.0f,%.0f) max=(%.0f,%.0f,%.0f)' % (bb['min']['x'],bb['min']['y'],bb['min']['z'],bb['max']['x'],bb['max']['y'],bb['max']['z']))
