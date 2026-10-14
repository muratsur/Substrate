import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
LEV = '/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:'
PAWN = LEV + 'PersistentLevel.BP_FirstPersonCharacter_C_0'

def put(x, y, z):
    M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
        'arguments': {'actor': {'refPath': PAWN},
                      'xform': {'location': {'x': x, 'y': y, 'z': z}}}})

def loc():
    t = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
        'arguments': {'actor': {'refPath': PAWN}}}))['returnValue']['location']
    return (t['x'], t['y'], t['z'])

M.init()
print('start at', loc())
last_ok = None
for x in [x * 1.0 for x in range(-1554, -1725, -10)]:
    put(x, 8409.0, 380.0)
    time.sleep(1.6)
    cx, cy, cz = loc()
    stayed = abs(cx - x) < 12 and abs(cy - 8409) < 12
    if not stayed:
        print('  BLOCKED: target x=%.0f -> pawn pushed to (%.0f, %.0f, %.0f)' % (x, cx, cy, cz))
        print('  last free x=%.0f  => blocking face near x=%.0f (capsule r=34 => collider face ~x=%.0f)' % (last_ok, x, (last_ok if last_ok else x) - 34))
        break
    last_ok = x
    print('  ok x=%.0f (at %.0f, %.0f, %.0f)' % (x, cx, cy, cz))
else:
    print('  no block down to -1724')
