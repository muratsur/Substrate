import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

EA = 'EditorToolset.EditorAppToolset'
LEV = '/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:'
GATE = LEV + 'PersistentLevel.StaticMeshActor_2678'
GATE_COMP = GATE + '.StaticMeshComponent0'

def ray(orig, yaw):
    M.app('SetCameraTransform', {'transform': {'location': {'x': orig[0], 'y': orig[1], 'z': orig[2]},
        'rotation': {'pitch': 0.0, 'yaw': yaw, 'roll': 0.0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
    r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'ScreenCoordsToWorld',
                             'arguments': {'coords': {'x': 0.5, 'y': 0.5}}})
    try: return json.loads(r)['returnValue']
    except Exception: return None

M.init()
print('--- west rays BEFORE (wall should block low) ---')
for z in (200.0, 430.0):
    h = ray((-1480.0, 8449.0, z), 180.0)
    print('  z=%4.0f -> %s' % (z, ('hit x=%.0f' % h['x']) if h else 'no hit'))

print('--- attempting to disable collision ---')
for values in ({'CollisionEnabled': 'NoCollision'},
               {'BodyInstance': {'bEnableCollision': False, 'CollisionEnabled': 'NoCollision'}},
               {'bEnableCollision': False}):
    r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties',
                             'arguments': {'instance': {'refPath': GATE_COMP}, 'values': json.dumps(values)}})
    print('  try', values, '->', r[:160])

print('--- west rays AFTER (low rays should pass beyond -1604 or reach -2600+) ---')
for z in (200.0, 260.0, 310.0, 430.0, 650.0):
    h = ray((-1480.0, 8449.0, z), 180.0)
    print('  z=%4.0f -> %s' % (z, ('hit x=%.0f' % h['x']) if h else 'no hit'))
