import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M

EA = 'EditorToolset.EditorAppToolset'
AT = 'editor_toolset.toolsets.actor.ActorTools'
LEV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:'
GATE = LEV + 'PersistentLevel.StaticMeshActor_2678'

def ray(orig, yaw, pitch=0.0):
    M.app('SetCameraTransform', {'transform': {'location': {'x': orig[0], 'y': orig[1], 'z': orig[2]},
        'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': 0.0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
    r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'ScreenCoordsToWorld',
                             'arguments': {'coords': {'x': 0.5, 'y': 0.5}}})
    try: return json.loads(r)['returnValue']
    except Exception: return None

M.init()
# park below the floor: same x/y as original, way under the ground
r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
    'arguments': {'actor': {'refPath': GATE},
                  'xform': {'location': {'x': -1629.6, 'y': 8602.6, 'z': -3000.0},
                            'rotation': {'pitch': 0.0, 'yaw': -90.0, 'roll': 0.0},
                            'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}}})
print('park below floor:', r[:80])
b = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds',
    'arguments': {'actor': {'refPath': GATE}}}))['returnValue']
print('bounds now: z[%d..%d]' % (b['min']['z'], b['max']['z']))

r = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                         'arguments': {'asset_paths': ['/Game/Substrate/Maps/L_SectorC']}})
print('save:', r[:100])
st = None
import os
st = os.stat('Content/Substrate/Maps/L_SectorC.umap')
print('umap mtime:', time.strftime('%m-%d %H:%M:%S', time.localtime(st.st_mtime)))

# fresh PIE for a real walk test
print('start PIE:', M.app('StartPIE', {'options': {'bSimulate': False}})[:60])
time.sleep(12)
print('PIE running:', M.app('IsPIERunning', {})[:40])

# verify in PIE: west lane at walking heights clear of the -1604 frame
print('--- PIE west rays (from eye/mid heights) ---')
for z in (300.0, 360.0, 430.0):
    h = ray((-1500.0, 8449.0, z), 180.0)
    print('  z=%4.0f -> %s' % (z, ('hit x=%.0f (dist %.0f)' % (h['x'], abs(h['x']+1500))) if h else 'no hit'))
