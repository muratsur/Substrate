import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M

EA = 'EditorToolset.EditorAppToolset'
AT = 'editor_toolset.toolsets.actor.ActorTools'
LEV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:'
GATE = LEV + 'PersistentLevel.StaticMeshActor_2678'

def ray(orig, yaw):
    M.app('SetCameraTransform', {'transform': {'location': {'x': orig[0], 'y': orig[1], 'z': orig[2]},
        'rotation': {'pitch': 0.0, 'yaw': yaw, 'roll': 0.0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
    r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'ScreenCoordsToWorld',
                             'arguments': {'coords': {'x': 0.5, 'y': 0.5}}})
    try: return json.loads(r)['returnValue']
    except Exception: return None

M.init()
# check current transform and read it so we only shift location
cur = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
    'arguments': {'actor': {'refPath': GATE}}}))['returnValue']
print('current:', cur)
r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
    'arguments': {'actor': {'refPath': GATE},
                  'xform': {'location': {'x': -1580.0, 'y': 11200.0, 'z': cur['location']['z']},
                            'rotation': cur.get('rotation', {'pitch': 0, 'yaw': 0, 'roll': 0}),
                            'scale': cur.get('scale', {'x': 1, 'y': 1, 'z': 1})}}})
print('move:', r[:120])
time.sleep(0.5)
b = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds',
    'arguments': {'actor': {'refPath': GATE}}}))['returnValue']
print('bounds after move:', b['min'], b['max'])

print('--- edit-mode west rays after move ---')
ok = True
for z in (170.0, 200.0, 240.0, 280.0):
    h = ray((-1480.0, 8449.0, z), 180.0)
    hit = h and abs(h['x'] + 1604) < 5
    print('  z=%4.0f -> %s' % (z, ('hit x=%.0f (STILL BLOCKED)' % h['x']) if hit else ('hit x=%.0f' % h['x'] if h else 'no hit')))
    if hit: ok = False
print('lane clear:', ok)

r = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                         'arguments': {'asset_paths': ['/Game/Substrate/Maps/L_SectorC']}})
print('save:', r[:100])
import os
st = os.stat('Content/Substrate/Maps/L_SectorC.umap')
print('umap size:', st.st_size, 'mtime:', time.strftime('%m-%d %H:%M:%S', time.localtime(st.st_mtime)))
