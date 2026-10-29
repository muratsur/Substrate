"""Sector A step 2: checklist fixtures, anomaly sites and room tone in the dome (SECTOR_A.md).
- A-01..A-03 are BP_Fixture actors on rows 9-11 that carry the prop's mesh themselves (fixtures are otherwise invisible
  markers), so an Absence on them hides the actual console / generator / shelf. They replace the plain props of the
  same name from build_sector_a.py.
- RequiredRowMax 7 -> 11, so the shift needs them. C-06 (the end-of-demo phantom row) moves 8 -> 20 so it stays out of
  the required range; LogLookedAtFixture's "row 8 ends the demo" check moves with it.
- Anomaly sites: generator missing (audited, it is a fixture), stool moved, mug gone, lamp dead, an extra mug.
  Only fixture Absences change the audit; the rest are there to be noticed.
- A_RoomTone: the generator hum (AMB_RoomTone_Hum), attenuated to the dome.
Usage: python _tools/sector_a_fixtures.py   (PIE stopped), then save L_SectorC + BP_RoundManager."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
import build_sector_a as A
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
LV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
FX = '/Game/Substrate/Core/BP_Fixture.BP_Fixture_C'
SOCK = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C'
PHANTOM_ROW = 20
# label: (FixtureID, row, mesh, dx, dy, yaw, replaces)
FIXTURES = {
    'A_Fix01': ('A-01 COMMS DESK', 9, 'Small_console/SM_small_console', -430, -150, 90, 'A_SmallConsole'),
    'A_Fix02': ('A-02 GENERATOR', 10, 'Generator/SM_Generator', -380, -380, 0, 'A_Generator'),
    'A_Fix03': ('A-03 RATION SHELF', 11, 'Furniture/SM_furniture_01', 420, 260, 90, 'A_Shelf')}
# label: (type, target label, minRound, cooldown, extra props, note)
SOCKETS = {
    'Anomaly_A_GeneratorGone': (0, 'A_Fix02', 3, 3, {}, 'Absence: A-02 GENERATOR is gone from the dome'),
    'Anomaly_A_StoolMoved':    (3, 'A_Stool1', 3, 2, {'offset': {'X': 0.0, 'Y': 70.0, 'Z': 0.0}}, 'Displacement: a dome stool has moved'),
    'Anomaly_A_MugGone':       (0, 'A_Jug', 3, 3, {}, 'Absence: the mug is gone from the table'),
    'Anomaly_A_LampDead':      (1, 'A_LightMain', 4, 4, {'lightIntensity': 0.0}, 'Light: the dome lamp is dead'),
    'Anomaly_A_ExtraMug':      (4, 'A_Jug2', 5, 4, {}, 'Addition: a second mug on the table')}

def call(ts, tool, args): return A.call(ts, tool, args)
def setp(a, vals): return call(M.OBJ, 'set_properties', {'instance': a, 'values': json.dumps(vals)})
def rm_read(g): return json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': RM + ':' + g}})).get('returnValue', '')

def rows():
    setp({'refPath': LV + 'BP_Fixture_C_8'}, {'RowOrder': PHANTOM_ROW})   # C-06 RELIEF VALVE
    setp({'refPath': LV + 'BP_RoundManager_C_1'}, {'RequiredRowMax': 11})
    s = rm_read('LogLookedAtFixture')
    old = '(== (Class|BPFixture|GetRowOrder _bestfixture) 8)'
    if old in s:
        new = s.replace(old, f'(== (Class|BPFixture|GetRowOrder _bestfixture) {PHANTOM_ROW})').replace(   # read-back is positional
            '(CallFunction|ShowHint "NOTHING IN RANGE', '(CallFunction|ShowHint :Text "NOTHING IN RANGE')
        print('LogLookedAtFixture ->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':LogLookedAtFixture'}, 'code': new})[:200])
        print(''.join(difflib.unified_diff(s.splitlines(True), rm_read('LogLookedAtFixture').splitlines(True), 'before', 'after')))
    B.compile_bp(RM)

def fixtures():
    for label, (fid, row, mesh, dx, dy, yaw, replaces) in FIXTURES.items():
        old = A.find(replaces)
        if old: call(M.SCN, 'remove_from_scene', {'actor': old})
        xf = A.xform(dx, dy, 0, yaw)
        a = A.place(label, lambda: call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': FX}, 'name': label, 'xform': xf}), xf)
        print(label, setp(a, {'FixtureID': fid, 'RowOrder': row, 'FixtureState': 0}),
              setp({'refPath': a['refPath'] + '.StaticMeshComponent'}, {'StaticMesh': {'refPath': A.KIT + mesh + '.' + mesh.split('/')[-1]}}))

def extra_mug():
    xf = A.xform(110, -20, 77, 40)
    a = A.place('A_Jug2', lambda: call(M.SCN, 'add_to_scene_from_asset', {'asset_path': A.KIT + 'Kitchen_props/SM_jug', 'name': 'A_Jug2', 'xform': xf}), xf)
    setp(a, {'bHidden': True})   # the Addition anomaly unhides it

def sockets():
    for label, (typ, target, minr, cd, extra, note) in SOCKETS.items():
        t = A.find(target)
        assert t, target
        loc = call(M.ACT, 'get_actor_transform', {'actor': t})['location']
        xf = {'location': {'x': loc['x'], 'y': loc['y'], 'z': loc['z'] + 150}, 'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
        a = A.place(label, lambda: call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': SOCK}, 'name': label, 'xform': xf}), xf)
        print(label, setp(a, dict({'anomalyType': typ, 'minRound': minr, 'maxRound': 0, 'cooldownRounds': cd, 'revertRule': 0,
                                   'severity': 1.0, 'note': note, 'targetActor': {'refPath': t['refPath']}}, **extra)))

def room_tone():
    xf = A.xform(-380, -380, 120)
    a = A.place('A_RoomTone', lambda: call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.AmbientSound'}, 'name': 'A_RoomTone', 'xform': xf}), xf)
    ac = {'refPath': a['refPath'] + '.AudioComponent0'}
    print('room tone', setp(ac, {'Sound': {'refPath': '/Game/Substrate/Audio/AMB_RoomTone_Hum.AMB_RoomTone_Hum'}, 'VolumeMultiplier': 0.5, 'bOverrideAttenuation': True}),
          setp(ac, {'AttenuationOverrides': '(bAttenuate=True,bSpatialize=True,FalloffDistance=900.0,AttenuationShapeExtents=(X=500.0,Y=0.0,Z=0.0))'}))

if __name__ == '__main__':
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    rows(); fixtures(); extra_mug(); sockets(); room_tone()
