"""Wall signs at the places players got lost: the dome airlock, the close-shift console, both sewer-side airlocks and
the transit return airlock. TextRenderActors (readable from the direction of their yaw) plus a small light each, in
outliner folder Substrate/Signs; placed by label, so re-running moves them.
Usage: python _tools/signs.py   (PIE stopped), then save L_SectorC."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
import build_sector_a as A
FOLDER = 'Substrate/Signs'
GREEN, AMBER = {'r': 0.4, 'g': 1.0, 'b': 0.5, 'a': 1.0}, {'r': 1.0, 'g': 0.75, 'b': 0.3, 'a': 1.0}
X, Y, Z = A.X, A.Y, A.Z
# label: (text, x, y, z, yaw = direction it is read from, size, light colour)
SIGNS = {   # the dock airlocks stand against a wall on their north side (y 1476): their signs hang on it, read from the south
    'Sign_DomeAirlock':   ('AIRLOCK\nSECTOR C - SEWER', X, Y + 360, Z + 330, -90, 28, GREEN),
    'Sign_DomeConsole':   ('CLOSE SHIFT\nLOG EVERY ROW FIRST', X - 470, Y + 180, Z + 290, 0, 22, AMBER),
    'Sign_DockToDome':    ('AIRLOCK\nSECTOR A - DOME', -300, 1465, 600, -90, 24, GREEN),
    'Sign_DockTransit':   ('AIRLOCK\nSECTOR B - TRANSIT', 300, 1465, 600, -90, 24, AMBER),
    'Sign_TransitReturn': ('AIRLOCK\nDOCK - SECTOR C', 8560, 4380, 640, -90, 24, AMBER)}

def place(label, text, x, y, z, yaw, size, colour):
    t = {'location': {'x': x, 'y': y, 'z': z}, 'rotation': {'pitch': 0, 'yaw': yaw, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
    a = A.find(label) or A.call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.TextRenderActor'}, 'name': label, 'xform': t})
    A.call(M.ACT, 'set_actor_transform', {'actor': a, 'xform': t})
    A.call(M.SCN, 'set_actor_folder', {'actor': a, 'folder_path': FOLDER})
    A.call(M.OBJ, 'set_properties', {'instance': {'refPath': a['refPath'] + '.NewTextRenderComponent'}, 'values': json.dumps(
        {'Text': text, 'WorldSize': float(size), 'HorizontalAlignment': 'EHTA_Center', 'VerticalAlignment': 'EVRTA_TextCenter'})})
    lx, ly = x + 60 * (1 if yaw == 0 else -1 if yaw == 180 else 0), y + 60 * (1 if yaw == 90 else -1 if yaw == -90 else 0)
    lt = {'location': {'x': lx, 'y': ly, 'z': z}, 'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
    l = A.find(label + '_Light') or A.call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.PointLight'}, 'name': label + '_Light', 'xform': lt})
    A.call(M.ACT, 'set_actor_transform', {'actor': l, 'xform': lt})
    A.call(M.SCN, 'set_actor_folder', {'actor': l, 'folder_path': FOLDER})
    A.call(M.OBJ, 'set_properties', {'instance': {'refPath': l['refPath'] + '.LightComponent0'}, 'values': json.dumps(
        {'Intensity': 6.0, 'IntensityUnits': 'Candelas', 'AttenuationRadius': 250.0, 'LightColor': colour, 'Mobility': 'Movable', 'CastShadows': False})})

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    for old in ('Sign_DockToDome_N', 'Sign_DockToDome_N_Light'):   # first layout put this one behind the dock wall
        a = A.find(old)
        if a: A.call(M.SCN, 'remove_from_scene', {'actor': a})
    for label, s in SIGNS.items(): place(label, *s)
    print('placed', len(SIGNS), 'signs')
