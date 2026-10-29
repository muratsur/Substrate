"""More Light anomaly sites on the route: the lamps over C-01, C-02, C-05 and the three transit lights can die (type 1,
intensity 0). Before, the only Light sites were the dock rect light and the dome lamp, so the director kept landing
Light anomalies in the same two places; with the PickByIndex fix these now spread across the route.
Light anomalies are not audited (only fixture Absence is); they are there to be noticed.
Usage: python _tools/light_sites.py   (PIE stopped), then save L_SectorC."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
import build_sector_a as A
SOCK = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C'
# socket label: (target label, minRound, cooldown, note)
SITES = {
    'Anomaly_Light_C01Lamp':  ('FixtureLamp_Fixture_C1', 3, 3, 'Light: the lamp over C-01 INLET VALVE is dead'),
    'Anomaly_Light_C02Lamp':  ('FixtureLamp_Fixture_C2', 3, 3, 'Light: the lamp over C-02 FILTRATION SEAL is dead'),
    'Anomaly_Light_C05Lamp':  ('FixtureLamp_Fixture_C5', 4, 3, 'Light: the lamp over C-05 OUTFALL GRATE is dead'),
    'Anomaly_Light_Transit1': ('TransitLight_1', 4, 3, 'Light: the transit light over B-01 is dead'),
    'Anomaly_Light_Transit2': ('TransitLight_2', 4, 3, 'Light: the transit light over B-02 is dead'),
    'Anomaly_Light_Transit3': ('TransitLight_3', 5, 3, 'Light: the transit light over B-03 is dead')}

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    for label, (target, minr, cd, note) in SITES.items():
        t = A.find(target)
        assert t, target
        loc = A.call(M.ACT, 'get_actor_transform', {'actor': t})['location']
        xf = {'location': {'x': loc['x'], 'y': loc['y'], 'z': loc['z'] - 100}, 'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
        a = A.find(label) or A.call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': SOCK}, 'name': label, 'xform': xf})
        A.call(M.ACT, 'set_actor_transform', {'actor': a, 'xform': xf})
        A.call(M.SCN, 'set_actor_folder', {'actor': a, 'folder_path': 'Substrate/Anomalies'})
        print(label, A.call(M.OBJ, 'set_properties', {'instance': a, 'values': json.dumps(
            {'anomalyType': 1, 'minRound': minr, 'maxRound': 0, 'cooldownRounds': cd, 'revertRule': 0, 'severity': 1.0,
             'lightIntensity': 0.0, 'note': note, 'targetActor': {'refPath': t['refPath']}})}))
