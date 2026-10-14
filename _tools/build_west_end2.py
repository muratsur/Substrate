"""Rebuild the west extension with strict response checking."""
import sys, json, os, time
sys.path.insert(0, '_tools')
import mcpx as M

M.init()
SCN = 'editor_toolset.toolsets.scene.SceneTools'
AT  = 'editor_toolset.toolsets.actor.ActorTools'
FLOOR = '/Game/Modular_Sewer_Kit/Meshes/Modules/Floor/SM_floor_module.SM_floor_module'
WALL  = '/Game/Modular_Sewer_Kit/Meshes/Modules/Walls/SM_module_high_wall_01.SM_module_high_wall_01'
BLOCK = '/Game/Modular_Sewer_Kit/Meshes/Concrete_block/SM_concrete_02.SM_concrete_02'
FLOOR_LZ = 104.688253594228

def pie():
    return 'true' in M.app('IsPIERunning', {})

if pie():
    M.app('StopPIE', {}); time.sleep(5)
    print('PIE stopped')

def spawn(name, asset, x, y, z, yaw=0.0):
    r = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'add_to_scene_from_asset',
        'arguments': {'asset_path': asset, 'name': name,
                      'xform': {'location': {'x': float(x), 'y': float(y), 'z': float(z)},
                                'rotation': {'pitch': 0.0, 'yaw': float(yaw), 'roll': 0.0}}}})
    ok = r.strip().startswith('{') and '"refPath"' in r
    if not ok:
        print('FAIL %s -> %s' % (name, r[:140]))
        return None
    return json.loads(r)['returnValue']['refPath']

# spawn ONE piece first and see the raw response path handling
t0 = spawn('WE_Test_Floor', FLOOR, -11570.0, -270.0, FLOOR_LZ)
print('single test floor ->', t0)
if t0:
    b = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds',
        'arguments': {'actor': {'refPath': t0}}}))['returnValue']
    print('  bounds:', tuple(round(b['min'][k]) for k in 'xyz'), '->', tuple(round(b['max'][k]) for k in 'xyz'))
