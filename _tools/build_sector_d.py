"""Sector D, the ending (DESIGN.md section 7: Research, "the source"). Three beats past the shift-8 arrival tube:
the tube (SectorD_Tube_*, unchanged), an abandoned lab, and a containment chamber full of growth with the C-06 relief
valve in it. Built from the Alien_Biomass kit straight off the tube's open north end (y -5671).
Rooms are kit wall modules (320 x 120 x 380, pivot at min corner), 640 x 820 floor tiles and 320 x 820 ceiling panels
on a 1280-wide footprint (x -1078..202): lab y -5671..-4031, chamber -4031..-2391, one door frame between them.
Every piece is found by label and re-placed, so re-running moves things instead of duplicating them.
Usage: python _tools/build_sector_d.py   (PIE stopped), then save L_SectorC."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
import build_sector_a as A
KIT = '/Game/Alien_Biomass/Meshes/'
FOLDER = 'Substrate/SectorD'
X0, X1 = -1078.0, 202.0            # room footprint, west/east
Y0, Y1, Y2 = -5671.0, -4031.0, -2391.0   # tube mouth, lab/chamber divider, chamber back wall
FZ, H = 290.0, 380.0                # floor top (tube floor), wall height
DOOR_I = 1                          # divider gap: wall segment 1 (x -758..-438)
LAB_LIGHT = {'r': 0.8, 'g': 0.92, 'b': 1.0, 'a': 1.0}
RED = {'r': 1.0, 'g': 0.15, 'b': 0.1, 'a': 1.0}

def m(path): return KIT + path + '.' + path.split('/')[-1]
def xf(x, y, z, yaw=0.0, s=(1, 1, 1)):
    return {'location': {'x': x, 'y': y, 'z': z}, 'rotation': {'pitch': 0, 'yaw': yaw, 'roll': 0}, 'scale': dict(zip('xyz', s))}

def place(label, mesh, t):
    a = A.find(label) or A.call(M.SCN, 'add_to_scene_from_asset', {'asset_path': KIT + mesh, 'name': label, 'xform': t})
    A.call(M.ACT, 'set_actor_transform', {'actor': a, 'xform': t})
    A.call(M.SCN, 'set_actor_folder', {'actor': a, 'folder_path': FOLDER})
    return a

def light(label, x, y, z, cd, radius, colour):
    t = xf(x, y, z)
    a = A.find(label) or A.call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.PointLight'}, 'name': label, 'xform': t})
    A.call(M.ACT, 'set_actor_transform', {'actor': a, 'xform': t})
    A.call(M.SCN, 'set_actor_folder', {'actor': a, 'folder_path': FOLDER})
    A.call(M.OBJ, 'set_properties', {'instance': {'refPath': a['refPath'] + '.LightComponent0'}, 'values': json.dumps(
        {'Intensity': cd, 'IntensityUnits': 'Candelas', 'AttenuationRadius': radius, 'LightColor': colour, 'Mobility': 'Movable'})})
    return a

def shell():
    n = 0
    for i in range(2):                     # floor tiles 640 x 820
        for j in range(4):
            place(f'D_Floor_{i}{j}', 'Floor/SM_floor_02', xf(X0 + i * 640, Y0 + j * 820, FZ - 18)); n += 1
    for i in range(4):                     # ceiling panels 320 x 820
        for j in range(4):
            place(f'D_Ceil_{i}{j}', 'Ceiling/SM_ceiling_large', xf(X0 + i * 320, Y0 + j * 820, FZ + H)); n += 1
    W = 'Wall_modules/SM_module_wall_0'
    for i in (0, 3):                       # south wall, leaving the tube mouth (segments 1-2) open
        place(f'D_WallS_{i}', W + '1', xf(X0 + i * 320, Y0 - 120, FZ)); n += 1
    for i in range(4):                     # divider, door in segment DOOR_I
        if i != DOOR_I: place(f'D_WallMid_{i}', W + '3', xf(X0 + i * 320, Y1 - 60, FZ)); n += 1
    place('D_DoorFrame', 'Door/SM_door_frame', xf(X0 + DOOR_I * 320 + 160, Y1, FZ)); n += 1
    for i in range(4):                     # north (back) wall
        place(f'D_WallN_{i}', W + '2', xf(X0 + i * 320, Y2, FZ)); n += 1
    k = 0
    while Y0 + k * 320 < Y2:               # side walls, rotated
        place(f'D_WallW_{k}', W + ('1' if k % 2 else '2'), xf(X0, Y0 + k * 320, FZ, 90)); n += 1
        place(f'D_WallE_{k}', W + ('3' if k % 2 else '1'), xf(X1, Y0 + (k + 1) * 320, FZ, -90)); n += 1
        k += 1
    return n

def lab():
    for k, y in enumerate((-5350, -4900, -4450)):           # benches with monitors along the west wall
        place(f'D_Bench_{k}', 'Tables/SM_table_01', xf(X0 + 75, y, FZ, 0))
    place('D_TableClean', 'Tables/SM_table_clean_01', xf(-250, -4950, FZ, 90))
    for k, (dx, dy) in enumerate(((-30, -40), (10, 25), (40, -10), (-5, 60))):
        place(f'D_Beaker_{k}', 'Scientific_props/SM_beaker', xf(-250 + dx, -4950 + dy, FZ + 88))
    place('D_Chair', 'Tables/SM_chair_01', xf(X0 + 330, -4880, FZ, 35))
    for k, y in enumerate((-5450, -5320, -5190)):           # filing shelves along the east wall
        place(f'D_Shelf_{k}', 'Shelf/SM_shelf_01', xf(X1 - 45, y, FZ, 180))
    for k, (x, y) in enumerate(((-860, -4150), (-330, -4150), (-960, -4320))):   # growth leaking in beside the door, not in front of it
        place(f'D_LabGrowth_{k}', 'Alien_organism/SM_alien_organism_13', xf(x, y, FZ + 60, k * 70))
    place('D_LabTendril', 'Alien_organism/SM_alien_organism_05', xf(-1000, -4150, FZ + H, 180, (1, 1, 0.6)))
    for k, y in enumerate((-5300, -4600)):
        light(f'D_LabLight_{k}', -440, y, FZ + 330, 30.0, 1100.0, LAB_LIGHT)

def chamber():
    clusters = ((-950, -3900, 20), (-950, -3300, 140), (-950, -2650, 260), (80, -3850, 200), (80, -3200, 40),
                (80, -2600, 300), (-600, -2550, 90), (-250, -2560, 180))
    for k, (x, y, yaw) in enumerate(clusters):
        place(f'D_Cluster_{k}', 'Alien_organism/SM_alien_organism_10', xf(x, y, FZ + 372 * 0.9, yaw, (0.9, 0.9, 0.9)))
    # tendrils run along local +Y for ~8 m: hang them by the walls, running along the walls, clear of the walk to C-06
    for k, (x, y, yaw) in enumerate(((-960, -3950, 0), (90, -3950, 0), (-960, -2500, 180), (90, -2500, 180), (-1000, -2480, 90))):
        place(f'D_Tendril_{k}', 'Alien_organism/SM_alien_organism_0' + ('1' if k % 2 else '5'), xf(x, y, FZ + H, yaw, (1, 1, 0.65)))
    for label in [f'D_Tendril_{k}' for k in range(5)] + ['D_LabTendril']:   # tendrils sprawl across the floor: walk through them
        A.call(M.OBJ, 'set_properties', {'instance': {'refPath': A.find(label)['refPath'] + '.StaticMeshComponent0'},
                                         'values': json.dumps({'BodyInstance': {'collisionEnabled': 'NoCollision', 'collisionProfileName': 'NoCollision'}})})
    for k, (x, y) in enumerate(((-438, -3500), (-438, -2800))):
        light(f'D_ChamberLight_{k}', x, y, FZ + 300, 18.0, 900.0, RED)

C06 = (-440.0, -3150.0)   # relief valve: centre of the chamber (was at the tube's end, -660, -6230)

def move_c06():
    # moves the C-06 fixture with its pipe and light, keeping their offsets; re-running is a no-op
    fix = A.find('Fix_D06')
    loc = A.call(M.ACT, 'get_actor_transform', {'actor': fix})['location']
    dx, dy = C06[0] - loc['x'], C06[1] - loc['y']
    for label in ('Fix_D06', 'SectorD_C06_Pipe', 'SectorD_C06_Light'):
        a = A.find(label)
        l = A.call(M.ACT, 'get_actor_transform', {'actor': a})['location']
        A.call(M.ACT, 'set_actor_transform', {'actor': a, 'xform': {'location': {'x': l['x'] + dx, 'y': l['y'] + dy, 'z': l['z']}}})
    # the valve itself was only a thin pipe on a dark floor: the fixture now carries a pressure-canister mesh, standing
    # on the floor (fixture origin = mesh base), so it reads as the thing to log
    # SM_tank is ~9.7 m tall with its pivot 4.95 m above its base: scale to ~2.9 m and lift so the base sits on the floor
    A.call(M.ACT, 'set_actor_transform', {'actor': fix, 'xform': {'location': {'x': C06[0], 'y': C06[1], 'z': FZ + 495 * 0.3},
                                                                  'scale': {'x': 0.3, 'y': 0.3, 'z': 0.3}}})
    A.call(M.OBJ, 'set_properties', {'instance': {'refPath': fix['refPath'] + '.StaticMeshComponent'},
                                     'values': json.dumps({'StaticMesh': {'refPath': '/Game/Scifi_Hideout/Meshes/Generator/SM_tank.SM_tank'}})})

def stretch_postprocess():
    # SectorD_PostProcess ended at y -3800; cover the chamber too (to y -2200)
    a = A.find('SectorD_PostProcess')
    b = A.call(M.ACT, 'get_actor_bounds', {'actor': a})
    if b['max']['y'] >= -2200: return
    t = A.call(M.ACT, 'get_actor_transform', {'actor': a})
    k = (-2200 - b['min']['y']) / (b['max']['y'] - b['min']['y'])
    A.call(M.ACT, 'set_actor_transform', {'actor': a, 'xform': {'location': dict(t['location'], y=t['location']['y'] + (-2200 - b['max']['y']) / 2),
                                                                'scale': dict(t['scale'], y=t['scale']['y'] * k)}})

SCREEN_TEXT = 'ROUTE COMPLETE.\nTHANK YOU, TECHNICIAN.\nPROCEED TO RELIEF VALVE.'

def screen():
    # the facility's last message, on the lab side of the divider, right of the door
    sx, sy, sz = -278.0, Y1 - 60 - 4, FZ + 150
    place('D_Screen', 'Screen/SM_screen_01', xf(sx, sy, sz, 0, (4, 1, 4)))
    t = xf(sx, sy - 6, sz + 84, -90)
    a = A.find('D_ScreenText') or A.call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.TextRenderActor'}, 'name': 'D_ScreenText', 'xform': t})
    A.call(M.ACT, 'set_actor_transform', {'actor': a, 'xform': t})
    A.call(M.SCN, 'set_actor_folder', {'actor': a, 'folder_path': FOLDER})
    print('text', A.call(M.OBJ, 'set_properties', {'instance': {'refPath': a['refPath'] + '.NewTextRenderComponent'}, 'values': json.dumps(
        {'Text': SCREEN_TEXT, 'WorldSize': 16.0, 'HorizontalAlignment': 'EHTA_Center', 'VerticalAlignment': 'EVRTA_TextCenter',
         'TextRenderColor': {'r': 120, 'g': 255, 'b': 150, 'a': 255}})}))
    light('D_ScreenGlow', sx, sy - 80, sz + 84, 6.0, 300.0, {'r': 0.5, 'g': 1.0, 'b': 0.6, 'a': 1.0})


# lab light flicker: BP_RoundManager.FlickerDLab, a 0.15 s looping timer from StartShift; each tick every light tagged
# DLabLight has a 12% chance to drop to near dark. Lights elsewhere are untouched.
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
FLICKER = '''(fn FlickerDLab ()
  (for l (Actor|GetAllActorsWithTag "DLabLight")
    (bind _lc (Utilities|Casting|CastToLightComponent (Actor|GetComponentByClass l "/Script/Engine.LightComponent"))
      (:then
        (Rendering|Components|Light|SetIntensity _lc (select (< (Math|Random|RandomIntegerInRange 0 99) 12) 2.0 30.0)))
      (:CastFailed))))
'''

def flicker():
    import anomaly_build as B
    for k in range(2): A.call(M.ACT, 'add_tag', {'actor': A.find(f'D_LabLight_{k}'), 'tag': 'DLabLight'})
    try: M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': 'FlickerDLab'})
    except Exception as e: print('FlickerDLab exists:', str(e)[:60])
    B.compile_bp(RM)
    print('FlickerDLab ->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':FlickerDLab'}, 'code': FLICKER})[:200])
    s = json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': RM + ':StartShift'}}))['returnValue']
    if 'FlickerDLab' not in s:
        old = '  (Utilities|Time|SetTimerbyFunctionName _self "AttachFlashlight" 0.5)\n'
        assert s.count(old) == 1
        print('StartShift ->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':StartShift'}, 'code': s.replace(old, old +
              '  (Utilities|Time|SetTimerbyFunctionName :Object _self :FunctionName "FlickerDLab" :Time 0.15 :bLooping true)\n')})[:200])
    B.compile_bp(RM)

if __name__ == '__main__':
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    print('shell pieces', shell()); lab(); chamber(); move_c06(); stretch_postprocess(); screen(); flicker(); print('done')
