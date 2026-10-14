import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
LEV = '/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:'
A = LEV + 'PersistentLevel.StaticMeshActor_3643'

def bounds(ref):
    b = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']
    return b['min'], b['max']

M.init()
mn, mx = bounds(A)
print('before: x[%.0f..%.0f] y[%.0f..%.0f] z[%.0f..%.0f]' % (mn['x'], mx['x'], mn['y'], mx['y'], mn['z'], mx['z']))
r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
    'arguments': {'actor': {'refPath': A},
                  'xform': {'location': {'x': -1691.6, 'y': 8420.4, 'z': -3000.0},
                            'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0},
                            'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}}})
print('move:', r[:80])
time.sleep(1.2)
mn, mx = bounds(A)
print('after : x[%.0f..%.0f] y[%.0f..%.0f] z[%.0f..%.0f]' % (mn['x'], mx['x'], mn['y'], mx['y'], mn['z'], mx['z']))
