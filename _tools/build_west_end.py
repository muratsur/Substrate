"""Extend the west tunnel past x=-11500 with matching Modular_Sewer_Kit geometry.

Determines current world extent by scanning test floor tiles (west_geo state),
stamps floor tiles westward over a 3x2 tile lane, walls both sides, sprinkles
props, adds an end-cap wall and two point lights, then repositions the
invisible BlockingVolume_1 to the new world edge so you can't walk off.

Run:  python _tools/build_west_end.py          (default: stop PIE if needed, then build+save)
      python _tools/build_west_end.py verify   (no edits; bounds check)
"""
import sys, json, os, time
sys.path.insert(0, '_tools')
import mcpx as M

M.init()
SCN = 'editor_toolset.toolsets.scene.SceneTools'
AT  = 'editor_toolset.toolsets.actor.ActorTools'
OT  = 'editor_toolset.toolsets.object.ObjectTools'
LEV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
FLOOR = '/Game/Modular_Sewer_Kit/Meshes/Modules/Floor/SM_floor_module.SM_floor_module'
WALL  = '/Game/Modular_Sewer_Kit/Meshes/Modules/Walls/SM_module_high_wall_01.SM_module_high_wall_01'
BLOCK = '/Game/Modular_Sewer_Kit/Meshes/Concrete_block/SM_concrete_02.SM_concrete_02'

FLOOR_LY = -270.0  # template lane south
FLOOR_RY =  730.0  # template lane north
FLOOR_LZ = 104.688253594228
WALL_S_LOC = (-10600.0, -90.0, 240.0)   # south wall template
WALL_N_LOC = (-9900.0, 1580.0, 240.0)   # north wall template (yaw 180)
BLOCK_LOC = (-10460.0, 120.0, 220.0)    # prop template
BLOCK_LOC2 = (-10480.0, 1390.0, 220.0)

def pie():
    return 'true' in M.app('IsPIERunning', {})

def bounds(name):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds',
                             'arguments': {'actor': {'refPath': LEV + name}}})
    v = json.loads(r)['returnValue']
    return tuple(round(v['min'][k]) for k in 'xyz') + tuple(round(v['max'][k]) for k in 'xyz')

def stop_pie():
    if pie():
        print('PIE running - stopping (saves and spawns need PIE off)')
        M.app('StopPIE', {})
        time.sleep(5)
        print('  PIE now:', M.app('IsPIERunning', {})[:50])

def spawn(name, asset, loc, yaw=0.0, scale=1.0):
    xf = {'location': loc,
          'rotation': {'pitch': 0.0, 'yaw': yaw, 'roll': 0.0},
          'scale': {'x': scale, 'y': scale, 'z': scale}}
    return M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'add_to_scene_from_asset',
                                'arguments': {'asset_path': asset, 'name': name, 'xform': xf}})

def build():
    stop_pie()
    # how far west does the built tunnel already reach? probe with temporary floor queries
    # we know from survey: existing floor spans down to x -10570..-11070 (tile center -11070 covers -11570..-10570)
    existing_tiles = [x for x in (-10570.0, -11070.0)]
    west_start = -11570.0  # continue from the west edge of the -11070 tile
    lanes = [FLOOR_LY, FLOOR_RY]
    n_floor = 0
    for i in range(14):  # 14 tiles x 1000 = 14000cm west
        x = west_start - i * 1000.0
        for ly in lanes:
            name = 'WestExt_Floor_%02d_%d' % (i, 0 if ly < 0 else 1)
            r = spawn(name, FLOOR, (x, ly, FLOOR_LZ))
            if 'error' in r.lower() or 'Fail' in r:
                print('spawn fail:', name, r[:120])
            else:
                n_floor += 1
    print('floor tiles spawned:', n_floor)

    # walls along both sides every 1000cm (south y=-90, north y=1580)
    n_wall = 0
    for i in range(14):
        x_center = -11570.0 - i * 1000.0 + 0.0  # south wall template is a 730-long piece; use same spacing as existing (-10600 - i*730 pattern too dense; use 1000 spacing, slight overlap OK)
        # south wall (yaw 0), staggered every 1000
        spawn('WestExt_WallS_%02d' % i, WALL, (-11250.0 - i * 1000.0, WALL_S_LOC[1], WALL_S_LOC[2]))
        # north wall (yaw 180) to face -Y into the lane
        spawn('WestExt_WallN_%02d' % i, WALL, (-11250.0 - i * 1000.0, WALL_N_LOC[1], WALL_N_LOC[2]), yaw=180.0)
        n_wall += 2
    print('wall pieces spawned:', n_wall)

    # props: concrete blocks along both ledges every ~3000cm, with slight yaw jitter
    n_prop = 0
    for i, x in enumerate(range(-11300, -24500, -3000)):
        spawn('WestExt_BlockS_%02d' % i, BLOCK, (float(x), 120.0, 220.0), yaw=(i * 17.0) % 30.0)
        spawn('WestExt_BlockN_%02d' % i, BLOCK, (float(x) - 400.0, 1390.0, 220.0), yaw=((i * 23) % 30) * 1.0)
        n_prop += 2
    print('props spawned:', n_prop)

    # end cap: two walls rotated to close the corridor at x ~ -25500+500
    cap_x = -25400.0
    spawn('WestExt_CapS', WALL, (cap_x, -90.0, 240.0), yaw=90.0)
    spawn('WestExt_CapN', WALL, (cap_x, 1580.0, 240.0), yaw=90.0)
    n_floor += 0
    print('end cap spawned at x=%d' % cap_x)

    # move the invisible boundary BlockingVolume_1 to just west of the end cap
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
        'arguments': {'actor': {'refPath': LEV + 'BlockingVolume_1'},
                      'xform': {'location': {'x': -25890.0, 'y': -945.0, 'z': 280.0},
                                'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0},
                                'scale': {'x': 4.4, 'y': 26.0, 'z': 0.2}}}})
    print('BV1 moved:', r[:80])
    time.sleep(1)
    print('BV1 new box:', bounds('BlockingVolume_1'))

    # lights: reuse PointLight placement pattern - PointLight_1..3 were at transit
    n_lights = 0
    for i, x in enumerate(range(-11200, -24200, -3200)):
        r = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'add_to_scene_from_class',
            'arguments': {'actor_type': {'refPath': '/Script/Engine.PointLight'},
                          'name': 'WestExt_Light_%02d' % i,
                          'xform': {'location': {'x': float(x), 'y': 700.0, 'z': 700.0}}}})
        if 'error' in r.lower() or 'Fail' in r:
            print('light spawn fail:', i, r[:120])
        else:
            n_lights += 1
    print('lights spawned:', n_lights)

def verify():
    for n in ('StaticMeshActor_85', 'WestExt_Floor_00_0', 'WestExt_Floor_13_1', 'WestExt_CapS'):
        try:
            print('%-24s %s' % (n, bounds(n)))
        except Exception as e:
            print(n, 'no bounds:', str(e)[:100])

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'verify':
        verify()
    else:
        build()
        # save
        r = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                                 'arguments': {'asset_paths': ['/Game/Substrate/Maps/L_SectorC']}})
        print('save:', r[:200])
        st = os.stat('Content/Substrate/Maps/L_SectorC.umap')
        print('umap: %d bytes  %s' % (st.st_size, time.strftime('%m-%d %H:%M:%S', time.localtime(st.st_mtime))))
