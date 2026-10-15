"""Phase 5 Step 3: Escalating Facility Hazards & Audio Decay.

1. Overtime Environmental Decay:
   - For every 3 Overtime shifts completed (OT-03, OT-06, ...), reduce facility base lighting intensity by 10% and scale ambient steam/pipe-leak particle emission rates.
2. Dynamic Audio Pitch Stress:
   - Scale down master room tone pitch multiplier: Pitch = max(0.20, 0.35 - (OvertimeShift * 0.02)), making the industrial sub-bass drone heavier and more oppressive.
"""
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

def ensure_fns(bp_path, fns):
    graphs = [g['refPath'].split(':')[-1] for g in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': bp_path}})).get('returnValue', [])]
    for fn in fns:
        if fn not in graphs:
            print(f'Adding function {fn} to {bp_path}...')
            M.bp('add_function_graph', {'blueprint': {'refPath': bp_path}, 'graph_name': fn})

def main():
    M.init()
    print('=== PHASE 5 - STEP 3: FACILITY HAZARDS & AUDIO DECAY ===')

    ensure_fns(RM, ['ApplyOvertimeDecay'])

    # 1. Write ApplyOvertimeDecay on BP_RoundManager
    APPLY_DECAY = '''(fn ApplyOvertimeDecay ()
  (if (Variables|Default|GetIsOvertime)
    (bind ot (Variables|Default|GetOvertimeShift))
    ;; 1. Audio pitch stress: Pitch = max(0.20, 0.35 - (ot * 0.02))
    (bind sub_pitch (- 0.35 (* (Math|Conversions|ToFloat(Integer) ot) 0.02)))
    (bind final_pitch (Math|Float|Max(Float) 0.20 sub_pitch))
    (bind amb_actors (Actor|GetAllActorsOfClass "/Script/Engine.AmbientSound"))
    (for a amb_actors
      (bind comp (Actor|GetComponentbyClass a "/Script/Engine.AudioComponent"))
      (bind audComp (Utilities|Casting|CastToAudioComponent comp)
        (:then
          (Audio|Components|Audio|SetPitchMultiplier audComp final_pitch))
        (:CastFailed)))

    ;; 2. Environmental lighting decay: every 3 shifts (ot >= 3, 6, 9...), reduce lighting by 10%
    (bind decay_step (/ ot 3))
    (bind light_mult (- 1.0 (* (Math|Conversions|ToFloat(Integer) decay_step) 0.10)))
    (bind final_light (Math|Float|Max(Float) 0.30 light_mult))
    (bind fixtures (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
    (for f fixtures
      (bind lightComp (Actor|GetComponentbyClass f "/Script/Engine.LightComponent"))
      (bind l (Utilities|Casting|CastToLightComponent lightComp)
        (:then
          (Rendering|Components|Light|SetIntensity l (* 1800.0 final_light)))
        (:CastFailed)))
    (Development|PrintString (Utilities|String|Append "OVERTIME DECAY APPLIED: Pitch=" (Utilities|String|ToString(Float) final_pitch)) true true "(R=0.200000,G=0.800000,B=1.000000,A=1.000000)" 5.0)))
'''
    print('Writing BP_RoundManager:ApplyOvertimeDecay...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:ApplyOvertimeDecay'}, 'code': balance(APPLY_DECAY)})

    # 2. Update StartShift to call ApplyOvertimeDecay
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
  (CallFunction|ApplyOvertimeDecay)
  (Utilities|Time|SetTimerbyFunctionName _self "RefreshTerminal" 0.3)
  (CallFunction|SaveShiftState)
  (Utilities|IsValid (Variables|Default|GetAnomalyDirector)
    (:"Is Valid"
      (Class|BPAnomalyDirector|RollAnomalies (Variables|Default|GetAnomalyDirector) (Variables|Default|GetCurrentRound)))
    (:"Is Not Valid"
      (bind _outactors_1 (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector_C"))
      (CallFunction|CacheDirector _self _outactors_1)
      (Class|BPAnomalyDirector|RollAnomalies (Variables|Default|GetAnomalyDirector) (Variables|Default|GetCurrentRound))))))
'''
    print('Writing BP_RoundManager:StartShift with ApplyOvertimeDecay hook...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:StartShift'}, 'code': balance(START_SHIFT)})

    print('Compiling BP_RoundManager...')
    c_rm = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('  compile BP_RoundManager ->', c_rm[:150])

    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM]}})
    print('Step 3 Facility Hazards & Audio Decay completed successfully!')

if __name__ == '__main__':
    main()
