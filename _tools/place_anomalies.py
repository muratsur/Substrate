"""Place BP_AnomalyDirector + BP_AnomalySocket instances in L_SectorC.

Socket authoring table (also the in-level documentation of what each anomaly is):
  name                 type  target                 minR  cd  revert
  Anomaly_Absence_C03  Absence  Fixture C-03 (2)     2    3   EndOfShift
  Anomaly_Light_Dock   Light    RectLight_2          3    3   EndOfShift
  Anomaly_Absence_C04  Absence  Fixture C-04 (3)     4    4   EndOfShift
  Anomaly_Growth_C     Growth   GrowthNode_C_0       5    4   Never
  Anomaly_Displace_C05 Displacement Fixture C-05 (4) 8    5   EndOfShift
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

BASE = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
DIRCLASS = '/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector_C'
SOCKCLASS = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C'

ABS, LIGHT, GROWTH, DISPLACE = 0, 1, 2, 3

SOCKETS = [
    dict(name='Anomaly_Absence_C03', loc=(-2480, 7212, 700), typ=ABS,
         target='BP_Fixture_C_2', minr=2, cd=3, revert=0,
         note='Absence: C-03 PRESSURE GAUGE goes missing (round 2+, the first anomaly)'),
    dict(name='Anomaly_Light_Dock', loc=(1727, 1438, 760), typ=LIGHT,
         target='RectLight_2', minr=3, cd=3, revert=0, intensity=0.0,
         note='Light: the dock rect light dies (round 3+)'),
    dict(name='Anomaly_Absence_C04', loc=(-1516, 8349, 700), typ=ABS,
         target='BP_Fixture_C_3', minr=4, cd=4, revert=0,
         note='Absence: C-04 OVERFLOW LAMP goes missing (round 4+)'),
    dict(name='Anomaly_Growth_C', loc=(2200, 5200, 900), typ=GROWTH,
         target='BP_GrowthNode_C_0', minr=5, cd=4, revert=1,
         note='Growth: Growth_Early jumps a stage while you are not looking (round 5+, permanent)'),
    dict(name='Anomaly_Displace_C05', loc=(-2543, 10200, 800), typ=DISPLACE,
         target='BP_Fixture_C_4', minr=8, cd=5, revert=0, offset=(0, 120, 0),
         note='Displacement: C-05 OUTFALL GRATE slides 1.2 m (round 8+)'),
]


def spawn(actor_type, name, loc):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'add_to_scene_from_class',
                             'arguments': {'actor_type': {'refPath': actor_type}, 'name': name,
                                           'xform': {'location': {'x': loc[0], 'y': loc[1], 'z': loc[2]}}}})
    print(' spawn', name, r[:170])
    try:
        return json.loads(r)['returnValue']['refPath']
    except Exception:
        return None


def setp(ref, values):
    r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties',
                             'arguments': {'instance': {'refPath': ref}, 'values': json.dumps(values)}})
    print('   set', r[:120])


def main():
    M.init()
    refs = []
    d = spawn(DIRCLASS, 'AnomalyDirector', (0, 1600, 500))
    if d:
        M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'set_actor_folder',
                             'arguments': {'actor': {'refPath': d}, 'folder_path': 'Substrate/Anomalies'}})
        refs.append(d)
    for s in SOCKETS:
        ref = spawn(SOCKCLASS, s['name'], s['loc'])
        if not ref:
            continue
        refs.append(ref)
        M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'set_actor_folder',
                             'arguments': {'actor': {'refPath': ref}, 'folder_path': 'Substrate/Anomalies'}})
        vals = {'anomalyType': s['typ'], 'minRound': s['minr'], 'cooldownRounds': s['cd'],
                'revertRule': s['revert'], 'severity': 1.0, 'maxRound': 0, 'note': s['note'],
                'targetActor': {'refPath': BASE + s['target']}}
        if 'intensity' in s:
            vals['lightIntensity'] = s['intensity']
        if 'offset' in s:
            vals['offset'] = {'X': s['offset'][0], 'Y': s['offset'][1], 'Z': s['offset'][2]}
        setp(ref, vals)
    print('verify:')
    for r in refs:
        r2 = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties',
                                  'arguments': {'instance': {'refPath': r},
                                                'properties': ['anomalyType', 'minRound', 'note', 'targetActor']}})
        print('  ', r.split('.')[-1], r2[:230])


if __name__ == '__main__':
    main()
