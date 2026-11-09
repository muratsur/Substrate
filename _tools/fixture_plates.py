"""ID plates over every checklist fixture, so an Absence reads as "plate with nothing under it" instead of an empty
dark corner (playtest 2026-11-08: two missing fixtures, neither noticed). Each plate is a TextRenderActor hung
PLATE_GAP above the top of the fixture's prop, facing the most open direction around it (where the player comes
from). Plates are separate actors, so Absence hides the prop and leaves the plate. C-02 already has its sign
(signs.py). Also re-aims C-02's wall lamp at the vent, which moved off the arch.
Placed by label in folder Substrate/Signs, so re-running moves them.
Usage: python _tools/fixture_plates.py   (PIE stopped), then save L_SectorC."""
import sys, json, math
sys.path.insert(0, '_tools')
import mcpx as M
import build_sector_a as A
import signs
LV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
FIXTURES = [0, 2, 3, 4, 5, 6, 7, 9, 10, 11]   # BP_Fixture_C_n; 1 = C-02 (has its own sign), 8 = C-06 (Sector D ending)
PLATE_GAP, SIZE = 35, 10

def trace(a, b):
    return json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'trace_world', 'arguments': {'start': a, 'end': b}})).get('returnValue')

EYE = 170   # max plate height above the floor; taller props get their plate beside them instead of on top

def prop_box(i, loc, scale):
    """(top z, half width) of the fixture's prop."""
    smc = {'refPath': LV + 'BP_Fixture_C_%d.StaticMeshComponent' % i}
    mesh = json.loads(A.call(M.OBJ, 'get_properties', {'instance': smc, 'properties': ['StaticMesh']}))['StaticMesh']
    b = A.call('editor_toolset.toolsets.static_mesh.StaticMeshTools', 'get_bounds', {'mesh': mesh})
    return loc['z'] + b['max']['z'] * scale, max(b['max']['x'], b['max']['y']) * scale

def open_yaw(loc, z):
    """Yaw of the most open horizontal direction from the fixture: the side the player sees it from."""
    best = (-1, 0)
    for k in range(16):
        a = math.radians(k * 22.5)
        d = trace({'x': loc['x'], 'y': loc['y'], 'z': z}, {'x': loc['x'] + 1500 * math.cos(a), 'y': loc['y'] + 1500 * math.sin(a), 'z': z})
        d = 1500 if d is None else d
        if d > best[0]: best = (d, k * 22.5)
    return best[1]

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    for i in FIXTURES:
        a = {'refPath': LV + 'BP_Fixture_C_%d' % i}
        fid = json.loads(A.call(M.OBJ, 'get_properties', {'instance': a, 'properties': ['FixtureID']}))['FixtureID']
        xf = A.call(M.ACT, 'get_actor_transform', {'actor': a})
        loc, s = xf['location'], xf['scale']['x']
        top, half = prop_box(i, loc, s)
        d = trace({'x': loc['x'], 'y': loc['y'], 'z': loc['z'] + 50}, {'x': loc['x'], 'y': loc['y'], 'z': loc['z'] - 400})
        floor = loc['z'] + 50 - d if d is not None else loc['z']
        x, y, z = loc['x'], loc['y'], top + PLATE_GAP + SIZE
        yaw = open_yaw(loc, min(z, floor + EYE))
        if z - floor > EYE:   # too high to see up close: hang it at eye level beside the prop, on a side with no wall
            z, reach = floor + EYE - 20, half + 40
            for a in (yaw - 90, yaw + 90, yaw):   # reader's right, left, else in front of the prop
                c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
                hit = trace({'x': loc['x'], 'y': loc['y'], 'z': z}, {'x': loc['x'] + (reach + 40) * c, 'y': loc['y'] + (reach + 40) * s_, 'z': z})
                if hit is None or a == yaw: break
            x, y = loc['x'] + reach * c, loc['y'] + reach * s_
        code, name = fid.split(' ', 1)
        # TextRender is read from its +X side; signs.py convention: yaw = the direction it is read from
        signs.place('Plate_' + code.replace('-', ''), code + '\n' + name, x, y, z, yaw, SIZE, signs.AMBER, light=False)
        print(fid, 'plate at', round(x), round(y), round(z), '(%d above floor)' % round(z - floor), 'read from yaw', yaw)
    lamp = A.find('FixtureLamp_Fixture_C2')   # vent is on the wall at (3340, 6340); hang the lamp above it, front (+Y) out of the wall
    A.call(M.ACT, 'set_actor_transform', {'actor': lamp, 'xform': {'location': {'x': 3340, 'y': 6358, 'z': 750},
           'rotation': {'pitch': 0, 'yaw': 180, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
    print('C-02 lamp re-aimed')
