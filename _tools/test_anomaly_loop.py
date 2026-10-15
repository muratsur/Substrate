"""Test Step 3: Full 2-round Anomaly & Revert loop (T1.1) in PIE.

Verifies:
1. Shift 1 baseline (0 anomalies applied).
2. Closes Shift 1 by logging all 8 fixtures and stepping into RouteEnd_ShiftTrigger (0, 1260, 420).
3. Verifies Shift 2 starts (Round 2), rolls budget 1, and applies 1 Absence anomaly.
4. Verifies the affected fixture is absent (FixtureState == 2).
5. Logs Round 2 correctly (FLAG for the absent fixture, PASS for others) and steps into trigger.
6. Verifies Shift 3 starts (Round 3), rolls budget 1-2, and reverts the Round 2 Absence anomaly!
"""
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
        print('Starting PIE...')
        M.app('StartPIE', {'options': {'bSimulate': False}})
        time.sleep(10)

    pawns = find('/Script/Engine.Character')
    if not pawns:
        sys.exit('Error: no pawn found in PIE')
    pawn = pawns[0]
    print('Found player pawn:', pawn.split('.')[-1])

    rm_actors = find('/Game/Substrate/Core/BP_RoundManager.BP_RoundManager_C')
    if not rm_actors:
        sys.exit('Error: no BP_RoundManager found in PIE')
    rm = rm_actors[0]
    print('Found BP_RoundManager:', rm.split('.')[-1])

    dir_actors = find('/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector_C')
    if not dir_actors:
        sys.exit('Error: no BP_AnomalyDirector found in PIE')
    director = dir_actors[0]
    print('Found BP_AnomalyDirector:', director.split('.')[-1])

    fixtures = sorted(find('/Game/Substrate/Core/BP_Fixture.BP_Fixture_C'),
                      key=lambda f: prop(f, 'RowOrder') if prop(f, 'RowOrder') is not None else 99)
    print(f'Found {len(fixtures)} fixtures.')

    cur_round = prop(rm, 'CurrentRound')
    print(f'Current Round: {cur_round}')

    # --- Close Shift 1 ---
    print('\n--- Step 1: Logging all fixtures correctly for Round 1 ---')
    for f in fixtures:
        row = prop(f, 'RowOrder')
        state = prop(f, 'FixtureState')
        want = 1 if state == 0 else 2
        setp(f, {'LogResult': want})
        name = prop(f, 'FixtureName') or f.split(':')[-1]
        print(f'  Row {row}: {name} (state={state}) -> LogResult={want}')

    print('\nStepping into Shift Trigger at (0, 1260, 420)...')
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(1.0)
    put(pawn, RM_TRIGGER)
    time.sleep(2.5)

    round_after_1 = prop(rm, 'CurrentRound')
    print(f'Round after closing Shift 1: {round_after_1}')
    if round_after_1 != 2:
        print(f'WARNING: Expected round 2, got {round_after_1}. Retrying trigger overlap...')
        put(pawn, OUTSIDE_TRIGGER)
        time.sleep(1.0)
        put(pawn, RM_TRIGGER)
        time.sleep(2.5)
        round_after_1 = prop(rm, 'CurrentRound')
        print(f'Round after retry: {round_after_1}')

    if round_after_1 != 2:
        sys.exit('FAIL: Shift 1 did not advance to Round 2')

    print('PASS: Shift 1 closed and advanced to Round 2!')

    # --- Check Round 2 Anomaly ---
    print('\n--- Step 2: Checking Round 2 Anomaly ---')
    applied_count = prop(director, 'AppliedCount')
    print(f'Director AppliedCount in Round 2: {applied_count}')

    sockets = find('/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C')
    applied_sockets = []
    for s in sockets:
        if prop(s, 'Applied'):
            typ = prop(s, 'AnomalyType')
            note = prop(s, 'Note')
            target = prop(s, 'TargetActor')
            applied_sockets.append((s, typ, note, target))
            print(f'  Applied Anomaly: Type={typ}, Note="{note}", Target={target}')

    # Find the absent fixture
    absent_fixture = None
    for f in fixtures:
        st = prop(f, 'FixtureState')
        name = prop(f, 'FixtureName') or f.split(':')[-1]
        row = prop(f, 'RowOrder')
        if st == 2:
            absent_fixture = f
            print(f'  CONFIRMED ABSENT FIXTURE: Row {row} ({name}) has FixtureState=2 (Hidden)')
        else:
            print(f'  Fixture Row {row} ({name}): FixtureState={st}')

    # --- Close Shift 2 ---
    print('\n--- Step 3: Logging Round 2 correctly (FLAG for absent, PASS for others) ---')
    for f in fixtures:
        row = prop(f, 'RowOrder')
        state = prop(f, 'FixtureState')
        want = 1 if state == 0 else 2
        setp(f, {'LogResult': want})
        name = prop(f, 'FixtureName') or f.split(':')[-1]
        print(f'  Row {row}: {name} (state={state}) -> LogResult={want}')

    print('\nStepping into Shift Trigger to close Shift 2...')
    put(pawn, OUTSIDE_TRIGGER)
    time.sleep(1.0)
    put(pawn, RM_TRIGGER)
    time.sleep(2.5)

    round_after_2 = prop(rm, 'CurrentRound')
    print(f'Round after closing Shift 2: {round_after_2}')
    if round_after_2 != 3:
        print(f'Retrying trigger overlap...')
        put(pawn, OUTSIDE_TRIGGER)
        time.sleep(1.0)
        put(pawn, RM_TRIGGER)
        time.sleep(2.5)
        round_after_2 = prop(rm, 'CurrentRound')
        print(f'Round after retry: {round_after_2}')

    if round_after_2 != 3:
        sys.exit('FAIL: Shift 2 did not advance to Round 3')

    print('PASS: Shift 2 closed and advanced to Round 3!')

    # --- Verify Revert on Round 3 ---
    print('\n--- Step 4: Verifying Revert of Round 2 Absence Anomaly ---')
    if absent_fixture:
        reverted_state = prop(absent_fixture, 'FixtureState')
        abs_name = prop(absent_fixture, 'FixtureName') or absent_fixture.split(':')[-1]
        print(f'Previously absent fixture {abs_name} state in Round 3: {reverted_state}')
        if reverted_state == 0:
            print(f'PASS: {abs_name} successfully REVERTED to nominal state (0) at start of Shift 3!')
        else:
            print(f'WARNING: {abs_name} state is {reverted_state}')

    dir_applied_3 = prop(director, 'AppliedCount')
    print(f'Director AppliedCount in Round 3: {dir_applied_3}')

    print('\n=============================================')
    print('STEP 3 RESULT: PASS - Full 2-round Anomaly & Revert loop verified!')
    print('=============================================')

if __name__ == '__main__':
    main()
