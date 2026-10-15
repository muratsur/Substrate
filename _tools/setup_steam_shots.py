"""Phase 3 Step 5: Setup Steam Shot automation in BP_RoundManager."""
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

def main():
    M.init()
    print('--- Setting up Steam Screenshot Automation ---')

    RUN_CAPTURE = '''(fn RunSteamCapture ()
  (Variables|Default|SetSteamShotStep 0)
  (CallFunction|StepSteamCapture))
'''

    STEP_CAPTURE = '''(fn StepSteamCapture ()
  (bind pawn (Game|GetPlayerPawn 0))
  (bind term (Variables|Default|GetTerminal))
  (bind step (Variables|Default|GetSteamShotStep))
  (switch int step
    (:0
      (Variables|Default|SetSteamShotStep 1)
      (Class|BPTerminal|ApplyRaised :self term :Want false)
      (Transformation|SetActorLocationAndRotation :self pawn :NewLocation (Math|Vector|MakeVector 600.0 3500.0 420.0) :NewRotation (Math|Rotator|MakeRotator 0.0 90.0 0.0) :bSweep false)
      (Development|ExecuteConsoleCommand "HighResShot 3840x2160")
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "StepSteamCapture" :Time 1.5 :bLooping false))
    (:1
      (Variables|Default|SetSteamShotStep 2)
      (Class|BPTerminal|ApplyRaised :self term :Want false)
      (Transformation|SetActorLocationAndRotation :self pawn :NewLocation (Math|Vector|MakeVector 8560.0 4300.0 420.0) :NewRotation (Math|Rotator|MakeRotator 0.0 -90.0 0.0) :bSweep false)
      (Development|ExecuteConsoleCommand "HighResShot 3840x2160")
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "StepSteamCapture" :Time 1.5 :bLooping false))
    (:2
      (Variables|Default|SetSteamShotStep 3)
      (Transformation|SetActorLocationAndRotation :self pawn :NewLocation (Math|Vector|MakeVector 1469.0 4150.0 420.0) :NewRotation (Math|Rotator|MakeRotator 0.0 90.0 0.0) :bSweep false)
      (CallFunction|LogLookedAtFixture 1)
      (Class|BPTerminal|ApplyRaised :self term :Want true)
      (Development|ExecuteConsoleCommand "HighResShot 3840x2160")
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "StepSteamCapture" :Time 1.5 :bLooping false))
    (:3
      (Variables|Default|SetSteamShotStep 4)
      (Variables|Default|SetCurrentRound 5)
      (CallFunction|RefreshTerminal)
      (Class|BPTerminal|ApplyRaised :self term :Want true)
      (Transformation|SetActorLocationAndRotation :self pawn :NewLocation (Math|Vector|MakeVector 1469.0 4150.0 420.0) :NewRotation (Math|Rotator|MakeRotator 0.0 90.0 0.0) :bSweep false)
      (Development|ExecuteConsoleCommand "HighResShot 3840x2160")
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "StepSteamCapture" :Time 1.5 :bLooping false))
    (:4
      (Variables|Default|SetSteamShotStep 5)
      (Class|BPTerminal|ApplyRaised :self term :Want false)
      (bind gn (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_GrowthNode.BP_GrowthNode_C"))
      (for elem gn
        (bind gnode (Utilities|Casting|CastToBP_GrowthNode elem)
          (:then
            (Class|BPGrowthNode|ForceAdvance :self gnode)
            (Class|BPGrowthNode|ForceAdvance :self gnode)
            (Class|BPGrowthNode|ForceAdvance :self gnode))
          (:CastFailed)))
      (Transformation|SetActorLocationAndRotation :self pawn :NewLocation (Math|Vector|MakeVector 2200.0 5000.0 380.0) :NewRotation (Math|Rotator|MakeRotator -10.0 90.0 0.0) :bSweep false)
      (Development|ExecuteConsoleCommand "HighResShot 3840x2160")
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "StepSteamCapture" :Time 1.5 :bLooping false))
    (:5
      (Variables|Default|SetSteamShotStep 6)
      (bind socks (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C"))
      (for s socks
        (bind sock (Utilities|Casting|CastToBP_AnomalySocket s)
          (:then
            (if (== (Class|BPAnomalySocket|GetAnomalyType :self sock) 0)
              (Class|BPAnomalySocket|Apply :self sock :Round 2)))
          (:CastFailed)))
      (CallFunction|RefreshTerminal)
      (Class|BPTerminal|ApplyRaised :self term :Want true)
      (Transformation|SetActorLocationAndRotation :self pawn :NewLocation (Math|Vector|MakeVector -1516.0 8100.0 420.0) :NewRotation (Math|Rotator|MakeRotator 0.0 90.0 0.0) :bSweep false)
      (Development|ExecuteConsoleCommand "HighResShot 3840x2160")
      (Development|PrintString "ALL 6 STEAM SCREENSHOTS CAPTURED!" true true "(R=0.200000,G=1.000000,B=0.500000,A=1.000000)" 8.0))
    (:Default)))
'''

    print('Writing RunSteamCapture...')
    r_rc = M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:RunSteamCapture'}, 'code': balance(RUN_CAPTURE)})
    print('  RunSteamCapture ->', r_rc[:150])

    print('Writing StepSteamCapture...')
    r_sc = M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:StepSteamCapture'}, 'code': balance(STEP_CAPTURE)})
    print('  StepSteamCapture ->', r_sc[:150])

    c_r = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('compile BP_RoundManager ->', c_r[:150])

    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}})
    print('save dirty ->', s[:100])

if __name__ == '__main__':
    main()
