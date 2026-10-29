"""From round 3, every shift has at least one anomaly the audit checks.
Only a fixture whose FixtureState != 0 changes the audit (TryCloseShift); lights, props and growth are there to be
noticed. A playtest shift 7 came out all PASS because the roll landed only on unaudited sites. After the normal roll,
RollAnomalies now counts anomalous fixtures (CountFixtureAnomalies) and, if there are none, tries Absence (type 0) up
to 4 more times. ApplyOne picks any eligible Absence site, which may be a prop (the dome mug), hence the retries;
if every fixture Absence site is on cooldown the shift simply has none.
Also fixes PickByIndex: after finding the wanted candidate it stopped counting, so every later eligible socket matched
too and overwrote the pick; the director always chose the LAST eligible socket of a type.
Usage: python _tools/guarantee_audited_anomaly.py   (PIE stopped), then save BP_AnomalyDirector."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
D = '/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector'
read = lambda g: json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': D + ':' + g}})).get('returnValue', '')
COUNT = '''(fn CountFixtureAnomalies ()
  (Variables|Default|SetFixAnoms 0)
  (for a (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C")
    (bind _f (Utilities|Casting|CastToBP_Fixture a))
    (if (!= (Class|BPFixture|GetFixtureState _f) 0)
      (Variables|Default|SetFixAnoms (+ (Variables|Default|GetFixAnoms) 1)))))
'''
PICK = '''(fn PickByIndex (TypeCode Round Wanted)
  (Variables|Default|SetScanIndex 0)
  (for _array_element (Variables|Default|GetSockets)
    (bind _s (Utilities|Casting|CastToBP_AnomalySocket _array_element))
    (if (and (== (Class|BPAnomalySocket|GetAnomalyType _s) TypeCode) (Class|BPAnomalySocket|CanApply _s Round))
      (if (== (Variables|Default|GetScanIndex) Wanted)
        (Variables|Default|SetPickSock _s))
      (Variables|Default|SetScanIndex (+ (Variables|Default|GetScanIndex) 1))))
  (return (Variables|Default|GetPickSock)))
'''
GUARANTEE = '''  (if (>= Round 3)
    (for _g (range 4)
      (CallFunction|CountFixtureAnomalies :self _self)
      (if (== (Variables|Default|GetFixAnoms) 0)
        (CallFunction|ApplyOne _self 0 Round))))
'''

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    have = [v['name'] if isinstance(v, dict) else v for v in json.loads(M.bp('list_variables', {'blueprint': {'refPath': D}}))['returnValue']]
    if 'FixAnoms' not in have: B.add_var(D, 'FixAnoms', 'int')
    try: M.bp('add_function_graph', {'blueprint': {'refPath': D}, 'graph_name': 'CountFixtureAnomalies'})
    except Exception as e: print('exists:', str(e)[:60])
    B.compile_bp(D)
    print('Count ->', M.bp('write_graph_dsl', {'graph': {'refPath': D + ':CountFixtureAnomalies'}, 'code': COUNT})[:200])
    B.compile_bp(D)
    before = read('PickByIndex')
    print('PickByIndex ->', M.bp('write_graph_dsl', {'graph': {'refPath': D + ':PickByIndex'}, 'code': PICK})[:200])
    print(''.join(difflib.unified_diff(before.splitlines(True), read('PickByIndex').splitlines(True), 'before', 'after')))
    B.compile_bp(D)
    s = read('RollAnomalies')
    if 'CountFixtureAnomalies' not in s:
        anchor = '  (if (and (== Round 2) (== (Variables|Default|GetAppliedCount) 0))\n'
        assert s.count(anchor) == 1
        new = s.replace(anchor, GUARANTEE + anchor)
        print('RollAnomalies ->', M.bp('write_graph_dsl', {'graph': {'refPath': D + ':RollAnomalies'}, 'code': new})[:200])
        print(''.join(difflib.unified_diff(s.splitlines(True), read('RollAnomalies').splitlines(True), 'before', 'after')))
    B.compile_bp(D)
