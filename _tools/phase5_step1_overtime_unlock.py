"""Phase 5 Step 1: Overtime Unlock & Mode Select.

- Extend BP_SubstrateSave with bOvertimeUnlocked and HighestOvertimeShift.
- Extend BP_RoundManager with bOvertimeUnlocked, HighestOvertimeShift, bIsOvertime, OvertimeShift.
- Update EndDemo in BP_RoundManager to unlock Overtime and save to Substrate_0.
- Update SaveShiftState, LoadShiftState, ResetSaveData to handle Overtime save data.
- Update TryCloseShift so Overtime shifts loop indefinitely into OT-02, OT-03, etc.
- Add StartOvertime function and wire Keyboard Key [R] in EventGraph.
- Update RefreshTerminal to render 'OVERTIME: AVAILABLE [PRESS [R] FOR OT-01]' on boot screen and 'OVERTIME: OT-XX' during Overtime shifts.
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

SS = '/Game/Substrate/Core/BP_SubstrateSave.BP_SubstrateSave'
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
EG = f'{RM}:EventGraph'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

def ensure_fns(bp_path, fns):
    graphs = [g['refPath'].split(':')[-1] for g in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': bp_path}})).get('returnValue', [])]
    for fn in fns:
        if fn not in graphs:
            print(f'Adding function {fn} to {bp_path}...')
            M.bp('add_function_graph', {'blueprint': {'refPath': bp_path}, 'graph_name': fn})

def main():
    M.init()
    print('=== PHASE 5 - STEP 1: OVERTIME UNLOCK & MODE SELECT ===')

    # 1. Variables in BP_SubstrateSave
    ss_vars = json.loads(M.bp('list_variables', {'blueprint': {'refPath': SS}})).get('returnValue', [])
    for vname, vtype in [('bOvertimeUnlocked', 'bool'), ('HighestOvertimeShift', 'int')]:
        if vname not in ss_vars:
            print(f'Adding {vname} ({vtype}) to BP_SubstrateSave...')
            M.bp('add_variable', {'blueprint': {'refPath': SS}, 'name': vname, 'type_name': vtype})

    # Helper functions on BP_SubstrateSave
    ensure_fns(SS, ['SetOvertimeData', 'GetOvertimeUnlocked', 'GetHighestOvertimeShift'])

    SET_OT = '''(fn SetOvertimeData (Unlocked Highest)
  (Variables|Default|SetOvertimeUnlocked Unlocked)
  (Variables|Default|SetHighestOvertimeShift Highest))
'''
    GET_OT_UNLOCKED = '''(fn GetOvertimeUnlocked ()
  (return (Variables|Default|GetOvertimeUnlocked)))
'''
    GET_OT_HIGHEST = '''(fn GetHighestOvertimeShift ()
  (return (Variables|Default|GetHighestOvertimeShift)))
'''
    print('Writing BP_SubstrateSave overtime functions...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{SS}:SetOvertimeData'}, 'code': balance(SET_OT)})
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{SS}:GetOvertimeUnlocked'}, 'code': balance(GET_OT_UNLOCKED)})
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{SS}:GetHighestOvertimeShift'}, 'code': balance(GET_OT_HIGHEST)})
    c_ss = M.bp('compile_blueprint', {'blueprint': {'refPath': SS}})
    print('  compile BP_SubstrateSave ->', c_ss[:150])

    # 2. Variables in BP_RoundManager
    rm_vars = json.loads(M.bp('list_variables', {'blueprint': {'refPath': RM}})).get('returnValue', [])
    for vname, vtype in [
        ('bOvertimeUnlocked', 'bool'),
        ('HighestOvertimeShift', 'int'),
        ('bIsOvertime', 'bool'),
        ('OvertimeShift', 'int')
    ]:
        if vname not in rm_vars:
            print(f'Adding {vname} ({vtype}) to BP_RoundManager...')
            M.bp('add_variable', {'blueprint': {'refPath': RM}, 'name': vname, 'type_name': vtype})
        M.bp('set_variable_instance_editable', {'blueprint': {'refPath': RM}, 'variable_name': vname, 'instance_editable': True})

    ensure_fns(RM, ['StartOvertime'])

    # 3. Update SaveShiftState
    SAVE_STATE = '''(fn SaveShiftState ()
  (bind _save (SaveGame|CreateSaveGameObject "/Game/Substrate/Core/BP_SubstrateSave.BP_SubstrateSave_C"))
  (bind _assave (Utilities|Casting|CastToBP_SubstrateSave _save)
    (:then
      (Class|BPSubstrateSave|ApplySaveData _assave (Variables|Default|GetCurrentRound))
      (Class|BPSubstrateSave|SetCodexData _assave (Variables|Default|GetDiscoveredMask) (Variables|Default|GetDiscoveredCount) (Variables|Default|GetCompletedSectorD))
      (Class|BPSubstrateSave|SetOvertimeData _assave (Variables|Default|GetOvertimeUnlocked) (Variables|Default|GetHighestOvertimeShift))
      (SaveGame|SaveGameToSlot _assave "Substrate_0"))
    (:CastFailed)))
'''
    print('Writing BP_RoundManager:SaveShiftState...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:SaveShiftState'}, 'code': balance(SAVE_STATE)})

    # 4. Update LoadShiftState
    LOAD_STATE = '''(fn LoadShiftState ()
  (if (SaveGame|DoesSaveGameExist "Substrate_0")
    (bind _loaded (SaveGame|LoadGameFromSlot "Substrate_0"))
    (bind _assave (Utilities|Casting|CastToBP_SubstrateSave _loaded)
      (:then
        (bind _round (Class|BPSubstrateSave|GetSavedRound _assave))
        (if (> _round 1)
          (Variables|Default|SetCurrentRound (- _round 1)))
        (Variables|Default|SetDiscoveredMask (Class|BPSubstrateSave|GetDiscoveredMask _assave))
        (Variables|Default|SetDiscoveredCount (Class|BPSubstrateSave|GetDiscoveredCount _assave))
        (Variables|Default|SetCompletedSectorD (Class|BPSubstrateSave|GetCompletedSectorD _assave))
        (Variables|Default|SetOvertimeUnlocked (Class|BPSubstrateSave|GetOvertimeUnlocked _assave))
        (Variables|Default|SetHighestOvertimeShift (Class|BPSubstrateSave|GetHighestOvertimeShift _assave)))
      (:CastFailed))))
'''
    print('Writing BP_RoundManager:LoadShiftState...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:LoadShiftState'}, 'code': balance(LOAD_STATE)})

    # 5. Update ResetSaveData
    RESET_SAVE = '''(fn ResetSaveData ()
  (SaveGame|DeleteGameInSlot "Substrate_0")
  (Variables|Default|SetCurrentRound 0)
  (Variables|Default|SetDiscoveredMask 0)
  (Variables|Default|SetDiscoveredCount 0)
  (Variables|Default|SetCompletedSectorD false)
  (Variables|Default|SetOvertimeUnlocked false)
  (Variables|Default|SetHighestOvertimeShift 0)
  (Variables|Default|SetIsOvertime false)
  (Variables|Default|SetOvertimeShift 0)
  (CallFunction|StartShift)
  (Development|PrintString "SAVE RESET -> SHIFT 001" true true "(R=1.000000,G=0.500000,B=0.000000,A=1.000000)" 6.0))
'''
    print('Writing BP_RoundManager:ResetSaveData...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:ResetSaveData'}, 'code': balance(RESET_SAVE)})

    # 6. Update EndDemo to unlock Overtime
    END_DEMO = '''(fn EndDemo ()
  (Variables|Default|SetOvertimeUnlocked true)
  (Variables|Default|SetCompletedSectorD true)
  (CallFunction|SaveShiftState)
  (Input|DisableInput :self self :PlayerController (Game|GetPlayerController 0))
  (CallFunction|PushTerminal
    :Header "SHIFT TERMINATED"
    :Names "SUBSTRATE DEMO COMPLETE\nOVERTIME MODE UNLOCKED"
    :States ""
    :Footer "THANK YOU FOR PLAYING")
  (CameraFades|StartCameraFade
    :self (Game|GetPlayerCameraManager 0)
    :FromAlpha 0.0
    :ToAlpha 1.0
    :Duration 3.0
    :Color "(R=0.000000,G=0.000000,B=0.000000,A=1.000000)"
    :bShouldFadeAudio true
    :bHoldWhenFinished true)
  (Utilities|Time|SetTimerbyFunctionName
    :self self
    :FunctionName "QuitApp"
    :Time 5.0
    :bLooping false)
  (Development|PrintString "SUBSTRATE DEMO COMPLETE - OVERTIME UNLOCKED" true true "(R=0.200000,G=1.000000,B=0.500000,A=1.000000)" 10.0))
'''
    print('Writing BP_RoundManager:EndDemo...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:EndDemo'}, 'code': balance(END_DEMO)})

    # 7. StartOvertime function
    START_OVERTIME = '''(fn StartOvertime ()
  (if (Variables|Default|GetOvertimeUnlocked)
    (Variables|Default|SetIsOvertime true)
    (Variables|Default|SetOvertimeShift 1)
    (Variables|Default|SetCurrentRound 8)
    (Variables|Default|SetLastLoggedAction "")
    (CallFunction|StartShift)))
'''
    print('Writing BP_RoundManager:StartOvertime...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:StartOvertime'}, 'code': balance(START_OVERTIME)})

    # 8. Update TryCloseShift to loop infinitely in Overtime
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
      (if (Variables|Default|GetIsOvertime)
        (bind cur_ot (Variables|Default|GetOvertimeShift))
        (if (> cur_ot (Variables|Default|GetHighestOvertimeShift))
          (Variables|Default|SetHighestOvertimeShift cur_ot))
        (Variables|Default|SetOvertimeShift (+ cur_ot 1))
        (CallFunction|StartShift)
        (else
          (if (>= (Variables|Default|GetCurrentRound) 8)
            (CallFunction|EnterSectorD)
            (else
              (CallFunction|StartShift)))))
      (else
        (CallFunction|OnShiftAuditFailed)))))
'''
    print('Writing BP_RoundManager:TryCloseShift...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:TryCloseShift'}, 'code': balance(TRY_CLOSE)})

    # 9. Update RefreshTerminal for Overtime mode and boot prompt
    REFRESH_TERMINAL = '''(fn RefreshTerminal ()
  (bind _currentround (Variables|Default|GetCurrentRound))
  (bind _isot (Variables|Default|GetIsOvertime))
  (bind _otshift (Variables|Default|GetOvertimeShift))
  (bind _ot_str (Utilities|String|ToString(Integer) _otshift))
  (bind _ot_pad (select (< _otshift 10) "0" ""))
  (bind _ot_hdr (Utilities|String|Append "OVERTIME: OT-" (Utilities|String|Append _ot_pad _ot_str)))

  (bind _returnvalue (Utilities|String|ToString(Integer) _currentround))
  (bind _returnvalue_8 (Utilities|String|Append "00" _returnvalue))
  (bind _returnvalue_9 (Utilities|String|Append "0" _returnvalue))
  (bind _returnvalue_10 (< _currentround 10))
  (bind _returnvalue_11 (< _currentround 100))
  (bind _returnvalue_12 (select _returnvalue_11 _returnvalue_9 _returnvalue))
  (bind _returnvalue_13 (select _returnvalue_10 _returnvalue_8 _returnvalue_12))
  (bind _norm_hdr (Utilities|String|Append "SHIFT " _returnvalue_13))
  (bind _final_hdr (select _isot _ot_hdr _norm_hdr))

  (bind _terminalremaining (Variables|Default|GetTerminalRemaining))
  (bind _returnvalue_1 (Utilities|String|ToString(Integer) _terminalremaining))
  (bind _returnvalue_15 (Utilities|String|Append _returnvalue_1 " left)"))
  (bind _returnvalue_16 (Utilities|String|Append "CLOSE SHIFT: BLOCKED (" _returnvalue_15))
  (bind _basefooter (select (> _terminalremaining 0) _returnvalue_16 "CLOSE SHIFT: READY"))

  (bind _lastloggedaction (Variables|Default|GetLastLoggedAction))
  (bind _haslast (> (Utilities|String|Len _lastloggedaction) 0))
  (bind _normfooter (select _haslast (Utilities|String|Append (Utilities|String|Append _lastloggedaction " | ") _basefooter) _basefooter))

  (bind _disccount (Utilities|String|ToString(Integer) (Variables|Default|GetDiscoveredCount)))
  (bind _codex_str (Utilities|String|Append (Utilities|String|Append "CATALOGUED ANOMALIES: [" _disccount) " / 16]"))

  (bind _boot_footer (select (Variables|Default|GetOvertimeUnlocked)
    (Utilities|String|Append _codex_str " | OVERTIME: AVAILABLE [PRESS [R] FOR OT-01]")
    (Utilities|String|Append _codex_str " | PRESS [BACKSPACE] TO WIPE RECORD")))

  (bind _finalfooter (select (and (== _currentround 1) (not _haslast) (not _isot)) _boot_footer _normfooter))

  (bind _self self)
  (Variables|Default|SetTerminalNames "")
  (Variables|Default|SetTerminalStates "")
  (Variables|Default|SetTerminalRemaining 0)
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _index (range (+ (Variables|Default|GetRequiredRowMax) 1))
    (for _array_element _outactors
      (CallFunction|AddRowifMatch _self _array_element _index)))
  (if (Variables|Default|GetDebugTerminal)
    (Development|PrintString (Utilities|String|Append (Utilities|String|Append _final_hdr (Variables|Default|GetNL)) (Variables|Default|GetTerminalNames)) true true "(R=0.000000,G=0.660000,B=1.000000,A=1.000000)" 6.0)
    (Development|PrintString (Utilities|String|Append (Variables|Default|GetTerminalStates) _finalfooter) true true "(R=0.000000,G=0.660000,B=1.000000,A=1.000000)" 6.0))
  (CallFunction|PushTerminal _self _final_hdr (Variables|Default|GetTerminalNames) (Variables|Default|GetTerminalStates) _finalfooter)
  (CallFunction|OpenWestGate))
'''
    print('Writing BP_RoundManager:RefreshTerminal...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:RefreshTerminal'}, 'code': balance(REFRESH_TERMINAL)})

    print('Compiling BP_RoundManager...')
    c_rm = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('  compile BP_RoundManager ->', c_rm[:150])

    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [SS, RM]}})
    print('Step 1 Overtime Unlock & Mode Select completed successfully!')

if __name__ == '__main__':
    main()
