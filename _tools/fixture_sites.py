"""Anomaly sites on every checklist fixture, now that every fixture has a visible prop (fixture_meshes.py).
Absence (type 0) on a fixture is the audited anomaly; before this only C-03, C-04 and A-02 had one, so the same three
rows kept going missing. Every other fixture gets an Absence site, with minRounds staggered so early shifts draw from
the obvious ones. Two Displacement sites (type 3, moved, not audited) are added on props that now read when moved.
Sites are placed by label, so re-running updates them.
Usage: python _tools/fixture_sites.py   (PIE stopped), then save L_SectorC."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
import build_sector_a as A
SOCK = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C'
LV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
# label: (fixture actor or label, type, minRound, cooldown, offset, note)
SITES = {
    'Anomaly_Absence_C01': ('BP_Fixture_C_0', 0, 3, 3, None, 'Absence: C-01 INLET VALVE goes missing'),
    'Anomaly_Absence_C02': ('BP_Fixture_C_1', 0, 3, 3, None, 'Absence: C-02 FILTRATION SEAL goes missing'),
    'Anomaly_Absence_C05': ('BP_Fixture_C_4', 0, 5, 4, None, 'Absence: C-05 OUTFALL GRATE goes missing'),
    'Anomaly_Absence_B01': ('BP_Fixture_C_5', 0, 3, 3, None, 'Absence: B-01 COOLANT PUMP goes missing'),
    'Anomaly_Absence_B02': ('BP_Fixture_C_6', 0, 4, 3, None, 'Absence: B-02 HEAT EXCHANGER goes missing'),
    'Anomaly_Absence_B03': ('BP_Fixture_C_7', 0, 5, 4, None, 'Absence: B-03 CONDENSER COIL goes missing'),
    'Anomaly_Absence_A01': ('A_Fix01', 0, 4, 3, None, 'Absence: A-01 COMMS DESK is gone from the dome'),
    'Anomaly_Absence_A03': ('A_Fix03', 0, 5, 4, None, 'Absence: A-03 RATION SHELF is gone from the dome'),
    'Anomaly_Displace_C02': ('BP_Fixture_C_1', 3, 4, 3, (0.0, -90.0, 0.0), 'Displacement: C-02 FILTRATION SEAL has shifted'),
    'Anomaly_Displace_B02': ('BP_Fixture_C_6', 3, 5, 4, (0.0, 140.0, 0.0), 'Displacement: B-02 HEAT EXCHANGER has slid along the wall')}

def target(ref):
    return {'refPath': LV + ref} if ref.startswith('BP_') else A.find(ref)

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    for label, (ref, typ, minr, cd, off, note) in SITES.items():
        t = target(ref)
        loc = A.call(M.ACT, 'get_actor_transform', {'actor': t})['location']
        xf = {'location': {'x': loc['x'], 'y': loc['y'], 'z': loc['z'] + 250}, 'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
        a = A.find(label) or A.call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': SOCK}, 'name': label, 'xform': xf})
        A.call(M.ACT, 'set_actor_transform', {'actor': a, 'xform': xf})
        A.call(M.SCN, 'set_actor_folder', {'actor': a, 'folder_path': 'Substrate/Anomalies'})
        vals = {'anomalyType': typ, 'minRound': minr, 'maxRound': 0, 'cooldownRounds': cd, 'revertRule': 0, 'severity': 1.0,
                'note': note, 'targetActor': {'refPath': t['refPath']}}
        if off: vals['offset'] = {'X': off[0], 'Y': off[1], 'Z': off[2]}
        print(label, A.call(M.OBJ, 'set_properties', {'instance': a, 'values': json.dumps(vals)}))
