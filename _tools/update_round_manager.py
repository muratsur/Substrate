import sys
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

def write_graph(name, code):
    r = M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:{name}'}, 'code': balance(code)})
    print(f'  write {name} -> {r[:150]}')
    return r

STARTSHIFT = '''(fn StartShift ()
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
      (bind _directors (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector_C"))
      (CallFunction|CacheDirector :Found _directors)
      (Class|BPAnomalyDirector|RollAnomalies (Variables|Default|GetAnomalyDirector) (Variables|Default|GetCurrentRound)))))
'''

def main():
    M.init()
    write_graph('StartShift', STARTSHIFT)
    c = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('compile RM ->', c[:200])
    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}})
    print('save dirty ->', s[:100])
    read = M.bp('read_graph_dsl', {'graph': {'refPath': f'{RM}:StartShift'}})
    print('readback StartShift:\n', read)

if __name__ == '__main__':
    main()
