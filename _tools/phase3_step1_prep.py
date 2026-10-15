"""Phase 3 Prep: Add RenameFixture to BP_Fixture and update BP_AnomalySocket Case 8."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

FIX = '/Game/Substrate/Core/BP_Fixture.BP_Fixture'
SOCK = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

def setup_fixture():
    fns = [x['refPath'].split(':')[-1] for x in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': FIX}}))['returnValue']]
    if 'RenameFixture' not in fns:
        print('Adding RenameFixture function to BP_Fixture...')
        M.bp('add_function_graph', {'blueprint': {'refPath': FIX}, 'graph_name': 'RenameFixture'})
        M.bp('add_function_param', {
            'graph': {'refPath': f'{FIX}:RenameFixture'},
            'param_name': 'NewID',
            'param_type': 'String',
            'input_param': True
        })
    code = '''(fn RenameFixture (NewID)
  (Variables|Default|SetFixtureID (Utilities|String|StringToName NewID)))
'''
    r = M.bp('write_graph_dsl', {'graph': {'refPath': f'{FIX}:RenameFixture'}, 'code': balance(code)})
    print('  write RenameFixture ->', r[:150])
    c = M.bp('compile_blueprint', {'blueprint': {'refPath': FIX}})
    print('  compile BP_Fixture ->', c[:150])

def setup_socket():
    svars = json.loads(M.bp('list_variables', {'blueprint': {'refPath': SOCK}}))['returnValue']
    if 'CachedFixtureID' not in svars:
        print('Adding CachedFixtureID to BP_AnomalySocket...')
        M.bp('add_variable', {'blueprint': {'refPath': SOCK}, 'name': 'CachedFixtureID', 'type_name': 'String'})

    SOCKET_APPLY = '''(fn Apply (Round)
  (Variables|Default|SetApplied false)
  (if (not (CallFunction|CanApply :self self :Round Round))
    (return false))
  (bind target (CallFunction|GetTarget))
  (Utilities|IsValid target
    (:"Is Valid"
      (switch int (Variables|Default|GetAnomalyType)
        (:0
          (bind fixA (Utilities|Casting|CastToBP_Fixture :Object target)
            (:then
              (Variables|Default|SetCachedState (Class|BPFixture|GetFixtureState :self fixA))
              (Class|BPFixture|ApplyFixtureState :self fixA :NewState 2)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (Variables|Default|SetCachedState 0)
              (Rendering|SetActorHiddenInGame :self target :bNewHidden true)
              (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision false)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))))
        (:1
          (bind compL (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.LightComponent"))
          (bind lightL (Utilities|Casting|CastToLightComponent :Object compL)
            (:then
              (Variables|Default|SetCachedIntensity (Class|LightComponentBase|GetIntensity :self lightL))
              (Rendering|Components|Light|SetIntensity :self lightL :NewIntensity (Variables|Default|GetLightIntensity))
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (return false))))
        (:2
          (bind growG (Utilities|Casting|CastToBP_GrowthNode :Object target)
            (:then
              (Class|BPGrowthNode|ForceAdvance :self growG)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (return false))))
        (:3
          (Variables|Default|SetCachedTransform (Transformation|GetActorTransform :self target))
          (bind locD (Transformation|GetActorLocation :self target))
          (Transformation|SetActorLocation
            :self target
            :NewLocation (+ locD (Variables|Default|GetOffset))
            :bSweep false)
          (Variables|Default|SetApplied true)
          (Variables|Default|SetLastAppliedRound Round)
          (return true))
        (:4
          (Rendering|SetActorHiddenInGame :self target :bNewHidden false)
          (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision true)
          (Variables|Default|SetApplied true)
          (Variables|Default|SetLastAppliedRound Round)
          (return true))
        (:5
          (bind compP (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.PrimitiveComponent"))
          (bind primP (Utilities|Casting|CastToPrimitiveComponent :Object compP)
            (:then
              (Rendering|SetCastHiddenShadow :self primP :NewCastHiddenShadow true)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (return false))))
        (:6
          (Rendering|SetActorHiddenInGame :self target :bNewHidden true)
          (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision false)
          (Variables|Default|SetApplied true)
          (Variables|Default|SetLastAppliedRound Round)
          (bind sec (Variables|Default|GetSecondaryActor))
          (Utilities|IsValid sec
            (:"Is Valid"
              (Rendering|SetActorHiddenInGame :self sec :bNewHidden false)
              (Collision|SetActorEnableCollision :self sec :bNewActorEnableCollision true)
              (return true))
            (:"Is Not Valid"
              (return true))))
        (:7
          (bind compA (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.AudioComponent"))
          (bind audA (Utilities|Casting|CastToAudioComponent :Object compA)
            (:then
              (Audio|Components|Audio|SetPaused :self audA :bPause true)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (return false))))
        (:8
          (bind fix8 (Utilities|Casting|CastToBP_Fixture :Object target)
            (:then
              (Variables|Default|SetCachedFixtureID (Utilities|String|ToString(Name) (Class|BPFixture|GetFixtureID :self fix8)))
              (Class|BPFixture|RenameFixture :self fix8 :NewID (Variables|Default|GetNote))
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))))
        (:9
          (bind airA (Utilities|Casting|CastToBP_Airlock :Object target)
            (:then
              (Class|BPAirlock|ApplyLoopBack :self airA :Enable true)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (return false))))
        (:Default
          (return false))))
    (:"Is Not Valid"
      (Development|PrintString "ANOMALY socket has no target - check the level" false false "(R=1.000000,G=0.400000,B=0.200000,A=1.000000)" 6.0)
      (return false))))
'''

    SOCKET_REVERT = '''(fn Revert ()
  (if (not (Variables|Default|GetApplied))
    (return))
  (if (== (Variables|Default|GetRevertRule) 1)
    (return))
  (Variables|Default|SetApplied false)
  (bind target (CallFunction|GetTarget))
  (Utilities|IsValid target
    (:"Is Valid"
      (switch int (Variables|Default|GetAnomalyType)
        (:0
          (bind fixR (Utilities|Casting|CastToBP_Fixture :Object target)
            (:then
              (Class|BPFixture|ApplyFixtureState :self fixR :NewState (Variables|Default|GetCachedState)))
            (:CastFailed
              (Rendering|SetActorHiddenInGame :self target :bNewHidden false)
              (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision true))))
        (:1
          (bind compR (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.LightComponent"))
          (bind lightR (Utilities|Casting|CastToLightComponent :Object compR)
            (:then
              (Rendering|Components|Light|SetIntensity :self lightR :NewIntensity (Variables|Default|GetCachedIntensity)))
            (:CastFailed)))
        (:2
          (bind growR (Utilities|Casting|CastToBP_GrowthNode :Object target)
            (:then
              (Class|BPGrowthNode|RevertGrowth :self growR))
            (:CastFailed)))
        (:3
          (Transformation|SetActorTransform :self target :NewTransform (Variables|Default|GetCachedTransform) :bSweep false))
        (:4
          (Rendering|SetActorHiddenInGame :self target :bNewHidden true)
          (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision false))
        (:5
          (bind compR5 (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.PrimitiveComponent"))
          (bind primR5 (Utilities|Casting|CastToPrimitiveComponent :Object compR5)
            (:then
              (Rendering|SetCastHiddenShadow :self primR5 :NewCastHiddenShadow false))
            (:CastFailed)))
        (:6
          (Rendering|SetActorHiddenInGame :self target :bNewHidden false)
          (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision true)
          (bind secR (Variables|Default|GetSecondaryActor))
          (Utilities|IsValid secR
            (:"Is Valid"
              (Rendering|SetActorHiddenInGame :self secR :bNewHidden true)
              (Collision|SetActorEnableCollision :self secR :bNewActorEnableCollision false))
            (:"Is Not Valid")))
        (:7
          (bind compR7 (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.AudioComponent"))
          (bind audR7 (Utilities|Casting|CastToAudioComponent :Object compR7)
            (:then
              (Audio|Components|Audio|SetPaused :self audR7 :bPause false))
            (:CastFailed)))
        (:8
          (bind fixR8 (Utilities|Casting|CastToBP_Fixture :Object target)
            (:then
              (Class|BPFixture|RenameFixture :self fixR8 :NewID (Variables|Default|GetCachedFixtureID)))
            (:CastFailed)))
        (:9
          (bind airR9 (Utilities|Casting|CastToBP_Airlock :Object target)
            (:then
              (Class|BPAirlock|ApplyLoopBack :self airR9 :Enable false))
            (:CastFailed)))
        (:Default)))
    (:"Is Not Valid")))
'''

    print('Writing Apply to BP_AnomalySocket...')
    r_ap = M.bp('write_graph_dsl', {'graph': {'refPath': f'{SOCK}:Apply'}, 'code': balance(SOCKET_APPLY)})
    print('  Apply ->', r_ap[:150])

    print('Writing Revert to BP_AnomalySocket...')
    r_rv = M.bp('write_graph_dsl', {'graph': {'refPath': f'{SOCK}:Revert'}, 'code': balance(SOCKET_REVERT)})
    print('  Revert ->', r_rv[:150])

    c_s = M.bp('compile_blueprint', {'blueprint': {'refPath': SOCK}})
    print('  compile Socket ->', c_s[:150])

def main():
    M.init()
    setup_fixture()
    setup_socket()
    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}})
    print('save dirty ->', s[:100])

if __name__ == '__main__':
    main()
