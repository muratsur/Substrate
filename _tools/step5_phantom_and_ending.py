"""Step 5: Wire the Phantom Row (Round 5) & Sector D Demo Ending (Round 8)."""
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

def ensure_fns():
    graphs = [x['refPath'].split(':')[-1] for x in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': RM}}))['returnValue']]
    for fn in ['EnterSectorD', 'EndDemo', 'QuitApp']:
        if fn not in graphs:
            print(f'Adding function {fn} to BP_RoundManager...')
            M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': fn})

ADD_ROW_IF_MATCH = '''(fn AddRowIfMatch (Fixture Row)
  (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture Fixture))
  (if (== (Class|BPFixture|GetRowOrder _asbp_fixture) Row)
    (Variables|Default|SetTerminalNames (Utilities|String|Append (Variables|Default|GetTerminalNames) (Utilities|String|Append (Utilities|String|ToString(Name) (Class|BPFixture|GetFixtureID _asbp_fixture)) (Variables|Default|GetNL))))
    (Variables|Default|SetTerminalStates (Utilities|String|Append (Variables|Default|GetTerminalStates) (Utilities|String|Append (select (== (Class|BPFixture|GetLogResult _asbp_fixture) 0) "[ ]" (select (== (Class|BPFixture|GetLogResult _asbp_fixture) 1) "[PASS]" "[FLAG]")) (Variables|Default|GetNL))))
    (bind _correct (Class|BPFixture|IsLoggedCorrectly _asbp_fixture))
    (if (and (not _correct) (<= Row (Variables|Default|GetRequiredRowMax)))
      (Variables|Default|SetTerminalRemaining (+ (Variables|Default|GetTerminalRemaining) 1)))))
'''

REFRESH_TERMINAL = '''(fn RefreshTerminal ()
  (bind _currentround (Variables|Default|GetCurrentRound))
  (bind _returnvalue (Utilities|String|ToString(Integer) _currentround))
  (bind _returnvalue_1 10)
  (bind _returnvalue_2 100)
  (bind _returnvalue_3 0)
  (bind _terminalremaining (Variables|Default|GetTerminalRemaining))
  (bind _returnvalue_4 (Utilities|String|ToString(Integer) _terminalremaining))
  (bind _returnvalue_5 "CLOSE SHIFT: READY")
  (bind _returnvalue_6 (Utilities|String|Append "00" _returnvalue))
  (bind _returnvalue_7 (Utilities|String|Append "0" _returnvalue))
  (bind _returnvalue_8 (< _currentround _returnvalue_1))
  (bind _returnvalue_9 (< _currentround _returnvalue_2))
  (bind _returnvalue_10 (select _returnvalue_9 _returnvalue_7 _returnvalue))
  (bind _returnvalue_11 (select _returnvalue_8 _returnvalue_6 _returnvalue_10))
  (bind _returnvalue_12 (Utilities|String|Append "SHIFT " _returnvalue_11))
  (bind _returnvalue_13 (Utilities|String|Append _returnvalue_4 " left)"))
  (bind _returnvalue_14 (Utilities|String|Append "CLOSE SHIFT: BLOCKED (" _returnvalue_13))
  (bind _returnvalue_15 (> _terminalremaining _returnvalue_3))
  (bind _returnvalue_16 (select _returnvalue_15 _returnvalue_14 _returnvalue_5))
  (bind _self self)
  (Variables|Default|SetTerminalNames "")
  (Variables|Default|SetTerminalStates "")
  (Variables|Default|SetTerminalRemaining 0)
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _index (range (+ (Variables|Default|GetRequiredRowMax) 1))
    (for _array_element _outactors
      (CallFunction|AddRowIfMatch _self _array_element _index)))
  (if (>= (Variables|Default|GetCurrentRound) 5)
    (for _array_element _outactors
      (CallFunction|AddRowIfMatch _self _array_element 8)))
  (if (Variables|Default|GetDebugTerminal)
    (Development|PrintString (Utilities|String|Append (Utilities|String|Append _returnvalue_12 (Variables|Default|GetNL)) (Variables|Default|GetTerminalNames)) true true "(R=0.000000,G=0.660000,B=1.000000,A=1.000000)" 6.0)
    (Development|PrintString (Utilities|String|Append (Variables|Default|GetTerminalStates) _returnvalue_16) true true "(R=0.000000,G=0.660000,B=1.000000,A=1.000000)" 6.0))
  (CallFunction|PushTerminal _self _returnvalue_12 (Variables|Default|GetTerminalNames) (Variables|Default|GetTerminalStates) _returnvalue_16)
  (CallFunction|OpenWestGate))
'''

TRY_CLOSE_SHIFT = '''(fn TryCloseShift ()
  (if (Variables|Default|GetShiftOpen)
    (Variables|Default|SetAllCorrect true)
    (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
    (for _array_element _outactors
      (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
      (bind _inrange (Class|BPFixture|InRowRange _asbp_fixture 0 (Variables|Default|GetRequiredRowMax)))
      (bind _correct (Class|BPFixture|IsLoggedCorrectly _asbp_fixture))
      (if (and _inrange (not _correct))
        (Variables|Default|SetAllCorrect false)))
    (if (Variables|Default|GetAllCorrect)
      (if (>= (Variables|Default|GetCurrentRound) 8)
        (CallFunction|EnterSectorD)
        (else
          (CallFunction|StartShift)))
      (else
        (CallFunction|ArmGrowth)))))
'''

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
    (Class|BPFixture|LogFixture (Variables|Default|GetBestFixture) Result)
    (if (== (Class|BPFixture|GetRowOrder (Variables|Default|GetBestFixture)) 8)
      (CallFunction|EndDemo))
    (else
      (Development|PrintString "Nothing in range - look at a fixture, get within 4 m")))
  (CallFunction|RefreshTerminal))
'''

ENTER_SECTOR_D = '''(fn EnterSectorD ()
  (Variables|Default|SetShiftOpen false)
  (bind pawn (Game|GetPlayerPawn 0))
  (Transformation|SetActorLocationAndRotation
    :self pawn
    :NewLocation (Math|Vector|MakeVector -660.0 -8500.0 450.0)
    :NewRotation (Math|Rotator|MakeRotator 0.0 90.0 0.0)
    :bSweep false)
  (CallFunction|PushTerminal
    :Header "SECTOR D - ACCESS GRANTED"
    :Names "C-06 RELIEF VALVE"
    :States "[ ]"
    :Footer "PROCEED TO RELIEF VALVE")
  (Utilities|Time|SetTimerbyFunctionName
    :self self
    :FunctionName "EndDemo"
    :Time 900.0
    :bLooping false)
  (Development|PrintString "SECTOR D - ACCESS GRANTED. PROCEED TO RELIEF VALVE." true true "(R=1.000000,G=0.800000,B=0.200000,A=1.000000)" 8.0))
'''

END_DEMO = '''(fn EndDemo ()
  (Input|DisableInput :self self :PlayerController (Game|GetPlayerController 0))
  (CallFunction|PushTerminal
    :Header "SHIFT TERMINATED"
    :Names "SUBSTRATE DEMO COMPLETE"
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
  (Development|PrintString "SUBSTRATE DEMO COMPLETE - THANK YOU FOR PLAYING" true true "(R=0.200000,G=1.000000,B=0.500000,A=1.000000)" 10.0))
'''

QUIT_APP = '''(fn QuitApp ()
  (Game|QuitGame :SpecificPlayer (Game|GetPlayerController 0)))
'''

def main():
    M.init()
    ensure_fns()
    print('Writing AddRowIfMatch...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:AddRowIfMatch'}, 'code': balance(ADD_ROW_IF_MATCH)})
    print('Writing RefreshTerminal...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:RefreshTerminal'}, 'code': balance(REFRESH_TERMINAL)})
    print('Writing TryCloseShift...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:TryCloseShift'}, 'code': balance(TRY_CLOSE_SHIFT)})
    print('Writing LogLookedAtFixture...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:LogLookedAtFixture'}, 'code': balance(LOG_LOOKED_AT)})
    print('Writing EnterSectorD...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:EnterSectorD'}, 'code': balance(ENTER_SECTOR_D)})
    print('Writing EndDemo...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:EndDemo'}, 'code': balance(END_DEMO)})
    print('Writing QuitApp...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:QuitApp'}, 'code': balance(QUIT_APP)})

    c = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('compile RM ->', c[:200])

    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}})
    print('save dirty ->', s[:100])

if __name__ == '__main__':
    main()
