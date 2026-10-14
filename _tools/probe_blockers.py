import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
SCN = 'editor_toolset.toolsets.scene.SceneTools'
LEV = '/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:'
PAWN = LEV + 'PersistentLevel.BP_FirstPersonCharacter_C_0'

def put(x, y, z):
    M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
        'arguments': {'actor': {'refPath': PAWN},
                      'xform': {'location': {'x': x, 'y': y, 'z': z}}}})

def loc():
    t = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
        'arguments': {'actor': {'refPath': PAWN}}}))['returnValue']['location']
    return ('%.0f' % t['x'], '%.0f' % t['y'], '%.0f' % t['z'])

M.init()
# broad sweep: ALL object channels 1..6 across the seam corridor
args = {'name': '', 'tag': '',
        'collision_channels': ['ObjectTypeQuery1', 'ObjectTypeQuery2', 'ObjectTypeQuery3',
                               'ObjectTypeQuery4', 'ObjectTypeQuery5', 'ObjectTypeQuery6'],
        'actor_type': {'refPath': ''},
        'bounds': {'min': {'x': -1900.0, 'y': 8000.0, 'z': 100.0},
                   'max': {'x': -1400.0, 'y': 8900.0, 'z': 700.0}, 'isValid': True}}
r = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'find_actors', 'arguments': args})
hits = json.loads(r)['returnValue']
print('=== collision-registered actors in seam corridor ===')
for h in hits:
    rp = h['refPath']
    if 'BP_FirstPersonCharacter' in rp:
        continue
    try:
        b = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': rp}}}))['returnValue']
        print('  %-48s x[%7.0f..%7.0f] y[%7.0f..%7.0f] z[%7.0f..%7.0f]' % (rp.split(':')[-1], b['min']['x'], b['max']['x'], b['min']['y'], b['max']['y'], b['min']['z'], b['max']['z']))
    except Exception:
        print('  %-48s (no bounds)' % rp.split(':')[-1])

print()
print('=== teleport probes ===')
for x, y in ((-1600.0, 8409.0), (-1700.0, 8409.0), (-1900.0, 8409.0), (-1700.0, 8550.0), (-1700.0, 8250.0)):
    put(x, y, 380.0)
    time.sleep(2.2)
    l = loc()
    stayed = abs(float(l[0]) - x) < 15 and abs(float(l[1]) - y) < 15
    print('  probe (%6.0f,%6.0f) -> after 2.2s at (%s, %s, %s) %s' % (x, y, l[0], l[1], l[2], '' if stayed else '<- PUSHED/EJECTED'))
    if not stayed:
        break
