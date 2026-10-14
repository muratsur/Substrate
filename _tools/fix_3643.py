import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
LEV = '/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:'
A3643 = LEV + 'PersistentLevel.StaticMeshActor_3643'
PAWN = LEV + 'PersistentLevel.BP_FirstPersonCharacter_C_0'

def bounds(ref):
    b = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']
    return b['min'], b['max']

def put_pawn(x, y, z):
    M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
        'arguments': {'actor': {'refPath': PAWN}, 'xform': {'location': {'x': x, 'y': y, 'z': z}}}})

def loc():
    t = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': PAWN}}}))['returnValue']['location']
    return (t['x'], t['y'], t['z'])

M.init()
mn, mx = bounds(A3643)
print('3643 before: x[%.0f..%.0f] y[%.0f..%.0f] z[%.0f..%.0f]' % (mn['x'], mx['x'], mn['y'], mx['y'], mn['z'], mx['z']))

# move it out of the walk lane: shift +2000 in y (north), keep x/z
r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
    'arguments': {'actor': {'refPath': A3643},
                  'xform': {'location': {'x': -1691.5956472285536, 'y': 10420.419249691198, 'z': 288.44475754543504},
                            'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0},
                            'scale': {'x': 1, 'y': 1, 'z': 1}}}})
print('move:', r[:80])
time.sleep(1.0)
mn, mx = bounds(A3643)
print('3643 after : x[%.0f..%.0f] y[%.0f..%.0f] z[%.0f..%.0f]' % (mn['x'], mx['x'], mn['y'], mx['y'], mn['z'], mx['z']))

# re-run the walk step probe through the seam
print('--- walk probe after moving 3643 ---')
put_pawn(-1554.0, 8409.0, 380.0)
time.sleep(1.2)
ok_to = None
for x in range(-1564, -1726, -20):
    put_pawn(x * 1.0, 8409.0, 380.0)
    time.sleep(1.6)
    cx, cy, cz = loc()
    stayed = abs(cx - x) < 12 and abs(cy - 8409) < 12
    print('  x=%d -> (%.0f, %.0f, %.0f) %s' % (x, cx, cy, cz, '' if stayed else '<- pushed'))
    if not stayed:
        break
    ok_to = x
print('clear to x=%s' % ok_to)
