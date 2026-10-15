"""Phase 4 Step 2: Observer-Reactive (Gaslighting) Anomalies & Proximity Spook."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

AS = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket'
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
    print('=== PHASE 4 - STEP 2: OBSERVER-REACTIVE ANOMALIES & SPOOK CUES ===')

    # 1. Add variables to BP_AnomalySocket
    vars_as = json.loads(M.bp('list_variables', {'blueprint': {'refPath': AS}})).get('returnValue', [])
    if 'GazeDuration' not in vars_as:
        print('Adding GazeDuration variable to BP_AnomalySocket...')
        M.bp('add_variable', {'blueprint': {'refPath': AS}, 'name': 'GazeDuration', 'type_name': 'float'})
    if 'GazeDissolved' not in vars_as:
        print('Adding GazeDissolved variable to BP_AnomalySocket...')
        M.bp('add_variable', {'blueprint': {'refPath': AS}, 'name': 'GazeDissolved', 'type_name': 'bool'})

    # 2. Ensure CheckGaze function on BP_AnomalySocket
    ensure_fns(AS, ['CheckGaze'])

    # 3. Write CheckGaze on BP_AnomalySocket
    CHECK_GAZE = '''(fn CheckGaze ()
  (if (Variables|Default|GetApplied)
    (if (not (Variables|Default|GetGazeDissolved))
      (bind typ (Variables|Default|GetAnomalyType))
      (if (or (== typ 4) (== typ 5))
        (bind target (Camera|GetTarget))
        (Utilities|IsValid target
          (:"Is Valid"
            (bind cam (Game|GetPlayerCameraManager 0))
            (bind camLoc (Camera|GetCameraLocation cam))
            (bind camRot (Camera|GetCameraRotation cam))
            (bind camFwd (Math|Vector|GetForwardVector camRot))
            (bind sockLoc (Transformation|GetActorLocation target))
            (bind toSock (Math|Vector|vector-vector sockLoc camLoc))
            (bind dist (Math|Vector|VectorLength toSock))
            (if (< dist 900.0)
              (bind dir (Math|Vector|Normal toSock))
              (bind dot (Math|Vector|VectorDotProduct camFwd dir))
              (if (> dot 0.88)
                (Variables|Default|SetGazeDuration (+ (Variables|Default|GetGazeDuration) 0.15))
                (if (>= (Variables|Default|GetGazeDuration) 1.2)
                  (Variables|Default|SetGazeDissolved true)
                  (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Laser_Pull.Laser_Pull" 0.5 0.6)
                  (if (== typ 4)
                    (Rendering|SetActorHiddenInGame target true)
                    (Collision|SetActorEnableCollision target false))
                  (if (== typ 5)
                    (bind prim (Utilities|Casting|CastToPrimitiveComponent (Actor|GetComponentByClass target "/Script/Engine.PrimitiveComponent"))
                      (:then
                        (Rendering|SetCastHiddenShadow prim false))
                      (:CastFailed))))
                (else
                  (Variables|Default|SetGazeDuration 0.0))))
              (else
                (Variables|Default|SetGazeDuration 0.0)))))))))
'''
    print('Writing BP_AnomalySocket:CheckGaze...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{AS}:CheckGaze'}, 'code': balance(CHECK_GAZE)})

    # 4. Update BP_AnomalySocket:Apply
    APPLY = '''(fn Apply (Round)
  (bind _secondaryactor (Variables|Default|GetSecondaryActor))
  (Variables|Default|SetApplied false)
  (bind _canapply (CallFunction|CanApply self Round))
  (if (not _canapply)
    (return false)
    (else
      (bind _target (Camera|GetTarget))
      (Utilities|IsValid _target
        (:"Is Valid"
          (switch Utilities|FlowControl|Switch|SwitchonInt (Variables|Default|GetAnomalyType)
            (:Default
              (return false))
            (:0
              (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _target)
                (:then
                  (Variables|Default|SetCachedState (Class|BPFixture|GetFixtureState _asbp_fixture))
                  (Class|BPFixture|ApplyFixtureState _asbp_fixture 2)
                  (Variables|Default|SetApplied true)
                  (Variables|Default|SetLastAppliedRound Round)
                  (return true))
                (:CastFailed
                  (Variables|Default|SetCachedState 0)
                  (Rendering|SetActorHiddenInGame _target true)
                  (Collision|SetActorEnableCollision _target)
                  (Variables|Default|SetApplied true)
                  (Variables|Default|SetLastAppliedRound Round)
                  (return true))))
            (:1
              (bind _aslight_component (Utilities|Casting|CastToLightComponent (Actor|GetComponentByClass _target "/Script/Engine.LightComponent"))
                (:then
                  (Variables|Default|SetCachedIntensity (Class|LightComponentBase|GetIntensity _aslight_component))
                  (Rendering|Components|Light|SetIntensity _aslight_component (Variables|Default|GetLightIntensity))
                  (Variables|Default|SetApplied true)
                  (Variables|Default|SetLastAppliedRound Round)
                  (return true))
                (:CastFailed
                  (return false))))
            (:2
              (bind _asbp_growth_node (Utilities|Casting|CastToBP_GrowthNode _target)
                (:then
                  (Class|BPGrowthNode|ForceAdvance _asbp_growth_node)
                  (Variables|Default|SetApplied true)
                  (Variables|Default|SetLastAppliedRound Round)
                  (return true))
                (:CastFailed
                  (return false))))
            (:3
              (Variables|Default|SetCachedTransform (Transformation|GetActorTransform _target))
              (Transformation|SetActorLocation _target (Math|Vector|vector+vector (Transformation|GetActorLocation _target) (Variables|Default|GetOffset)))
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:4
              (Rendering|SetActorHiddenInGame _target)
              (Collision|SetActorEnableCollision _target true)
              (Variables|Default|SetGazeDuration 0.0)
              (Variables|Default|SetGazeDissolved false)
              (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "CheckGaze" :Time 0.15 :bLooping true)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:5
              (bind _asprimitive_component (Utilities|Casting|CastToPrimitiveComponent (Actor|GetComponentByClass _target "/Script/Engine.PrimitiveComponent"))
                (:then
                  (Rendering|SetCastHiddenShadow _asprimitive_component true)
                  (Variables|Default|SetGazeDuration 0.0)
                  (Variables|Default|SetGazeDissolved false)
                  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "CheckGaze" :Time 0.15 :bLooping true)
                  (Variables|Default|SetApplied true)
                  (Variables|Default|SetLastAppliedRound Round)
                  (return true))
                (:CastFailed
                  (return false))))
            (:6
              (Rendering|SetActorHiddenInGame _target true)
              (Collision|SetActorEnableCollision _target)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (Utilities|IsValid _secondaryactor
                (:"Is Valid"
                  (Rendering|SetActorHiddenInGame _secondaryactor)
                  (Collision|SetActorEnableCollision _secondaryactor true)
                  (return true))
                (:"Is Not Valid"
                  (return true))))
            (:7
              (bind _asaudio_component (Utilities|Casting|CastToAudioComponent (Actor|GetComponentByClass _target "/Script/Engine.AudioComponent"))
                (:then
                  (Audio|Components|Audio|SetPaused _asaudio_component true)
                  (Variables|Default|SetApplied true)
                  (Variables|Default|SetLastAppliedRound Round)
                  (return true))
                (:CastFailed
                  (return false))))
            (:8
              (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _target)
                (:then
                  (Variables|Default|SetCachedFixtureID (Utilities|String|ToString(Name) (Class|BPFixture|GetFixtureID _asbp_fixture)))
                  (Class|BPFixture|RenameFixture _asbp_fixture (Variables|Default|GetNote))
                  (Variables|Default|SetApplied true)
                  (Variables|Default|SetLastAppliedRound Round)
                  (return true))
                (:CastFailed
                  (Variables|Default|SetApplied true)
                  (Variables|Default|SetLastAppliedRound Round)
                  (return true))))
            (:9
              (bind _asbp_airlock (Utilities|Casting|CastToBP_Airlock _target)
                (:then
                  (Class|BPAirlock|ApplyLoopBack _asbp_airlock true)
                  (Variables|Default|SetApplied true)
                  (Variables|Default|SetLastAppliedRound Round)
                  (return true))
                (:CastFailed
                  (return false))))))
        (:"Is Not Valid"
          (return false))))))
'''
    print('Writing BP_AnomalySocket:Apply...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{AS}:Apply'}, 'code': balance(APPLY)})

    # 5. Update BP_AnomalySocket:Revert
    REVERT = '''(fn Revert ()
  (bind _secondaryactor (Variables|Default|GetSecondaryActor))
  (if (not (Variables|Default|GetApplied))
    _
    (elif (== (Variables|Default|GetRevertRule) 1)
      _
      (else
        (Variables|Default|SetApplied false)
        (Variables|Default|SetGazeDuration 0.0)
        (Variables|Default|SetGazeDissolved false)
        (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "CheckGaze")
        (bind _target (Camera|GetTarget))
        (Utilities|IsValid _target
          (:"Is Valid"
            (switch Utilities|FlowControl|Switch|SwitchonInt (Variables|Default|GetAnomalyType)
              (:0
                (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _target)
                  (:then
                    (Class|BPFixture|ApplyFixtureState _asbp_fixture (Variables|Default|GetCachedState)))\n                  (:CastFailed
                    (Rendering|SetActorHiddenInGame _target)
                    (Collision|SetActorEnableCollision _target true))))
              (:1
                (bind _aslight_component (Utilities|Casting|CastToLightComponent (Actor|GetComponentByClass _target "/Script/Engine.LightComponent")))
                (Rendering|Components|Light|SetIntensity _aslight_component (Variables|Default|GetCachedIntensity)))
              (:2
                (bind _asbp_growth_node (Utilities|Casting|CastToBP_GrowthNode _target))
                (Class|BPGrowthNode|RevertGrowth _asbp_growth_node))
              (:3
                (Transformation|SetActorTransform _target (Variables|Default|GetCachedTransform)))
              (:4
                (Rendering|SetActorHiddenInGame _target true)
                (Collision|SetActorEnableCollision _target))
              (:5
                (bind _asprimitive_component (Utilities|Casting|CastToPrimitiveComponent (Actor|GetComponentByClass _target "/Script/Engine.PrimitiveComponent")))
                (Rendering|SetCastHiddenShadow _asprimitive_component))
              (:6
                (Rendering|SetActorHiddenInGame _target)
                (Collision|SetActorEnableCollision _target true)
                (Utilities|IsValid _secondaryactor
                  (:"Is Valid"
                    (Rendering|SetActorHiddenInGame _secondaryactor true)
                    (Collision|SetActorEnableCollision _secondaryactor))))
              (:7
                (bind _asaudio_component (Utilities|Casting|CastToAudioComponent (Actor|GetComponentByClass _target "/Script/Engine.AudioComponent")))
                (Audio|Components|Audio|SetPaused _asaudio_component))
              (:8
                (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _target))
                (Class|BPFixture|RenameFixture _asbp_fixture (Variables|Default|GetCachedFixtureID)))
              (:9
                (bind _asbp_airlock (Utilities|Casting|CastToBP_Airlock _target))
                (Class|BPAirlock|ApplyLoopBack _asbp_airlock))))))))))
'''
    print('Writing BP_AnomalySocket:Revert...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{AS}:Revert'}, 'code': balance(REVERT)})
    print('Compiling BP_AnomalySocket...')
    c_as = M.bp('compile_blueprint', {'blueprint': {'refPath': AS}})
    print('  compile BP_AnomalySocket ->', c_as)

    # 6. Add PlayedBehindAudioThisRound to BP_RoundManager
    vars_rm = json.loads(M.bp('list_variables', {'blueprint': {'refPath': RM}})).get('returnValue', [])
    if 'PlayedBehindAudioThisRound' not in vars_rm:
        print('Adding PlayedBehindAudioThisRound to BP_RoundManager...')
        M.bp('add_variable', {'blueprint': {'refPath': RM}, 'name': 'PlayedBehindAudioThisRound', 'type_name': 'bool'})

    # 7. Add CheckProximitySpook to BP_RoundManager
    ensure_fns(RM, ['CheckProximitySpook'])
    SPOOK = '''(fn CheckProximitySpook ()
  (if (>= (Variables|Default|GetCurrentRound) 4)
    (if (not (Variables|Default|GetPlayedBehindAudioThisRound))
      (if (< (Math|Random|RandomFloatInRange 0.0 1.0) 0.25)
        (Variables|Default|SetPlayedBehindAudioThisRound true)
        (bind pawn (Game|GetPlayerPawn 0))
        (bind pLoc (Transformation|GetActorLocation pawn))
        (bind fwd (Math|Vector|GetForwardVector (Transformation|GetActorRotation pawn)))
        (bind behind (Math|Vector|vector-vector pLoc (Math|Vector|vector*float fwd 400.0)))
        (Audio|PlaySoundatLocation "/Game/Alien_Biomass/Audio/AMB_SewerRoomTone_Loop.AMB_SewerRoomTone_Loop" behind (Math|Rotator|MakeRotator 0.0 0.0 0.0) 0.85 1.8)))))
'''
    print('Writing BP_RoundManager:CheckProximitySpook...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:CheckProximitySpook'}, 'code': balance(SPOOK)})

    # 8. Reset PlayedBehindAudioThisRound in StartShift
    # Read existing StartShift and ensure SetPlayedBehindAudioThisRound is called
    START_SHIFT = '''(fn StartShift ()
  (bind _self self)
  (Variables|Default|SetCurrentRound (+ (Variables|Default|GetCurrentRound) 1))
  (Variables|Default|SetShiftOpen true)
  (Variables|Default|SetLastLoggedAction "")
  (Variables|Default|SetPlayedBehindAudioThisRound false)
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _array_element _outactors
    (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
    (Class|BPFixture|ResetLog _asbp_fixture))
  (CallFunction|ArmGrowth)
  (CallFunction|FindTerminal)
  (Utilities|Time|SetTimerbyFunctionName _self "RefreshTerminal" 0.3)
  (CallFunction|SaveShiftState)
  (Utilities|IsValid (Variables|Default|GetAnomalyDirector)
    (:"Is Valid"
      (Class|BPAnomalyDirector|RollAnomalies (Variables|Default|GetAnomalyDirector) (Variables|Default|GetCurrentRound)))
    (:"Is Not Valid"
      (bind _outactors_1 (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector_C"))
      (CallFunction|CacheDirector _self _outactors_1)
      (Class|BPAnomalyDirector|RollAnomalies (Variables|Default|GetAnomalyDirector) (Variables|Default|GetCurrentRound)))))
'''
    print('Writing BP_RoundManager:StartShift...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:StartShift'}, 'code': balance(START_SHIFT)})

    print('Compiling BP_RoundManager...')
    c_rm = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('  compile BP_RoundManager ->', c_rm)

    # 9. Save assets
    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [AS, RM]}})
    print('Step 2 Observer-Reactive Anomalies & Proximity Spook successfully implemented!')

if __name__ == '__main__':
    main()
