import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M

EA = 'EditorToolset.EditorAppToolset'
AT = 'editor_toolset.toolsets.actor.ActorTools'
LEV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:'
GATE = LEV + 'PersistentLevel.StaticMeshActor_2678'
GATE_COMP = GATE + '.StaticMeshComponent0'

def ray(orig, yaw, pitch=0.0):
    M.app('SetCameraTransform', {'transform': {'location': {'x': orig[0], 'y': orig[1], 'z': orig[2]},
        'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': 0.0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
    r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'ScreenCoordsToWorld',
                             'arguments': {'coords': {'x': 0.5, 'y': 0.5}}})
    try: return json.loads(r)['returnValue']
    except Exception: return None

M.init()
print('PIE:', M.app('IsPIERunning', {})[:50])
if 'true' in M.app('IsPIERunning', {}).lower():
    print('stop PIE:', M.app('StopPIE', {})[:80])
    time.sleep(4)
    print('PIE now:', M.app('IsPIERunning', {})[:50])

print('bounds in edit mode:', M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds',
    'arguments': {'actor': {'refPath': GATE}}})[:250])

print('--- edit-mode west rays BEFORE ---')
for z in (170.0, 200.0, 240.0, 280.0, 310.0, 360.0):
    h = ray((-1480.0, 8449.0, z), 180.0)
    print('  z=%4.0f -> %s' % (z, ('hit x=%.0f' % h['x']) if h else 'no hit'))

# disable the wall's collision in the persistent level
r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties',
                         'arguments': {'instance': {'refPath': GATE_COMP},
                                       'values': json.dumps({'BodyInstance': {'CollisionEnabled': 'NoCollision'}})}})
print('disable collision:', r[-120:])

print('--- edit-mode west rays AFTER ---')
for z in (170.0, 200.0, 240.0, 280.0, 310.0, 360.0):
    h = ray((-1480.0, 8449.0, z), 180.0)
    print('  z=%4.0f -> %s' % (z, ('hit x=%.0f' % h['x']) if h else 'no hit'))

r = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                         'arguments': {'asset_paths': ['/Game/Substrate/Maps/L_SectorC']}})
print('save:', r[:200])
import os
st = os.stat('Content/Substrate/Maps/L_SectorC.umap')
print('umap size:', st.st_size, 'mtime:', time.strftime('%m-%d %H:%M:%S', time.localtime(st.st_mtime)))
