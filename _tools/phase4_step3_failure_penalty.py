"""Phase 4 Step 3: Diegetic Shift Failure & Audit Penalty Sequence."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

def ensure_fns(bp_path, fns):
    graphs = [g['refPath'] for g in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': bp_path}})).get('returnValue', [])]
    for fn in fns:
        target = f'{bp_path}:{fn}'
        if target not in graphs:
            print(f'Creating function {fn} in {bp_path}...')
            M.bp('add_function_graph', {'blueprint': {'refPath': bp_path}, 'graph_name': fn})

def main():
    M.init()
    print('=== PHASE 4 - STEP 3: DIEGETIC SHIFT FAILURE & AUDIT PENALTY ===')

    # 1. Add variables to BP_RoundManager
    vars_rm = json.loads(M.bp('list_variables', {'blueprint': {'refPath': RM}})).get('returnValue', [])
    if 'AuditMissedAnomaly' not in vars_rm:
        print('Adding AuditMissedAnomaly to BP_RoundManager...')
        M.bp('add_variable', {'blueprint': {'refPath': RM}, 'name': 'AuditMissedAnomaly', 'type_name': 'bool'})
    if 'AuditFalseAlarm' not in vars_rm:
        print('Adding AuditFalseAlarm to BP_RoundManager...')
        M.bp('add_variable', {'blueprint': {'refPath': RM}, 'name': 'AuditFalseAlarm', 'type_name': 'bool'})

    # 2. Ensure functions on BP_RoundManager
    ensure_fns(RM, ['OnShiftAuditFailed', 'FinishAuditFailureReset'])

    # 3. Write OnShiftAuditFailed & FinishAuditFailureReset
    AUDIT_FAILED = '''(fn OnShiftAuditFailed ()
  (Variables|Default|SetShiftOpen false)
  (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Invalid_Action.Invalid_Action" 1.0 0.5)
  (CameraFades|StartCameraFade (Game|GetPlayerCameraManager 0) 0.0 0.5 0.4 "(R=0.900000,G=0.050000,B=0.020000,A=1.000000)" false true)
  (bind reason (select (Variables|Default|GetAuditMissedAnomaly) "AUDIT FAILED: UNREPORTED CONTAMINATION | RESETTING TO SHIFT 001" "AUDIT FAILED: FALSE ALARM PENALTY | RESETTING TO SHIFT 001"))
  (CallFunction|PushTerminal :Header "SHIFT 001 — MANDATORY AUDIT" :Names "" :States "" :Footer reason)
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "FinishAuditFailureReset" :Time 2.0 :bLooping false))
'''

    FINISH_RESET = '''(fn FinishAuditFailureReset ()
  (CameraFades|StopCameraFade (Game|GetPlayerCameraManager 0))
  (CameraFades|StartCameraFade (Game|GetPlayerCameraManager 0) 0.5 0.0 0.8 "(R=0.900000,G=0.050000,B=0.020000,A=1.000000)" false false)
  (CallFunction|ArmGrowth)
  (Variables|Default|SetCurrentRound 0)
  (CallFunction|StartShift))
'''

    print('Writing BP_RoundManager:OnShiftAuditFailed & FinishAuditFailureReset...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:OnShiftAuditFailed'}, 'code': balance(AUDIT_FAILED)})
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:FinishAuditFailureReset'}, 'code': balance(FINISH_RESET)})

    # 4. Update BP_RoundManager:TryCloseShift to diagnose failure and call OnShiftAuditFailed
    TRY_CLOSE = '''(fn TryCloseShift ()
  (if (Variables|Default|GetShiftOpen)
    (Variables|Default|SetAllCorrect true)
    (Variables|Default|SetAuditMissedAnomaly false)
    (Variables|Default|SetAuditFalseAlarm false)
    (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
    (for _array_element _outactors
      (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
      (bind _inrange (Class|BPFixture|InRowRange _asbp_fixture 0 (Variables|Default|GetRequiredRowMax)))
      (bind _correct (Class|BPFixture|IsLoggedCorrectly _asbp_fixture))
      (if (and _inrange (not _correct))
        (Variables|Default|SetAllCorrect false)
        (if (!= (Class|BPFixture|GetFixtureState _asbp_fixture) 0)
          (Variables|Default|SetAuditMissedAnomaly true)
          (else
            (Variables|Default|SetAuditFalseAlarm true)))))
    (if (Variables|Default|GetAllCorrect)
      (CallFunction|RecordDiscoveredAnomalies)
      (if (>= (Variables|Default|GetCurrentRound) 8)
        (CallFunction|EnterSectorD)
        (else
          (CallFunction|StartShift)))
      (else
        (CallFunction|OnShiftAuditFailed)))))
'''

    print('Writing BP_RoundManager:TryCloseShift...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:TryCloseShift'}, 'code': balance(TRY_CLOSE)})

    print('Compiling BP_RoundManager...')
    c_rm = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('  compile BP_RoundManager ->', c_rm)

    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM]}})
    print('Step 3 Diegetic Shift Failure & Audit Penalty successfully implemented and saved!')

if __name__ == '__main__':
    main()
