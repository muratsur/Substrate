"""Step 6: Implement Persistence (BP_SubstrateSave) (T1.6 / Section 5.8)."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

SAVE = '/Game/Substrate/Core/BP_SubstrateSave.BP_SubstrateSave'
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

def setup_save_asset():
    # Variables on BP_SubstrateSave
    svars = json.loads(M.bp('list_variables', {'blueprint': {'refPath': SAVE}}))['returnValue']
    for v in ['SavedRound', 'GrowthEarlyStage', 'GrowthLateStage', 'GrowthTransStage']:
        if v not in svars:
            print(f'Adding variable {v} to BP_SubstrateSave...')
            M.bp('add_variable', {'blueprint': {'refPath': SAVE}, 'name': v, 'type_name': 'int'})

    # Functions on BP_SubstrateSave
    sfns = [x['refPath'].split(':')[-1] for x in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': SAVE}}))['returnValue']]
    if 'ApplySaveData' not in sfns:
        print('Adding ApplySaveData to BP_SubstrateSave...')
        M.bp('add_function_graph', {'blueprint': {'refPath': SAVE}, 'graph_name': 'ApplySaveData'})
        M.bp('add_function_param', {
            'graph': {'refPath': f'{SAVE}:ApplySaveData'},
            'param_name': 'Round',
            'param_type': 'int',
            'input_param': True
        })
    if 'GetSavedRound' not in sfns:
        print('Adding GetSavedRound to BP_SubstrateSave...')
        M.bp('add_function_graph', {'blueprint': {'refPath': SAVE}, 'graph_name': 'GetSavedRound'})
        M.bp('add_function_param', {
            'graph': {'refPath': f'{SAVE}:GetSavedRound'},
            'param_name': 'Round',
            'param_type': 'int',
            'input_param': False
        })

APPLY_SAVE_DATA = '''(fn ApplySaveData (Round)
  (Variables|Default|SetSavedRound Round))
'''

GET_SAVED_ROUND = '''(fn GetSavedRound ()
  (return (Variables|Default|GetSavedRound)))
'''

def setup_rm_fns():
    rfns = [x['refPath'].split(':')[-1] for x in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': RM}}))['returnValue']]
    for fn in ['SaveShiftState', 'LoadShiftState']:
        if fn not in rfns:
            print(f'Adding {fn} to BP_RoundManager...')
            M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': fn})

SAVE_SHIFT_STATE = '''(fn SaveShiftState ()
  (if (> (Variables|Default|GetCurrentRound) 1)
    (bind obj (SaveGame|CreateSaveGameObject :SaveGameClass "/Game/Substrate/Core/BP_SubstrateSave.BP_SubstrateSave_C"))
    (bind ssave (Utilities|Casting|CastToBP_SubstrateSave :Object obj)
      (:then
        (Class|BPSubstrateSave|ApplySaveData :self ssave :Round (Variables|Default|GetCurrentRound))
        (SaveGame|SaveGametoSlot :SaveGameObject ssave :SlotName "Substrate_0" :UserIndex 0)
        (Development|PrintString "Game saved to slot Substrate_0" false false "(R=0.200000,G=0.800000,B=1.000000,A=1.000000)" 3.0))
      (:CastFailed))))
'''

LOAD_SHIFT_STATE = '''(fn LoadShiftState ()
  (bind exists (SaveGame|DoesSaveGameExist :SlotName "Substrate_0" :UserIndex 0))
  (if exists
    (bind obj (SaveGame|LoadGamefromSlot :SlotName "Substrate_0" :UserIndex 0))
    (bind ssave (Utilities|Casting|CastToBP_SubstrateSave :Object obj)
      (:then
        (bind r (Class|BPSubstrateSave|GetSavedRound :self ssave))
        (if (> r 1)
          (Variables|Default|SetCurrentRound (- r 1))
          (Development|PrintString (Utilities|String|Append "Loaded save game: Round " (Utilities|String|ToString(Integer) r)) true true "(R=0.200000,G=0.800000,B=1.000000,A=1.000000)" 5.0)))
      (:CastFailed))))
'''

STARTSHIFT_SAVED = '''(fn StartShift ()
  (Variables|Default|SetCurrentRound (+ (Variables|Default|GetCurrentRound) 1))
  (Variables|Default|SetShiftOpen true)
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _array_element _outactors
    (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
    (Class|BPFixture|ResetLog _asbp_fixture))
  (CallFunction|ArmGrowth)
  (CallFunction|FindTerminal)
  (Utilities|Time|SetTimerbyFunctionName self "RefreshTerminal" 0.3)
  (Utilities|IsValid (Variables|Default|GetAnomalyDirector)
    (:"Is Valid"
      (Class|BPAnomalyDirector|RollAnomalies (Variables|Default|GetAnomalyDirector) (Variables|Default|GetCurrentRound)))
    (:"Is Not Valid"
      (bind _outactors_1 (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector_C"))
      (CallFunction|CacheDirector _outactors_1)
      (Class|BPAnomalyDirector|RollAnomalies (Variables|Default|GetAnomalyDirector) (Variables|Default|GetCurrentRound))))
  (CallFunction|SaveShiftState))
'''

EVENT_GRAPH = '''(event EventBeginPlay
  (CallFunction|LoadShiftState)
  (CallFunction|StartShift)
  (Input|EnableInput (Game|GetPlayerController 0)))

(event Collision|EventActorBeginOverlap (OtherActor)
  (Utilities|Casting|CastToCharacter OtherActor)
  (CallFunction|TryCloseShift))

(event EventTick (DeltaSeconds))

(event E (Key))

(event Q (Key))
'''

def main():
    M.init()
    setup_save_asset()
    print('Writing ApplySaveData...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{SAVE}:ApplySaveData'}, 'code': balance(APPLY_SAVE_DATA)})
    print('Writing GetSavedRound...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{SAVE}:GetSavedRound'}, 'code': balance(GET_SAVED_ROUND)})
    c_s = M.bp('compile_blueprint', {'blueprint': {'refPath': SAVE}})
    print('compile BP_SubstrateSave ->', c_s[:150])

    setup_rm_fns()
    print('Writing SaveShiftState...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:SaveShiftState'}, 'code': balance(SAVE_SHIFT_STATE)})
    print('Writing LoadShiftState...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:LoadShiftState'}, 'code': balance(LOAD_SHIFT_STATE)})
    print('Writing StartShift...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:StartShift'}, 'code': balance(STARTSHIFT_SAVED)})
    print('Writing EventGraph...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:EventGraph'}, 'code': balance(EVENT_GRAPH)})

    c_r = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('compile BP_RoundManager ->', c_r[:150])

    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}})
    print('save dirty ->', s[:100])

if __name__ == '__main__':
    main()
