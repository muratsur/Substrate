"""Step 7: Wire Footstep & Terminal Audio (T1.7 / T2.2)."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

TERM = '/Game/Substrate/Core/BP_Terminal.BP_Terminal'
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

TERM_APPLY_RAISED = '''(fn ApplyRaised (Want)
  (bind _self self)
  (Collision|SetActorEnableCollision _self)
  (Variables|Default|SetRaised Want)
  (if Want
    (Transformation|SetActorRelativeLocation _self (Variables|Default|GetUpOffset))
    (else
      (Transformation|SetActorRelativeLocation _self (Variables|Default|GetStowOffset))))
  (Rendering|SetActorHiddenInGame _self (not Want))
  (Audio|PlaySound2D
    :Sound "/Engine/VREditor/Sounds/UI/Click_on_Button.Click_on_Button"
    :VolumeMultiplier 0.7
    :PitchMultiplier (select Want 1.05 0.95)))
'''

LOG_LOOKED_AT_AUDIO = '''(fn LogLookedAtFixture (Result)
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
    (if (== Result 1)
      (Audio|PlaySound2D :Sound "/Engine/VREditor/Sounds/UI/Laser_Pull.Laser_Pull" :VolumeMultiplier 0.6 :PitchMultiplier 1.2)
      (else
        (Audio|PlaySound2D :Sound "/Engine/VREditor/Sounds/UI/Invalid_Action.Invalid_Action" :VolumeMultiplier 0.7 :PitchMultiplier 0.85)))
    (if (== (Class|BPFixture|GetRowOrder (Variables|Default|GetBestFixture)) 8)
      (CallFunction|EndDemo))
    (else
      (Development|PrintString "Nothing in range - look at a fixture, get within 4 m")))
  (CallFunction|RefreshTerminal))
'''

CHECK_FOOTSTEP = '''(fn CheckFootstep ()
  (bind pawn (Game|GetPlayerPawn 0))
  (Utilities|IsValid pawn
    (:"Is Valid"
      (bind vel (Movement|GetVelocity :self pawn))
      (bind spd (Math|Vector|VectorLength vel))
      (if (> spd 50.0)
        (bind loc (Transformation|GetActorLocation :self pawn))
        (bind pitch (Math|Random|RandomFloatinRange 0.92 1.08))
        (Audio|PlaySoundatLocation
          :Sound "/Engine/VREditor/Sounds/UI/Drop_Item_From_ContentBrowser.Drop_Item_From_ContentBrowser"
          :Location loc
          :VolumeMultiplier 0.5
          :PitchMultiplier pitch)))
    (:"Is Not Valid")))
'''

EVENT_GRAPH_AUDIO = '''(event EventBeginPlay
  (CallFunction|LoadShiftState)
  (CallFunction|StartShift)
  (Input|EnableInput (Game|GetPlayerController 0))
  (Utilities|Time|SetTimerbyFunctionName :self self :FunctionName "CheckFootstep" :Time 0.55 :bLooping true))

(event Collision|EventActorBeginOverlap (OtherActor)
  (Utilities|Casting|CastToCharacter OtherActor)
  (CallFunction|TryCloseShift))

(event EventTick (DeltaSeconds))

(event E (Key))

(event Q (Key))
'''

def main():
    M.init()
    print('Writing ApplyRaised on BP_Terminal...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{TERM}:ApplyRaised'}, 'code': balance(TERM_APPLY_RAISED)})
    c_t = M.bp('compile_blueprint', {'blueprint': {'refPath': TERM}})
    print('compile BP_Terminal ->', c_t[:150])

    rfns = [x['refPath'].split(':')[-1] for x in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': RM}}))['returnValue']]
    if 'CheckFootstep' not in rfns:
        print('Adding CheckFootstep to BP_RoundManager...')
        M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': 'CheckFootstep'})

    print('Writing CheckFootstep on BP_RoundManager...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:CheckFootstep'}, 'code': balance(CHECK_FOOTSTEP)})

    print('Writing LogLookedAtFixture on BP_RoundManager...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:LogLookedAtFixture'}, 'code': balance(LOG_LOOKED_AT_AUDIO)})

    print('Writing EventGraph on BP_RoundManager...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:EventGraph'}, 'code': balance(EVENT_GRAPH_AUDIO)})

    c_r = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('compile BP_RoundManager ->', c_r[:150])

    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}})
    print('save dirty ->', s[:100])

if __name__ == '__main__':
    main()
