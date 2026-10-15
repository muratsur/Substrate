"""Phase 4 Step 4: Streamer Replayability - Anomaly Codex & Persistence."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

SS = '/Game/Substrate/Core/BP_SubstrateSave.BP_SubstrateSave'
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
    print('=== PHASE 4 - STEP 4: CODEX PERSISTENCE & OVERTIME TRACKING ===')

    # 1. Add variables to BP_SubstrateSave
    vars_ss = json.loads(M.bp('list_variables', {'blueprint': {'refPath': SS}})).get('returnValue', [])
    for vname, vtype in [('DiscoveredMask', 'int'), ('DiscoveredCount', 'int'), ('CompletedSectorD', 'bool')]:
        if vname not in vars_ss:
            print(f'Adding {vname} to BP_SubstrateSave...')
            M.bp('add_variable', {'blueprint': {'refPath': SS}, 'name': vname, 'type_name': vtype})

    # 2. Add variables to BP_RoundManager
    vars_rm = json.loads(M.bp('list_variables', {'blueprint': {'refPath': RM}})).get('returnValue', [])
    for vname, vtype in [('DiscoveredMask', 'int'), ('DiscoveredCount', 'int'), ('CompletedSectorD', 'bool')]:
        if vname not in vars_rm:
            print(f'Adding {vname} to BP_RoundManager...')
            M.bp('add_variable', {'blueprint': {'refPath': RM}, 'name': vname, 'type_name': vtype})

    # 3. Update BP_SubstrateSave:ApplySaveData to accept mask and count
    ensure_fns(SS, ['SetCodexData', 'GetDiscoveredCount', 'GetDiscoveredMask', 'GetCompletedSectorD'])

    SET_CODEX = '''(fn SetCodexData (Mask Count CompletedD)
  (Variables|Default|SetDiscoveredMask Mask)
  (Variables|Default|SetDiscoveredCount Count)
  (Variables|Default|SetCompletedSectorD CompletedD))
'''
    GET_COUNT = '''(fn GetDiscoveredCount ()
  (return (Variables|Default|GetDiscoveredCount)))
'''
    GET_MASK = '''(fn GetDiscoveredMask ()
  (return (Variables|Default|GetDiscoveredMask)))
'''
    GET_COMPLETED = '''(fn GetCompletedSectorD ()
  (return (Variables|Default|GetCompletedSectorD)))
'''
    print('Writing BP_SubstrateSave codex functions...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{SS}:SetCodexData'}, 'code': balance(SET_CODEX)})
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{SS}:GetDiscoveredCount'}, 'code': balance(GET_COUNT)})
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{SS}:GetDiscoveredMask'}, 'code': balance(GET_MASK)})
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{SS}:GetCompletedSectorD'}, 'code': balance(GET_COMPLETED)})
    c_ss = M.bp('compile_blueprint', {'blueprint': {'refPath': SS}})
    print('  compile BP_SubstrateSave ->', c_ss)

    # 4. Add RecordDiscoveredAnomalies to BP_RoundManager
    ensure_fns(RM, ['RecordDiscoveredAnomalies'])
    RECORD = '''(fn RecordDiscoveredAnomalies ()
  (bind socks (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C"))
  (for s socks
    (bind sock (Utilities|Casting|CastToBP_AnomalySocket s)
      (:then
        (if (Class|BPAnomalySocket|GetApplied sock)
          (bind code (Class|BPAnomalySocket|GetAnomalyType sock))
          (bind bit (Math|Integer|bit_shift_left 1 code))
          (if (== (Math|Integer|bit_and (Variables|Default|GetDiscoveredMask) bit) 0)
            (Variables|Default|SetDiscoveredMask (Math|Integer|bit_or (Variables|Default|GetDiscoveredMask) bit))
            (Variables|Default|SetDiscoveredCount (+ (Variables|Default|GetDiscoveredCount) 1)))))
      (:CastFailed))))
'''
    print('Writing BP_RoundManager:RecordDiscoveredAnomalies...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:RecordDiscoveredAnomalies'}, 'code': balance(RECORD)})

    # 5. Update SaveShiftState on BP_RoundManager
    SAVE_STATE = '''(fn SaveShiftState ()
  (bind _save (SaveGame|CreateSaveGameObject "/Game/Substrate/Core/BP_SubstrateSave.BP_SubstrateSave_C"))
  (bind _assave (Utilities|Casting|CastToBP_SubstrateSave _save)
    (:then
      (Class|BPSubstrateSave|ApplySaveData _assave (Variables|Default|GetCurrentRound))
      (Class|BPSubstrateSave|SetCodexData _assave (Variables|Default|GetDiscoveredMask) (Variables|Default|GetDiscoveredCount) (Variables|Default|GetCompletedSectorD))
      (SaveGame|SaveGameToSlot _assave "Substrate_0"))
    (:CastFailed)))
'''
    print('Writing BP_RoundManager:SaveShiftState...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:SaveShiftState'}, 'code': balance(SAVE_STATE)})

    # 6. Update LoadShiftState on BP_RoundManager
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
        (Variables|Default|SetCompletedSectorD (Class|BPSubstrateSave|GetCompletedSectorD _assave)))
      (:CastFailed))))
'''
    print('Writing BP_RoundManager:LoadShiftState...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:LoadShiftState'}, 'code': balance(LOAD_STATE)})

    # 7. Update ResetSaveData on BP_RoundManager
    RESET_SAVE = '''(fn ResetSaveData ()
  (SaveGame|DeleteGameInSlot "Substrate_0")
  (Variables|Default|SetCurrentRound 0)
  (Variables|Default|SetDiscoveredMask 0)
  (Variables|Default|SetDiscoveredCount 0)
  (Variables|Default|SetCompletedSectorD false)
  (CallFunction|StartShift)
  (Development|PrintString "SAVE RESET -> SHIFT 001" true true "(R=1.000000,G=0.500000,B=0.000000,A=1.000000)" 6.0))
'''
    print('Writing BP_RoundManager:ResetSaveData...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:ResetSaveData'}, 'code': balance(RESET_SAVE)})

    # 8. Update RefreshTerminal on BP_RoundManager for Shift 1 Boot Summary
    REFRESH_TERM = '''(fn RefreshTerminal ()
  (bind term (Variables|Default|GetTerminal))
  (bind cur_round (Variables|Default|GetCurrentRound))
  (bind header (Utilities|String|Append "SHIFT 00" (Utilities|String|ToString(Integer) cur_round)))
  (bind names "")
  (bind states "")
  (bind footer "")
  (bind r0 (CallFunction|AddRowIfMatch names states 0 "C-01 INLET VALVE"))
  (bind names (Utilities|SetOutVariable:names r0:names))
  (bind states (Utilities|SetOutVariable:states r0:states))
  (bind r1 (CallFunction|AddRowIfMatch names states 1 "C-02 FILTRATION SEAL"))
  (bind names (Utilities|SetOutVariable:names r1:names))
  (bind states (Utilities|SetOutVariable:states r1:states))
  (bind r2 (CallFunction|AddRowIfMatch names states 2 "C-03 PRESSURE GAUGE"))
  (bind names (Utilities|SetOutVariable:names r2:names))
  (bind states (Utilities|SetOutVariable:states r2:states))
  (bind r3 (CallFunction|AddRowIfMatch names states 3 "C-04 OVERFLOW LAMP"))
  (bind names (Utilities|SetOutVariable:names r3:names))
  (bind states (Utilities|SetOutVariable:states r3:states))
  (bind r4 (CallFunction|AddRowIfMatch names states 4 "C-05 SUMP ACCESS"))
  (bind names (Utilities|SetOutVariable:names r4:names))
  (bind states (Utilities|SetOutVariable:states r4:states))
  (if (>= cur_round 3)
    (bind rb1 (CallFunction|AddRowIfMatch names states 5 "B-01 JUNCTION CONDUIT"))
    (bind names (Utilities|SetOutVariable:names rb1:names))
    (bind states (Utilities|SetOutVariable:states rb1:states))
    (bind rb2 (CallFunction|AddRowIfMatch names states 6 "B-02 VENTILATION SHAFT"))
    (bind names (Utilities|SetOutVariable:names rb2:names))
    (bind states (Utilities|SetOutVariable:states rb2:states))
    (bind rb3 (CallFunction|AddRowIfMatch names states 7 "B-03 DRAIN MONITOR"))
    (bind names (Utilities|SetOutVariable:names rb3:names))
    (bind states (Utilities|SetOutVariable:states rb3:states)))
  (if (>= cur_round 5)
    (bind names (Utilities|String|Append names "C-06 RELIEF VALVE\n"))
    (bind states (Utilities|String|Append states "[ ]\n")))
  (if (and (== cur_round 1) (== (Variables|Default|GetLastLoggedAction) ""))
    (bind footer (Utilities|String|Append (Utilities|String|Append "CATALOGUED ANOMALIES: [" (Utilities|String|ToString(Integer) (Variables|Default|GetDiscoveredCount))) " / 10] | PRESS [BACKSPACE] TO WIPE RECORD"))
    (else
      (if (!= (Variables|Default|GetLastLoggedAction) "")
        (bind footer (Utilities|String|Append "CLOSE SHIFT: AIRLOCK AT DOCK | " (Variables|Default|GetLastLoggedAction)))
        (else
          (bind footer "CLOSE SHIFT: AIRLOCK AT DOCK")))))
  (Utilities|IsValid term
    (:"Is Valid"
      (Class|BPTerminal|ShowChecklist term header names states footer))))
'''
    print('Writing BP_RoundManager:RefreshTerminal...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:RefreshTerminal'}, 'code': balance(REFRESH_TERM)})

    # 9. Update TryCloseShift to call RecordDiscoveredAnomalies on success
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

    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [SS, RM]}})
    print('Step 4 Codex Persistence & Overtime Tracking successfully implemented and saved!')

if __name__ == '__main__':
    main()
