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
    try:
        bb = json.loads(act('get_actor_bounds', {'actor': {'refPath': ref}, 'only_colliding': True}))['returnValue']
        return bb
    except Exception:
        return None

# every actor whose bounds overlap a wide band around the stop plane
b = {'min': {'x': -1500, 'y': 1550, 'z': -500}, 'max': {'x': 1500, 'y': 2300, 'z': 900}, 'isValid': True}
r = scn('find_actors', {'name': '', 'tag': '', 'collision_channels': [], 'bounds': b})
actors = [h['refPath'] for h in json.loads(r)['returnValue']]
print('actors overlapping band:', len(actors))
for ref in actors:
    cls = ref.split('.')[-1].split('_')[0] if '.' in ref else ''
    name = ref.split(':PersistentLevel.')[-1] if ':PersistentLevel.' in ref else ref
    bb = bounds(ref)
    if bb and (bb['min']['x'] or bb['max']['x'] or bb['min']['y'] or bb['max']['y'] or bb['min']['z'] or bb['max']['z']):
        print('  %-58s x[%.0f..%.0f] y[%.0f..%.0f] z[%.0f..%.0f]' % (name[:58],
            bb['min']['x'],bb['max']['x'],bb['min']['y'],bb['max']['y'],bb['min']['z'],bb['max']['z']))
    else:
        print('  %-58s (no bounds)' % name[:58])
