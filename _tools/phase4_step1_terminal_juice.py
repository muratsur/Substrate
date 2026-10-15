"""Phase 4 Step 1: Diegetic Terminal Juice & Attention-Trap Mechanics."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

BT = '/Game/Substrate/Core/BP_Terminal.BP_Terminal'
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
    print('=== PHASE 4 - STEP 1: TERMINAL JUICE & DIEGETIC MECHANICS ===')

    # 1. Add PlayerCamera variable to BP_Terminal if not present
    vars_bt = json.loads(M.bp('list_variables', {'blueprint': {'refPath': BT}})).get('returnValue', [])
    if 'PlayerCamera' not in vars_bt:
        print('Adding PlayerCamera variable to BP_Terminal...')
        M.bp('add_object_variable', {'blueprint': {'refPath': BT}, 'name': 'PlayerCamera', 'object_class': {'refPath': '/Script/Engine.CameraComponent'}})

    # 2. Ensure functions on BP_Terminal
    ensure_fns(BT, ['PunchTerminal', 'ResetPunch', 'TriggerGlitch', 'ResetGlitch'])

    # 3. Write AttachToPlayer on BP_Terminal
    ATTACH = '''(fn AttachToPlayer ()
  (bind _self self)
  (bind _ascamera_component (Utilities|Casting|CastToCameraComponent (Actor|GetComponentByClass (Game|GetPlayerPawn 0) "/Script/Engine.CameraComponent"))
    (:then
      (Variables|Default|SetPlayerCamera _ascamera_component)
      (Transformation|AttachActorToComponent _self _ascamera_component "None" "KeepRelative" "KeepRelative" "KeepRelative" false)
      (Transformation|SetActorRelativeRotation _self (Math|Rotator|MakeRotator 0.0 0.0 (Variables|Default|GetScreenYaw)))
      (Variables|Default|SetBound true)
      (CallFunction|ApplyRaised _self))
    (:CastFailed)))
'''
    print('Writing BP_Terminal:AttachToPlayer...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{BT}:AttachToPlayer'}, 'code': balance(ATTACH)})

    # 4. Write ApplyRaised on BP_Terminal (FOV change + Pitch variance on click)
    APPLY_RAISED = '''(fn ApplyRaised (Want)
  (bind _self self)
  (Collision|SetActorEnableCollision _self)
  (Variables|Default|SetRaised Want)
  (if Want
    (Transformation|SetActorRelativeLocation _self (Variables|Default|GetUpOffset))
    (else
      (Transformation|SetActorRelativeLocation _self (Variables|Default|GetStowOffset))))
  (Rendering|SetActorHiddenInGame _self (not Want))
  (Utilities|IsValid (Variables|Default|GetPlayerCamera)
    (:"Is Valid"
      (Class|CameraComponent|SetFieldOfView (Variables|Default|GetPlayerCamera) (select Want 86.0 90.0))))
  (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Click_on_Button.Click_on_Button" 0.7 (* (select Want 1.05 0.95) (Math|Random|RandomFloatInRange 0.94 1.06))))
'''
    print('Writing BP_Terminal:ApplyRaised...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{BT}:ApplyRaised'}, 'code': balance(APPLY_RAISED)})

    # 5. Write PunchTerminal & ResetPunch on BP_Terminal
    PUNCH = '''(fn PunchTerminal ()
  (bind body (Variables|Default|GetBody))
  (Transformation|SetRelativeLocationAndRotation body (Math|Vector|MakeVector 0.0 0.0 -1.2) (Math|Rotator|MakeRotator -2.5 0.0 0.0) false)
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ResetPunch" :Time 0.12 :bLooping false))
'''
    RESET_PUNCH = '''(fn ResetPunch ()
  (bind body (Variables|Default|GetBody))
  (Transformation|SetRelativeLocationAndRotation body (Math|Vector|MakeVector 0.0 0.0 0.0) (Math|Rotator|MakeRotator 0.0 0.0 0.0) false))
'''
    print('Writing BP_Terminal:PunchTerminal & ResetPunch...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{BT}:PunchTerminal'}, 'code': balance(PUNCH)})
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{BT}:ResetPunch'}, 'code': balance(RESET_PUNCH)})

    # 6. Write TriggerGlitch & ResetGlitch on BP_Terminal
    GLITCH = '''(fn TriggerGlitch ()
  (bind screen (Variables|Default|GetScreen))
  (bind widget (Utilities|Casting|CastToWBP_Terminal (UserInterface|GetUserWidgetObject screen))
    (:then
      (Widget|SetRenderOpacity widget 0.75)
      (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Laser_Pull.Laser_Pull" 0.3 0.35)
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ResetGlitch" :Time 0.3 :bLooping false))
    (:CastFailed)))
'''
    RESET_GLITCH = '''(fn ResetGlitch ()
  (bind screen (Variables|Default|GetScreen))
  (bind widget (Utilities|Casting|CastToWBP_Terminal (UserInterface|GetUserWidgetObject screen))
    (:then
      (Widget|SetRenderOpacity widget 1.0))
    (:CastFailed)))
'''
    print('Writing BP_Terminal:TriggerGlitch & ResetGlitch...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{BT}:TriggerGlitch'}, 'code': balance(GLITCH)})
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{BT}:ResetGlitch'}, 'code': balance(RESET_GLITCH)})

    print('Compiling BP_Terminal...')
    c_bt = M.bp('compile_blueprint', {'blueprint': {'refPath': BT}})
    print('  compile BP_Terminal ->', c_bt)

    # 7. Upgrade BP_RoundManager:LogLookedAtFixture to call PunchTerminal and audio pitch variance
    LOG_LOOKED = '''(fn LogLookedAtFixture (Result)
  (bind term (Variables|Default|GetTerminal))
  (bind _bestfixture (Variables|Default|GetBestFixture))
  (Variables|Default|SetBestDist 400.0)
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _array_element _outactors
    (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
    (bind _score (Class|BPFixture|ViewScore _asbp_fixture (Camera|GetCameraLocation (Game|GetPlayerCameraManager 0)) (Math|Vector|GetForwardVector (Camera|GetCameraRotation (Game|GetPlayerCameraManager 0)))))
    (if (< _score (Variables|Default|GetBestDist))
      (Variables|Default|SetBestDist _score)
      (Variables|Default|SetBestFixture _asbp_fixture)))
  (if (< (Variables|Default|GetBestDist) 400.0)
    (Class|BPFixture|LogFixture _bestfixture Result)
    (Variables|Default|SetLastLoggedAction (Utilities|String|Append (Utilities|String|ToString(Name) (Class|BPFixture|GetFixtureID _bestfixture)) (select (== Result 1) " [PASS]" " [FLAG]")))
    (Utilities|IsValid term
      (:"Is Valid"
        (Class|BPTerminal|PunchTerminal term)))
    (if (== Result 1)
      (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Laser_Pull.Laser_Pull" 0.6 (* 1.2 (Math|Random|RandomFloatInRange 0.94 1.06)))
      (else
        (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Invalid_Action.Invalid_Action" 0.7 (* 0.85 (Math|Random|RandomFloatInRange 0.94 1.06)))))
    (if (>= (Variables|Default|GetCurrentRound) 5)
      (if (< (Math|Random|RandomFloatInRange 0.0 1.0) 0.35)
        (Utilities|IsValid term
          (:"Is Valid"
            (Class|BPTerminal|TriggerGlitch term)))))
    (if (== (Class|BPFixture|GetRowOrder _bestfixture) 8)
      (CallFunction|EndDemo))
    (else
      (Development|PrintString (Variables|Default|GetLastLoggedAction) true true "(R=0.200000,G=0.800000,B=1.000000,A=1.000000)" 4.0)))
  (CallFunction|RefreshTerminal))
'''
    print('Writing BP_RoundManager:LogLookedAtFixture...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:LogLookedAtFixture'}, 'code': balance(LOG_LOOKED)})
    print('Compiling BP_RoundManager...')
    c_rm = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('  compile BP_RoundManager ->', c_rm)

    # 8. Save dirty assets
    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [BT, RM]}})
    print('Step 1 Terminal Juice & Attention-Trap Mechanics successfully implemented and saved!')

if __name__ == '__main__':
    main()
