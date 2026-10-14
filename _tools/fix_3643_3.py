import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
LEV_EDIT = '/Game/Substrate/Maps/L_SectorC.L_SectorC:'
A = LEV_EDIT + 'PersistentLevel.StaticMeshActor_3643'

def bounds(ref):
    b = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']
    return b['min'], b['max']

M.init()
print('PIE:', M.app('IsPIERunning', {})[:50])
if 'true' in M.app('IsPIERunning', {}).lower():
    print('stop PIE:', M.app('StopPIE', {})[:60])
    time.sleep(4)
print('PIE now:', M.app('IsPIERunning', {})[:40])

mn, mx = bounds(A)
print('before: x[%.0f..%.0f] y[%.0f..%.0f] z[%.0f..%.0f]' % (mn['x'], mx['x'], mn['y'], mx['y'], mn['z'], mx['z']))
r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
    'arguments': {'actor': {'refPath': A},
                  'xform': {'location': {'x': -1691.6, 'y': 8420.4, 'z': -3000.0},
                            'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0},
                            'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}}})
print('move:', r[:80])
time.sleep(1.0)
mn, mx = bounds(A)
print('after : x[%.0f..%.0f] y[%.0f..%.0f] z[%.0f..%.0f]' % (mn['x'], mx['x'], mn['y'], mx['y'], mn['z'], mx['z']))

r = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                         'arguments': {'asset_paths': ['/Game/Substrate/Maps/L_SectorC']}})
print('save:', r[:100])
import os
st = os.stat('Content/Substrate/Maps/L_SectorC.umap')
print('umap mtime:', time.strftime('%m-%d %H:%M:%S', time.localtime(st.st_mtime)))

# restart PIE and walk-probe the seam
print('start PIE:', M.app('StartPIE', {'options': {'bSimulate': False}})[:50])
time.sleep(13)
print('PIE running:', M.app('IsPIERunning', {})[:40])
LEV_PIE = '/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:'
PAWN = LEV_PIE + 'PersistentLevel.BP_FirstPersonCharacter_C_0'

def put(x, y, z):
    M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
        'arguments': {'actor': {'refPath': PAWN}, 'xform': {'location': {'x': x, 'y': y, 'z': z}}}})

def loc():
    t = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': PAWN}}}))['returnValue']['location']
    return (t['x'], t['y'], t['z'])

put(-1554.0, 8409.0, 380.0)
time.sleep(1.5)
ok_to = None
for x in range(-1564, -1746, -20):
    put(x * 1.0, 8409.0, 380.0)
    time.sleep(1.6)
    cx, cy, cz = loc()
    stayed = abs(cx - x) < 12 and abs(cy - 8409) < 12
    print('  x=%d -> (%.0f, %.0f, %.0f) %s' % (x, cx, cy, cz, '' if stayed else '<- pushed/BLOCKED'))
    if not stayed:
        break
    ok_to = x
print('walk-clear east-to-west to x=%s' % ok_to)
