"""Wire BP_RoundManager: cache the anomaly director, roll anomalies each shift."""
import sys
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
DIRCLASS = '/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector_C'


def g(name):
    return {'refPath': RM + ':' + name}


STARTSHIFT = '''(fn StartShift ()
  (Variables|Default|SetCurrentRound (+ (Variables|Default|GetCurrentRound) 1))
  (Variables|Default|SetShiftOpen true)
  (bind fixtures (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for fi fixtures
    (bind fx (Utilities|Casting|CastToBP_Fixture :Object fi)
      (:then
        (Class|BPFixture|ResetLog :self fx))
      (:CastFailed)))
  (CallFunction|ArmGrowth)
  (Utilities|IsValid (Variables|Default|GetAnomalyDirector)
    (:"Is Valid"
      (Class|BPAnomalyDirector|RollAnomalies :self (Variables|Default|GetAnomalyDirector) :Round (Variables|Default|GetCurrentRound)))
    (:"Is Not Valid")))
'''

BEGINPLAY = '''(event EventBeginPlay
  (bind dirs (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector_C"))
  (CallFunction|CacheDirector :self self :Found dirs)
  (CallFunction|StartShift)
  (Input|EnableInput (Game|GetPlayerController 0)))
'''

CACHEDIRECTOR = '''(fn CacheDirector (Found)
  (Utilities|IsValid (Utilities|Array|Get(acopy) Found 0)
    (:"Is Valid"
      (bind d0 (Utilities|Casting|CastToBP_AnomalyDirector :Object (Utilities|Array|Get(acopy) Found 0))
        (:then
          (Variables|Default|SetAnomalyDirector d0))
        (:CastFailed)))
    (:"Is Not Valid"
      (Development|PrintString "RoundManager: no BP_AnomalyDirector in the level - anomaly system OFF" false false "(R=1.000000,G=0.400000,B=0.200000,A=1.000000)" 8.0))))
'''

OVERLAP = '''(event Collision|EventActorBeginOverlap (OtherActor)
  (Utilities|Casting|CastToCharacter :Object OtherActor
    (:then
      (CallFunction|TryCloseShift))
    (:CastFailed)))
'''


def balance(code):
    depth = code.count('(') - code.count(')')
    return code.rstrip('\n') + ')' * depth + '\n' if depth > 0 else code


def main():
    M.init()
    import json as _json
    have = _json.loads(M.bp('list_variables', {'blueprint': {'refPath': RM}}))['returnValue']
    for dup in [v for v in have if v.endswith('_0')]:
        print('rm dup', dup, M.bp('remove_variable', {'blueprint': {'refPath': RM},
                                                    'name': dup})[:60])
    if 'AnomalyDirector' not in have:
        print('add AnomalyDirector var', M.bp('add_object_variable', {
            'blueprint': {'refPath': RM}, 'name': 'AnomalyDirector',
            'object_class': {'refPath': DIRCLASS}})[:120])
    M.bp('set_variable_instance_editable', {'blueprint': {'refPath': RM},
                                            'variable_name': 'AnomalyDirector',
                                            'instance_editable': False})
    print('flush', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:80])
    print('vars', M.bp('list_variables', {'blueprint': {'refPath': RM}})[:300])
    print('fn CacheDirector', M.bp('add_function_graph', {
        'blueprint': {'refPath': RM}, 'graph_name': 'CacheDirector'})[:120])
    print('  param', M.bp('add_object_function_param', {
        'graph': g('CacheDirector'), 'param_name': 'Found',
        'object_class': {'refPath': '/Script/Engine.Actor'}, 'input_param': True,
        'container_type': 'ARRAY'})[:100])
    print('graph CacheDirector', M.bp('write_graph_dsl', {
        'graph': g('CacheDirector'), 'code': balance(CACHEDIRECTOR)})[:400])
    print('graph EventGraph', M.bp('write_graph_dsl', {
        'graph': g('EventGraph'), 'code': balance(BEGINPLAY + '\n' + OVERLAP)})[:400])
    print('prune EventGraph:')
    import prune
    prune.prune(RM + ':EventGraph', dry=False)
    print('graph StartShift', M.bp('write_graph_dsl', {
        'graph': g('StartShift'), 'code': balance(STARTSHIFT)})[:400])
    print('compile', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:300])


if __name__ == '__main__':
    main()
