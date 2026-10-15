"""Full Phase 3 Regression Verification Test in PIE."""
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
    if 'true' not in M.app('IsPIERunning', {}):
        print('Starting PIE for regression testing...')
        M.app('StartPIE', {'options': {'bSimulate': False}})
        time.sleep(10)

    pawns = find('/Script/Engine.Character')
    if not pawns:
        sys.exit('Error: no pawn found in PIE')
    pawn = pawns[0]
    rm = find('/Game/Substrate/Core/BP_RoundManager.BP_RoundManager_C')[0]
    director = find('/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector_C')[0]
    fixtures = sorted(find('/Game/Substrate/Core/BP_Fixture.BP_Fixture_C'),
                      key=lambda f: prop(f, 'RowOrder') if prop(f, 'RowOrder') is not None else 99)

    print('=== REGRESSION TEST 1: RESET TO ROUND 1 ===')
    # Set CurrentRound to 1 (Shift 1)
    setp(rm, {'CurrentRound': 1})
    round_val = prop(rm, 'CurrentRound')
    print(f'CurrentRound at start of Shift 1: {round_val}')
    assert round_val == 1, f'Expected Round 1, got {round_val}'

    print('=== REGRESSION TEST 2: ROUND 1 -> ROUND 2 (ABSENCE) -> ROUND 3 (REVERT) ===')
    # Log Round 1
    for f in fixtures:
        state = prop(f, 'FixtureState')
        want = 1 if state == 0 else 2
        setp(f, {'LogResult': want})
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(0.5)
    put(pawn, RM_TRIGGER)
    time.sleep(2.5)

    r2 = prop(rm, 'CurrentRound')
    print(f'Round after closing Shift 1: {r2}')
    assert r2 == 2, f'Expected Round 2, got {r2}'

    # Check Absence Anomaly in Round 2
    absent_fixture = None
    for f in fixtures:
        st = prop(f, 'FixtureState')
        if st == 2:
            absent_fixture = f
            print(f'Found absent fixture in Round 2: {prop(f, "FixtureName")}')
    assert absent_fixture is not None, 'No absent fixture found in Round 2!'

    # Log Round 2 (FLAG absent, PASS nominal)
    for f in fixtures:
        st = prop(f, 'FixtureState')
        want = 1 if st == 0 else 2
        setp(f, {'LogResult': want})
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
    assert reverted_st == 0, f'Expected state 0 (reverted), got {reverted_st}'
    print('PASS: Round 1 -> 3 loop and revert verified!')

    print('=== REGRESSION TEST 3: ROUND 5 PHANTOM ROW C-06 ===')
    # Set to Round 4 and close shift -> Round 5
    setp(rm, {'CurrentRound': 4})
    for f in fixtures:
        st = prop(f, 'FixtureState')
        setp(f, {'LogResult': 1 if st == 0 else 2})
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(0.5)
    put(pawn, RM_TRIGGER)
    time.sleep(2.5)

    r5 = prop(rm, 'CurrentRound')
    print(f'Current Round: {r5}')
    assert r5 == 5, f'Expected Round 5, got {r5}'

    # Verify shift 5 can close without logging C-06
    for f in fixtures:
        st = prop(f, 'FixtureState')
        setp(f, {'LogResult': 1 if st == 0 else 2})
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(0.5)
    put(pawn, RM_TRIGGER)
    time.sleep(2.5)

    r6 = prop(rm, 'CurrentRound')
    print(f'Round after closing Shift 5: {r6}')
    assert r6 == 6, f'Expected Round 6, got {r6}'
    print('PASS: Round 5 Phantom Row did not block shift close!')

    print('=== REGRESSION TEST 4: ROUND 8 -> SECTOR D TELEPORT & BEATS ===')
    setp(rm, {'CurrentRound': 7})
    for f in fixtures:
        st = prop(f, 'FixtureState')
        setp(f, {'LogResult': 1 if st == 0 else 2})
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(0.5)
    put(pawn, RM_TRIGGER)
    time.sleep(2.5)

    r8 = prop(rm, 'CurrentRound')
    print(f'Round: {r8}')
    assert r8 == 8, f'Expected Round 8, got {r8}'

    # Close Round 8 -> calls EnterSectorD
    for f in fixtures:
        st = prop(f, 'FixtureState')
        setp(f, {'LogResult': 1 if st == 0 else 2})
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(0.5)
    put(pawn, RM_TRIGGER)
    time.sleep(3.5)

    # Check pawn location after EnterSectorD
    pawn_tr = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': pawn}}})).get('returnValue', {})
    loc = pawn_tr.get('location', {})
    print(f'Player pawn location in Sector D: {loc}')
    assert loc.get('y', 0) < -7000, f'Expected player teleported to Sector D (y < -7000), got {loc}'

    # Walk player through beats:
    # Beat 1: Y = -7900
    print('Testing Sector D Beat 1 (Y = -7900)...')
    put(pawn, (-660, -7850, 450))
    time.sleep(1.0)
    beat = prop(rm, 'SectorDBeat')
    print(f'SectorDBeat after Y = -7850: {beat}')
    assert beat >= 1, f'Expected SectorDBeat >= 1, got {beat}'

    # Beat 2: Y = -7300
    print('Testing Sector D Beat 2 (Y = -7300)...')
    put(pawn, (-660, -7250, 450))
    time.sleep(1.0)
    beat = prop(rm, 'SectorDBeat')
    print(f'SectorDBeat after Y = -7250: {beat}')
    assert beat >= 2, f'Expected SectorDBeat >= 2, got {beat}'

    # Beat 3: Y = -6700
    print('Testing Sector D Beat 3 (Y = -6700)...')
    put(pawn, (-660, -6650, 450))
    time.sleep(1.0)
    beat = prop(rm, 'SectorDBeat')
    print(f'SectorDBeat after Y = -6650: {beat}')
    assert beat >= 3, f'Expected SectorDBeat >= 3, got {beat}'

    print('\n=============================================')
    print('ALL REGRESSION TESTS PASSED CLEANLY!')
    print('=============================================')

    print('Stopping PIE...')
    M.app('StopPIE', {})

if __name__ == '__main__':
    main()
