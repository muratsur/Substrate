"""Step 4: Add the remaining 6 Anomaly types to BP_AnomalySocket (Codes 0..9) & BP_Airlock."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

SOCKET = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket'
AIRLOCK = '/Game/Substrate/Core/BP_Airlock.BP_Airlock'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

def setup_vars():
    # 1. Add SecondaryActor to BP_AnomalySocket
    s_vars = json.loads(M.bp('list_variables', {'blueprint': {'refPath': SOCKET}}))['returnValue']
    if 'SecondaryActor' not in s_vars:
        print('Adding SecondaryActor to BP_AnomalySocket...')
        M.bp('add_object_variable', {
            'blueprint': {'refPath': SOCKET},
            'name': 'SecondaryActor',
            'object_class': {'refPath': '/Script/Engine.Actor'}
        })
    M.bp('set_variable_instance_editable', {
        'blueprint': {'refPath': SOCKET},
        'variable_name': 'SecondaryActor',
        'instance_editable': True
    })

    # 2. Add LoopBackThisOnce to BP_Airlock
    a_vars = json.loads(M.bp('list_variables', {'blueprint': {'refPath': AIRLOCK}}))['returnValue']
    if 'LoopBackThisOnce' not in a_vars:
        print('Adding LoopBackThisOnce to BP_Airlock...')
        M.bp('add_variable', {
            'blueprint': {'refPath': AIRLOCK},
            'name': 'LoopBackThisOnce',
            'type_name': 'bool'
        })

    # 3. Add ApplyLoopBack function to BP_Airlock
    a_fns = [x['refPath'].split(':')[-1] for x in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': AIRLOCK}}))['returnValue']]
    if 'ApplyLoopBack' not in a_fns:
        print('Adding ApplyLoopBack function to BP_Airlock...')
        M.bp('add_function_graph', {'blueprint': {'refPath': AIRLOCK}, 'graph_name': 'ApplyLoopBack'})
        M.bp('add_function_param', {
            'graph': {'refPath': f'{AIRLOCK}:ApplyLoopBack'},
            'param_name': 'Enable',
            'param_type': 'bool',
            'input_param': True
        })

APPLY_LOOPBACK = '''(fn ApplyLoopBack (Enable)
  (Variables|Default|SetLoopBackThisOnce Enable))
'''

AIRLOCK_TRANSIT = '''(fn Transit (Traveler)
  (if (Variables|Default|GetLoopBackThisOnce)
    (Variables|Default|SetLoopBackThisOnce false)
    (CallFunction|Disarm self)
    (Transformation|SetActorLocation Traveler (Transformation|GetActorLocation self))
    (CallFunction|FaceNearestFixture self Traveler)
    (else
      (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Airlock.BP_Airlock_C"))
      (for _array_element _outactors
        (if (!= _array_element self)
          (bind _asbp_airlock (Utilities|Casting|CastToBP_Airlock _array_element)
            (:then
              (CallFunction|Disarm _asbp_airlock)
              (Transformation|SetActorLocation Traveler (Transformation|GetActorLocation _array_element))
              (CallFunction|FaceNearestFixture _asbp_airlock Traveler))
            (:CastFailed)))))))
'''

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
          (Variables|Default|SetApplied true)
          (Variables|Default|SetLastAppliedRound Round)
          (return true))
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
        (:8)
        (:9
          (bind airR9 (Utilities|Casting|CastToBP_Airlock :Object target)
            (:then
              (Class|BPAirlock|ApplyLoopBack :self airR9 :Enable false))
            (:CastFailed)))
        (:Default)))
    (:"Is Not Valid")))
'''

def main():
    M.init()
    setup_vars()
    print('Writing ApplyLoopBack to BP_Airlock...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{AIRLOCK}:ApplyLoopBack'}, 'code': balance(APPLY_LOOPBACK)})

    print('Writing Transit to BP_Airlock...')
    r_a = M.bp('write_graph_dsl', {'graph': {'refPath': f'{AIRLOCK}:Transit'}, 'code': balance(AIRLOCK_TRANSIT)})
    print('  Transit ->', r_a[:150])
    c_a = M.bp('compile_blueprint', {'blueprint': {'refPath': AIRLOCK}})
    print('  compile Airlock ->', c_a[:150])

    print('Writing Apply to BP_AnomalySocket...')
    r_ap = M.bp('write_graph_dsl', {'graph': {'refPath': f'{SOCKET}:Apply'}, 'code': balance(SOCKET_APPLY)})
    print('  Apply ->', r_ap[:150])

    print('Writing Revert to BP_AnomalySocket...')
    r_rv = M.bp('write_graph_dsl', {'graph': {'refPath': f'{SOCKET}:Revert'}, 'code': balance(SOCKET_REVERT)})
    print('  Revert ->', r_rv[:150])

    c_s = M.bp('compile_blueprint', {'blueprint': {'refPath': SOCKET}})
    print('  compile Socket ->', c_s[:150])

    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}})
    print('save dirty ->', s[:100])

if __name__ == '__main__':
    main()
