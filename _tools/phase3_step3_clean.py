"""Phase 3 Step 3: Clean Implementation of Save Reset Key & Diegetic Terminal Footer."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
EG = {'refPath': RM + ':EventGraph'}

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

def setup_vars_and_fns():
    rvars = json.loads(M.bp('list_variables', {'blueprint': {'refPath': RM}}))['returnValue']
    if 'LastLoggedAction' not in rvars:
        print('Adding LastLoggedAction variable...')
        M.bp('add_variable', {'blueprint': {'refPath': RM}, 'name': 'LastLoggedAction', 'type_name': 'String'})

    rfns = [x['refPath'].split(':')[-1] for x in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': RM}}))['returnValue']]
    if 'ResetSaveData' not in rfns:
        print('Adding ResetSaveData function...')
        M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': 'ResetSaveData'})

def write_reset_save_data():
    RESET_SAVE_DATA = '''(fn ResetSaveData ()
  (SaveGame|DeleteGameInSlot :SlotName "Substrate_0" :UserIndex 0)
  (Variables|Default|SetCurrentRound 0)
  (CallFunction|StartShift)
  (Development|PrintString "SAVE RESET -> SHIFT 001" true true "(R=1.000000,G=0.500000,B=0.000000,A=1.000000)" 6.0))
'''
    r = M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:ResetSaveData'}, 'code': balance(RESET_SAVE_DATA)})
    print('write ResetSaveData ->', r[:150])

def write_start_shift():
    STARTSHIFT = '''(fn StartShift ()
  (Variables|Default|SetCurrentRound (+ (Variables|Default|GetCurrentRound) 1))
  (Variables|Default|SetShiftOpen true)
  (Variables|Default|SetLastLoggedAction "")
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _array_element _outactors
    (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
    (Class|BPFixture|ResetLog _asbp_fixture))
  (CallFunction|ArmGrowth)
  (CallFunction|FindTerminal)
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshTerminal" :Time 0.3)
  (CallFunction|SaveShiftState)
  (Utilities|IsValid (Variables|Default|GetAnomalyDirector)
    (:"Is Valid"
      (Class|BPAnomalyDirector|RollAnomalies (Variables|Default|GetAnomalyDirector) (Variables|Default|GetCurrentRound)))
    (:"Is Not Valid"
      (bind _outactors_1 (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector_C"))
      (CallFunction|CacheDirector :self self :Found _outactors_1)
      (Class|BPAnomalyDirector|RollAnomalies (Variables|Default|GetAnomalyDirector) (Variables|Default|GetCurrentRound)))))
'''
    r = M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:StartShift'}, 'code': balance(STARTSHIFT)})
    print('write StartShift ->', r[:150])

def write_log_looked_at():
    LOG_LOOKED_AT = '''(fn LogLookedAtFixture (Result)
  (Variables|Default|SetBestDist 400.0)
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _array_element _outactors
    (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
    (bind _score (Class|BPFixture|ViewScore _asbp_fixture (Camera|GetCameraLocation (Game|GetPlayerCameraManager 0)) (Math|Vector|GetForwardVector (Camera|GetCameraRotation (Game|GetPlayerCameraManager 0)))))
    (if (< _score (Variables|Default|GetBestDist))
      (Variables|Default|SetBestDist _score)
      (Variables|Default|SetBestFixture _asbp_fixture)))
  (if (< (Variables|Default|GetBestDist) 400.0)
    (bind best (Variables|Default|GetBestFixture))
    (Class|BPFixture|LogFixture best Result)
    (bind fid (Utilities|String|ToString(Name) (Class|BPFixture|GetFixtureID best)))
    (bind tag (select (== Result 1) " [PASS]" " [FLAG]"))
    (Variables|Default|SetLastLoggedAction (Utilities|String|Append fid tag))
    (if (== Result 1)
      (Audio|PlaySound2D :Sound "/Engine/VREditor/Sounds/UI/Laser_Pull.Laser_Pull" :VolumeMultiplier 0.6 :PitchMultiplier 1.2)
      (else
        (Audio|PlaySound2D :Sound "/Engine/VREditor/Sounds/UI/Invalid_Action.Invalid_Action" :VolumeMultiplier 0.7 :PitchMultiplier 0.85)))
    (if (== (Class|BPFixture|GetRowOrder best) 8)
      (CallFunction|EndDemo))
    (else
      (Development|PrintString (Variables|Default|GetLastLoggedAction) true true "(R=0.200000,G=0.800000,B=1.000000,A=1.000000)" 4.0)))
  (CallFunction|RefreshTerminal))
'''
    r = M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:LogLookedAtFixture'}, 'code': balance(LOG_LOOKED_AT)})
    print('write LogLookedAtFixture ->', r[:150])

def write_refresh_terminal():
    REFRESH_TERMINAL = '''(fn RefreshTerminal ()
  (bind _currentround (Variables|Default|GetCurrentRound))
  (bind _returnvalue (Utilities|String|ToString(Integer) _currentround))
  (bind _terminalremaining (Variables|Default|GetTerminalRemaining))
  (bind _returnvalue_4 (Utilities|String|ToString(Integer) _terminalremaining))
  (bind _returnvalue_6 (Utilities|String|Append "00" _returnvalue))
  (bind _returnvalue_7 (Utilities|String|Append "0" _returnvalue))
  (bind _returnvalue_8 (< _currentround 10))
  (bind _returnvalue_9 (< _currentround 100))
  (bind _returnvalue_10 (select _returnvalue_9 _returnvalue_7 _returnvalue))
  (bind _returnvalue_11 (select _returnvalue_8 _returnvalue_6 _returnvalue_10))
  (bind _returnvalue_12 (Utilities|String|Append "SHIFT " _returnvalue_11))
  (bind _returnvalue_13 (Utilities|String|Append _returnvalue_4 " left)"))
  (bind _returnvalue_14 (Utilities|String|Append "CLOSE SHIFT: BLOCKED (" _returnvalue_13))
  (bind _returnvalue_15 (> _terminalremaining 0))
  (bind _basefooter (select _returnvalue_15 _returnvalue_14 "CLOSE SHIFT: READY"))
  (bind _last (Variables|Default|GetLastLoggedAction))
  (bind _haslast (> (Utilities|String|Len _last) 0))
  (bind _footer (select _haslast (Utilities|String|Append (Utilities|String|Append _last " | ") _basefooter) _basefooter))
  (bind _self self)
  (Variables|Default|SetTerminalNames "")
  (Variables|Default|SetTerminalStates "")
  (Variables|Default|SetTerminalRemaining 0)
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _index (range (+ (Variables|Default|GetRequiredRowMax) 1))
    (for _array_element _outactors
      (CallFunction|AddRowifMatch _self _array_element _index)))
  (if (Variables|Default|GetDebugTerminal)
    (Development|PrintString (Utilities|String|Append (Utilities|String|Append _returnvalue_12 (Variables|Default|GetNL)) (Variables|Default|GetTerminalNames)) true true "(R=0.000000,G=0.660000,B=1.000000,A=1.000000)" 6.0)
    (Development|PrintString (Utilities|String|Append (Variables|Default|GetTerminalStates) _footer) true true "(R=0.000000,G=0.660000,B=1.000000,A=1.000000)" 6.0))
  (CallFunction|PushTerminal _self _returnvalue_12 (Variables|Default|GetTerminalNames) (Variables|Default|GetTerminalStates) _footer)
  (CallFunction|OpenWestGate))
'''
    r = M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:RefreshTerminal'}, 'code': balance(REFRESH_TERMINAL)})
    print('write RefreshTerminal ->', r[:150])

def wire_key_nodes():
    print('Wiring Backspace and Delete keys in EventGraph...')
    for key, y in [('BackSpace', 1300), ('Delete', 1600)]:
        n_key = json.loads(M.bp('create_node', {
            'graph': EG, 'type_id': 'Input|KeyboardEvents|' + key, 'pos': {'x': 0, 'y': y}
        }))['returnValue']
        n_call = json.loads(M.bp('create_node', {
            'graph': EG, 'type_id': 'CallFunction|ResetSaveData', 'pos': {'x': 420, 'y': y}
        }))['returnValue']

        info = json.loads(M.bp('get_node_infos', {'nodes': [n_key, n_call]}))['returnValue']
        kref = n_key['refPath'] if isinstance(n_key, dict) else n_key
        cref = n_call['refPath'] if isinstance(n_call, dict) else n_call
        ki = [i for i in info if i['node']['refPath'] == kref][0]
        ci = [i for i in info if i['node']['refPath'] == cref][0]
        pressed = [p for p in ki['output_pins'] if p['name'] == 'Pressed'][0]
        ex = [p for p in ci['input_pins'] if p['type_id'] == 'Exec'][0]
        c_res = M.bp('connect_pins', {'output_pin': pressed['pin_id'], 'input_pin': ex['pin_id']})
        print(f'  wired {key} ->', c_res[:100])

def main():
    M.init()
    setup_vars_and_fns()
    write_reset_save_data()
    write_start_shift()
    write_log_looked_at()
    write_refresh_terminal()
    wire_key_nodes()
    c = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('compile BP_RoundManager ->', c[:150])
    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}})
    print('save dirty ->', s[:100])

if __name__ == '__main__':
    main()
