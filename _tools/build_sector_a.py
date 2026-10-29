"""Sector A (Habitation / Control), DESIGN.md section 7: the lived-in room where shifts start and end, built from the
Scifi_Hideout kit's dome hut (SM_house, 11 m across, doorways on +Y and -Y). It sits in empty space at ORIGIN, away from
the canal water plane (y < 2910) and above the canal rescue volume (z < -400); airlocks connect it to the route.
Every piece is found by label and re-placed, so re-running moves things instead of duplicating them.
Usage: python _tools/build_sector_a.py   (PIE stopped), then save L_SectorC."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
X, Y, Z = 16000.0, 12000.0, 1000.0   # ORIGIN: dome centre, floor level
KIT = '/Game/Scifi_Hideout/Meshes/'
FOLDER = 'Substrate/SectorA'
# label: (mesh, dx, dy, dz, yaw)
PIECES = {
    'A_House':        ('House_modules/SM_house', 0, 0, 0, 0),
    'A_Floor':        ('Floors/SM_floor_house_circular', 0, 0, 0, 0),
    'A_Console':      ('Console/SM_console', -430, 180, 0, 180),
    'A_Table':        ('Table/SM_table', 150, 0, 0, 90),
    'A_Stool1':       ('Stool/SM_stool', 40, -60, 0, 20),
    'A_Stool2':       ('Stool/SM_stool', 260, 70, 0, -35),
    'A_Jug':          ('Kitchen_props/SM_jug', 140, 40, 77, 0),
    'A_Tray':         ('Kitchen_props/SM_tray', 170, -60, 77, 15),
    'A_CrateA':       ('Crates/SM_crate_01', 380, -320, 0, 70),
    'A_CrateB':       ('Crates/SM_crate_02', 330, -330, 65, 80),
    'A_Lamp':         ('Ceiling_lamps/SM_lamp_02', 0, 0, 560, 0)}
# the comms desk, generator and shelf are checklist fixtures: sector_a_fixtures.py places them
# label: (dx, dy, dz, candelas, radius, colour); main lamp raised 40 -> 70 cd after playtests found the dome too dark
LIGHTS = {
    'A_LightMain':    (0, 0, 480, 70.0, 1500.0, {'r': 1.0, 'g': 0.8, 'b': 0.6, 'a': 1.0}),
    'A_LightConsole': (-330, 100, 180, 14.0, 500.0, {'r': 0.6, 'g': 0.85, 'b': 1.0, 'a': 1.0})}

def call(ts, tool, args):
    r = M.call('call_tool', {'toolset_name': ts, 'tool_name': tool, 'arguments': args})
    try: return json.loads(r).get('returnValue')
    except ValueError: raise RuntimeError(f'{tool} {args.get("name", "")}: {r[:300]}')

def find(label):
    for a in call(M.SCN, 'find_actors', {'name': label, 'tag': '', 'collision_channels': []}) or []:
        if call(M.ACT, 'get_label', {'actor': a}) == label: return a

def xform(dx, dy, dz, yaw=0):
    return {'location': {'x': X + dx, 'y': Y + dy, 'z': Z + dz}, 'rotation': {'pitch': 0, 'yaw': yaw, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}

def place(label, make, xf):
    a = find(label) or make()
    call(M.ACT, 'set_actor_transform', {'actor': a, 'xform': xf})
    call(M.SCN, 'set_actor_folder', {'actor': a, 'folder_path': FOLDER})
    return a

if __name__ == '__main__':
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    for label, (mesh, dx, dy, dz, yaw) in PIECES.items():
        xf = xform(dx, dy, dz, yaw)
        place(label, lambda: call(M.SCN, 'add_to_scene_from_asset', {'asset_path': KIT + mesh, 'name': label, 'xform': xf}), xf)
    for label, (dx, dy, dz, cd, rad, col) in LIGHTS.items():
        xf = xform(dx, dy, dz)
        a = place(label, lambda: call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.PointLight'}, 'name': label, 'xform': xf}), xf)
        call(M.OBJ, 'set_properties', {'instance': {'refPath': a['refPath'] + '.LightComponent0'}, 'values': json.dumps(
            {'Intensity': cd, 'IntensityUnits': 'Candelas', 'AttenuationRadius': rad, 'LightColor': col, 'Mobility': 'Movable'})})
    print('placed', len(PIECES), 'pieces,', len(LIGHTS), 'lights')
