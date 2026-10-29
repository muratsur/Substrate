"""Give every sewer/transit checklist fixture a visible prop.
C-01..C-05 and B-01..B-03 were invisible markers under a light (BP_Fixture has no mesh of its own), so there was
nothing to look at, and an Absence anomaly on them (the audited kind, guaranteed every shift from round 3) changed
nothing on screen. Each fixture's own StaticMeshComponent now carries a kit mesh that fits its name, standing on the
floor under its light; Absence hides it, Displacement moves it. Transit props sit against the +X wall so the corridor
stays walkable. Collision is off on these props (profile NoCollision): they are looked at, not walked around.
Usage: python _tools/fixture_meshes.py   (PIE stopped), then save L_SectorC."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
import build_sector_a as A
LV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
# fixture actor: (mesh, scale, base offset = pivot height above the mesh's bottom at scale 1, yaw, dx, dy)
PROPS = {
    'BP_Fixture_C_0': ('/Game/Scifi_Hideout/Meshes/Generator/SM_tank', 0.18, 495, 0, 0, 0),           # C-01 INLET VALVE
    'BP_Fixture_C_1': ('/Game/Scifi_Hideout/Meshes/Vent/SM_vent', 1.5, 61, 0, 0, 0),                  # C-02 FILTRATION SEAL
    'BP_Fixture_C_2': ('/Game/Scifi_Hideout/Meshes/Console/SM_console', 0.7, 0, -90, 0, 0),            # C-03 PRESSURE GAUGE
    'BP_Fixture_C_3': ('/Game/Ice_Station/Meshes/Exterior_lamp/SM_exterior_lamp_01', 0.45, 0, 0, 0, 0),  # C-04 OVERFLOW LAMP
    'BP_Fixture_C_4': ('/Game/Alien_Biomass/Meshes/Lamps/SM_floor_lamp', 1.5, 0, 0, 0, 0),            # C-05 OUTFALL GRATE
    'BP_Fixture_C_5': ('/Game/Ice_Station/Meshes/interior/SM_generator', 0.3, 0, 0, 260, 0),          # B-01 COOLANT PUMP
    'BP_Fixture_C_6': ('/Game/Ice_Station/Meshes/Pipe/SM_pipe_group_03', 0.3, 4, 90, 300, 0),         # B-02 HEAT EXCHANGER
    'BP_Fixture_C_7': ('/Game/Ice_Station/Meshes/Pipe/SM_pipe_group_01', 0.15, 6, 90, 280, 0)}        # B-03 CONDENSER COIL

def trace(a, b):
    return json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'trace_world', 'arguments': {'start': dict(zip('xyz', a)), 'end': dict(zip('xyz', b))}})).get('returnValue')

def apply():
    for ref, (mesh, s, off, yaw, dx, dy) in PROPS.items():
        a = {'refPath': LV + ref}
        smc = {'refPath': LV + ref + '.StaticMeshComponent'}
        loc = A.call(M.ACT, 'get_actor_transform', {'actor': a})['location']
        already = '"None"' not in A.call(M.OBJ, 'get_properties', {'instance': smc, 'properties': ['StaticMesh']})
        if already: print(ref, 'already has a mesh, skipped'); continue   # moved once; re-running must not shift it again
        x, y = loc['x'] + dx, loc['y'] + dy
        d = trace((x, y, loc['z'] + 50), (x, y, loc['z'] - 400))
        floor = loc['z'] + 50 - d if d is not None else loc['z'] - 120
        A.call(M.OBJ, 'set_properties', {'instance': smc, 'values': json.dumps({'StaticMesh': {'refPath': mesh + '.' + mesh.split('/')[-1]},
              'BodyInstance': {'collisionEnabled': 'NoCollision', 'collisionProfileName': 'NoCollision'}})})
        A.call(M.ACT, 'set_actor_transform', {'actor': a, 'xform': {'location': {'x': x, 'y': y, 'z': floor + off * s},
              'rotation': {'pitch': 0, 'yaw': yaw, 'roll': 0}, 'scale': {'x': s, 'y': s, 'z': s}}})
        print(ref, mesh.split('/')[-1], 'floor', round(floor), 'at', round(x), round(y))

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    apply()
