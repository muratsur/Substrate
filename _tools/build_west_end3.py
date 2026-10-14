"""Full west extension build with per-piece verification."""
import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M

M.init()
SCN = 'editor_toolset.toolsets.scene.SceneTools'
FLOOR = '/Game/Modular_Sewer_Kit/Meshes/Modules/Floor/SM_floor_module.SM_floor_module'
WALL  = '/Game/Modular_Sewer_Kit/Meshes/Modules/Walls/SM_module_high_wall_01.SM_module_high_wall_01'
BLOCK = '/Game/Modular_Sewer_Kit/Meshes/Concrete_block/SM_concrete_02.SM_concrete_02'
FLOOR_LZ = 104.688253594228

def spawn(name, asset, x, y, z, yaw=0.0):
    r = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'add_to_scene_from_asset',
        'arguments': {'asset_path': asset, 'name': name,
                      'xform': {'location': {'x': float(x), 'y': float(y), 'z': float(z)},
                                'rotation': {'pitch': 0.0, 'yaw': float(yaw), 'roll': 0.0}}}})
    if r.strip().startswith('{') and '"refPath"' in r:
        return json.loads(r)['returnValue']['refPath']
    print('FAIL %s -> %s' % (name, r[:140]))
    return None

ok = fail = 0
# floor: lane centers x = -12570 .. -25570 step -1000 (tile 4 covers to -26070), lanes y=-270 and y=730
xs = [ -12570 - 1000*i for i in range(14) ]
for x in xs:
    for ly in (-270.0, 730.0):
        r = spawn('WEF%d' % int(-x/1000), FLOOR, x, ly, FLOOR_LZ)
        ok, fail = (ok+1, fail) if r else (ok, fail+1)
print('floor ok=%d fail=%d' % (ok, fail))

# walls every 730cm: south yaw 0 at y=-90, north yaw 180 at y=1580
wok = wfail = 0
i = 0
x = -11330.0
while x > -25400.0:
    r1 = spawn('WES%d' % i, WALL, x, -90.0, 240.0)
    r2 = spawn('WEN%d' % i, WALL, x, 1580.0, 240.0, yaw=180.0)
    wok += (r1 is not None) + (r2 is not None)
    wfail += (r1 is None) + (r2 is None)
    x -= 730.0
    i += 1
print('walls ok=%d fail=%d' % (wok, wfail))

# props: blocks on both ledges roughly every 3000cm
pok = pfail = 0
for i, x in enumerate(range(-11600, -24401, -3000)):
    r1 = spawn('WEB_S%d' % i, BLOCK, float(x), 120.0, 220.0, yaw=(i*17) % 30)
    r2 = spawn('WEB_N%d' % i, BLOCK, float(x) - 400.0, 1390.0, 220.0, yaw=(i*23) % 30)
    pok += (r1 is not None) + (r2 is not None)
    pfail += (r1 is None) + (r2 is None)
print('props ok=%d fail=%d' % (pok, pfail))

# save
r = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
    'arguments': {'asset_paths': ['/Game/Substrate/Maps/L_SectorC']}})
print('save:', r[:150])
import os
st = __import__('os').path.getsize('Content/Substrate/Maps/L_SectorC.umap')
print('umap:', st, 'bytes')
