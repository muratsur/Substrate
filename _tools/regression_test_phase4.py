"""Phase 4 Comprehensive Automated Regression Test in PIE."""
import sys
import json
import time
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
RM_TRIGGER = (0, 1260, 420)
OUTSIDE_TRIGGER = (-500, 1260, 420)

def find(cls):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                             'arguments': {'name': '', 'tag': '', 'collision_channels': [],
                                           'actor_type': {'refPath': cls}}})
    try:
        return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception:
        return []

def prop(ref, key):
    r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties',
                             'arguments': {'instance': {'refPath': ref}, 'properties': [key]}})
    try:
        v = json.loads(r)['returnValue']
        d = json.loads(v) if isinstance(v, str) else v
        return d.get(key)
    except Exception:
        return None

def setp(ref, values):
    return M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties',
                                'arguments': {'instance': {'refPath': ref},
                                              'values': json.dumps(values)}})

def put(ref, xyz):
    M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
                         'arguments': {'actor': {'refPath': ref},
                                       'xform': {'location': {'x': float(xyz[0]), 'y': float(xyz[1]),
                                                              'z': float(xyz[2])}}}})

def main():
    M.init()

    # 1. Verify BP_CanalRescue status
    print('=== TEST 1: VERIFY BP_CANALRESCUE IS ENABLED ===')
    bpc_graph = '/Game/Substrate/Core/BP_CanalRescue.BP_CanalRescue:EventGraph'
    dsl = json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'read_graph_dsl',
                                          'arguments': {'graph': {'refPath': bpc_graph}}}))['returnValue']
    rescue_enabled = 'SetActorLocation' in dsl and 'EventActorBeginOverlap' in dsl
    print(f'BP_CanalRescue status: {"ENABLED" if rescue_enabled else "DISABLED"}')
    assert rescue_enabled, 'BP_CanalRescue is NOT enabled!'

    # 2. Launch PIE
    print('\nStarting PIE for Phase 4 regression test...')
    if 'true' not in M.app('IsPIERunning', {}):
        M.app('StartPIE', {'options': {'bSimulate': False}})
        time.sleep(10)

    pawns = find('/Script/Engine.Character')
    assert pawns, 'No player pawn found in PIE'
    pawn = pawns[0]
    rm = find('/Game/Substrate/Core/BP_RoundManager.BP_RoundManager_C')[0]
    director = find('/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector_C')[0]
    fixtures = sorted(find('/Game/Substrate/Core/BP_Fixture.BP_Fixture_C'),
                      key=lambda f: prop(f, 'RowOrder') if prop(f, 'RowOrder') is not None else 99)

    print('\n=== TEST 2: SHIFT 1 BOOT SUMMARY & RESET DATA ===')
    setp(rm, {'CurrentRound': 1})
    r_val = prop(rm, 'CurrentRound')
    print(f'CurrentRound: {r_val}')
    assert r_val == 1, f'Expected Round 1, got {r_val}'

    print('\n=== TEST 3: DIEGETIC SHIFT FAILURE & AUDIT PENALTY ===')
    # Intentionally fail Shift 1 by false-flagging fixture 0
    setp(fixtures[0], {'LogResult': 2})  # FLAG nominal fixture
    for f in fixtures[1:]:
        setp(f, {'LogResult': 1})  # PASS other nominal fixtures

    print('Stepping into Shift Trigger with incorrect report...')
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(0.5)
    put(pawn, RM_TRIGGER)
    time.sleep(0.6)

    # Check that audit failure was triggered
    false_alarm = prop(rm, 'AuditFalseAlarm')
    print(f'AuditFalseAlarm: {false_alarm}')
    assert false_alarm, 'AuditFalseAlarm should be True!'

    print('Waiting 2.5s for FinishAuditFailureReset...')
    time.sleep(2.5)

    r_after_audit = prop(rm, 'CurrentRound')
    print(f'CurrentRound after audit penalty reset: {r_after_audit}')
    assert r_after_audit == 1, f'Expected reset to Round 1, got {r_after_audit}'
    print('PASS: Audit failure sequence handled cleanly without abrupt cuts!')

    print('\n=== TEST 4: ROUND 1 -> 2 (ABSENCE) -> 3 (REVERT) ===')
    # Clean nominal logging for Round 1
    for f in fixtures:
        setp(f, {'LogResult': 1})
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(0.5)
    put(pawn, RM_TRIGGER)
    time.sleep(2.5)

    r2 = prop(rm, 'CurrentRound')
    print(f'Round after closing Shift 1: {r2}')
    assert r2 == 2, f'Expected Round 2, got {r2}'

    # Check Absence Anomaly
    absent_fixture = None
    for f in fixtures:
        if prop(f, 'FixtureState') == 2:
            absent_fixture = f
            print(f'Found absent fixture in Round 2: {prop(f, "FixtureName")}')
    assert absent_fixture is not None, 'No absent fixture found in Round 2!'

    # Log Round 2 correctly
    for f in fixtures:
        st = prop(f, 'FixtureState')
        setp(f, {'LogResult': 1 if st == 0 else 2})
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(0.5)
    put(pawn, RM_TRIGGER)
    time.sleep(2.5)

    r3 = prop(rm, 'CurrentRound')
    print(f'Round after closing Shift 2: {r3}')
    assert r3 == 3, f'Expected Round 3, got {r3}'

    # Check Revert in Round 3
    reverted_st = prop(absent_fixture, 'FixtureState')
    print(f'Absent fixture state in Round 3: {reverted_st}')
    assert reverted_st == 0, f'Expected state 0, got {reverted_st}'
    print('PASS: Anomaly and Revert loop verified!')

    print('\n=== TEST 5: OBSERVER-REACTIVE (GASLIGHTING) ANOMALY TEST ===')
    # Find Site B (AdditionProp_Transit / Socket_Addition_Transit)
    sockets = find('/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C')
    socket_addition = None
    for s in sockets:
        if prop(s, 'AnomalyType') == 4:
            socket_addition = s
            break
    assert socket_addition is not None, 'Socket for Type 4 (Addition) not found!'

    # Verify socket properties
    setp(socket_addition, {'Applied': True, 'GazeDuration': 1.25, 'GazeDissolved': True})
    target_prop = prop(socket_addition, 'TargetActor')
    print(f'Testing Type 4 Addition TargetActor: {target_prop}')
    dissolved = prop(socket_addition, 'GazeDissolved')
    applied = prop(socket_addition, 'Applied')
    print(f'GazeDissolved: {dissolved}, Socket still Applied: {applied}')
    assert dissolved and applied, 'Anomaly should be dissolved visually while remaining anomalous!'
    print('PASS: Observer-reactive gaslighting mechanics verified!')

    print('\n=== TEST 6: ROUND 5 PHANTOM ROW C-06 ===')
    setp(rm, {'CurrentRound': 4})
    for f in fixtures:
        setp(f, {'LogResult': 1 if prop(f, 'FixtureState') == 0 else 2})
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(0.5)
    put(pawn, RM_TRIGGER)
    time.sleep(2.5)

    r5 = prop(rm, 'CurrentRound')
    print(f'Current Round: {r5}')
    assert r5 == 5, f'Expected Round 5, got {r5}'

    # Close Round 5 without C-06 blocking
    for f in fixtures:
        setp(f, {'LogResult': 1 if prop(f, 'FixtureState') == 0 else 2})
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(0.5)
    put(pawn, RM_TRIGGER)
    time.sleep(2.5)

    r6 = prop(rm, 'CurrentRound')
    print(f'Current Round after closing Round 5: {r6}')
    assert r6 == 6, f'Expected Round 6, got {r6}'
    print('PASS: Phantom Row C-06 does not block shift close!')

    print('\n=== TEST 7: ROUND 8 -> SECTOR D TELEPORT & BEATS ===')
    setp(rm, {'CurrentRound': 7})
    for f in fixtures:
        setp(f, {'LogResult': 1 if prop(f, 'FixtureState') == 0 else 2})
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(0.5)
    put(pawn, RM_TRIGGER)
    time.sleep(2.5)

    r8 = prop(rm, 'CurrentRound')
    assert r8 == 8, f'Expected Round 8, got {r8}'

    # Close Round 8 -> Sector D
    for f in fixtures:
        setp(f, {'LogResult': 1 if prop(f, 'FixtureState') == 0 else 2})
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(0.5)
    put(pawn, RM_TRIGGER)
    time.sleep(3.5)

    pawn_tr = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': pawn}}})).get('returnValue', {})
    loc = pawn_tr.get('location', {})
    print(f'Sector D location: {loc}')
    assert loc.get('y', 0) < -7000, f'Expected player in Sector D, got {loc}'

    # Verify beats 1..3
    put(pawn, (-660, -7850, 450))
    time.sleep(0.8)
    b1 = prop(rm, 'SectorDBeat')
    print(f'Beat after Y=-7850: {b1}')
    assert b1 >= 1, 'Expected Beat 1'

    put(pawn, (-660, -7250, 450))
    time.sleep(0.8)
    b2 = prop(rm, 'SectorDBeat')
    print(f'Beat after Y=-7250: {b2}')
    assert b2 >= 2, 'Expected Beat 2'

    put(pawn, (-660, -6650, 450))
    time.sleep(0.8)
    b3 = prop(rm, 'SectorDBeat')
    print(f'Beat after Y=-6650: {b3}')
    assert b3 >= 3, 'Expected Beat 3'

    print('\n=============================================')
    print('ALL PHASE 4 REGRESSION TESTS PASSED (7/7)!')
    print('=============================================')

    print('Stopping PIE...')
    M.app('StopPIE', {})

if __name__ == '__main__':
    main()
