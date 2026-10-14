"""Build the Substrate anomaly system.

Usage:  python _tools/build_anomalies.py [step ...]
Steps are idempotent-ish; each writes graphs and compiles.
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

SOCKET = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket'
DIRECTOR = '/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector'
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
GROWTH = '/Game/Substrate/Core/BP_GrowthNode.BP_GrowthNode'


def g(bp, name):
    return {'refPath': bp + ':' + name}


def balance(code):
    '''Append any missing closing parens (quoted literals here are balanced).'''
    depth = code.count('(') - code.count(')')
    if depth > 0:
        print('  (auto-closing', depth, 'parens in', code.splitlines()[0][:40] + ')', flush=True)
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code


def write_graph(bp, name, code):
    r = M.bp('write_graph_dsl', {'graph': g(bp, name), 'code': balance(code)})
    print('  graph', name, '->', r[:400])
    return r


def add_var(bp, name, type_name, container=None, obj_class=None):
    args = {'blueprint': {'refPath': bp}, 'name': name}
    if obj_class:
        args['object_class'] = {'refPath': obj_class}
        if container:
            args['container_type'] = container
        r = M.bp('add_object_variable', args)
    elif type_name:
        args['type_name'] = type_name
        if container:
            args['container_type'] = container
        r = M.bp('add_variable', args)
    print('  var', name, '->', r[:200])
    return r


def editable(bp, *names):
    for n in names:
        print('  editable', n, M.bp('set_variable_instance_editable',
                                    {'blueprint': {'refPath': bp},
                                     'variable_name': n, 'instance_editable': True})[:120])


def compile_bp(bp):
    r = M.bp('compile_blueprint', {'blueprint': {'refPath': bp}})
    print('  compile ->', r[:600])


def check(bp):
    r = M.bp('list_variables', {'blueprint': {'refPath': bp}})
    print('  vars:', r[:600])


def step_socket_vars():
    print('== socket vars')
    for n, t in [('AnomalyType', 'Int'), ('TargetTag', 'Name'), ('MinRound', 'Int'),
                 ('MaxRound', 'Int'), ('Severity', 'Float'), ('CooldownRounds', 'Int'),
                 ('RevertRule', 'Int'), ('Offset', 'Vector'), ('LightIntensity', 'Float'),
                 ('Note', 'String'), ('Applied', 'Bool'), ('LastAppliedRound', 'Int'),
                 ('CachedTransform', 'Transform'), ('CachedIntensity', 'Float'),
                 ('CachedState', 'Int')]:
        add_var(SOCKET, n, t)
    add_var(SOCKET, 'TargetActor', None, obj_class='/Script/Engine.Actor')
    editable(SOCKET, 'AnomalyType', 'TargetTag', 'TargetActor', 'MinRound', 'MaxRound',
             'Severity', 'CooldownRounds', 'RevertRule', 'Offset', 'LightIntensity', 'Note')
    check(SOCKET)


def step_director_vars():
    print('== director vars')
    for n, t in [('CurrentRound', 'Int'), ('BandFromRound', 'Int'), ('BandToRound', 'Int'),
                 ('BandMin', 'Int'), ('BandMax', 'Int'),
                 ('WAbsence', 'Float'), ('WLight', 'Float'), ('WGrowth', 'Float'),
                 ('WDisplacement', 'Float'),
                 ('AppliedThisRound', 'Object'), ('Sockets', 'Object')]:
        if t == 'Object':
            add_var(DIRECTOR, n, None, container='ARRAY',
                    obj_class='/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C')
        else:
            add_var(DIRECTOR, n, t, container='ARRAY' if n.startswith('Band') or n.startswith('W') else None)
    check(DIRECTOR)


def add_fn(bp, name):
    print('  fn', name, M.bp('add_function_graph',
                              {'blueprint': {'refPath': bp}, 'graph_name': name})[:120])


def add_param(bp, fn, pname, ptype, is_input=True, container=None):
    args = {'graph': g(bp, fn), 'param_name': pname, 'param_type': ptype,
            'input_param': is_input}
    if container:
        args['container_type'] = container
    print('  param', fn + '.' + pname, M.bp('add_function_param', args)[:120])


def step_socket_fns():
    print('== socket functions')
    for n in ('GetTarget', 'CanApply', 'Apply', 'Revert'):
        add_fn(SOCKET, n)
    add_param(SOCKET, 'CanApply', 'Round', 'int', True)
    add_param(SOCKET, 'CanApply', 'CanApply', 'bool', False)
    add_param(SOCKET, 'Apply', 'Round', 'int', True)
    add_param(SOCKET, 'Apply', 'Applied', 'bool', False)
    add_param(SOCKET, 'GetTarget', 'Target', 'Actor', False)


GROWTH_FORCE = '''(fn ForceAdvance ()
  (bind idx (Variables|Default|GetStageIndex))
  (bind stages (Variables|Default|GetGrowthStages))
  (if (< idx (Utilities|Array|Length stages))
    (Components|StaticMesh|SetStaticMesh
      :self (Variables|Default|GetStaticMeshComponent)
      :NewMesh (Utilities|Array|Get(acopy) stages idx))
    (else
      (if (> (Utilities|Array|Length stages) 0)
        (Components|StaticMesh|SetStaticMesh
          :self (Variables|Default|GetStaticMeshComponent)
          :NewMesh (Utilities|Array|Get(acopy) stages (- (Utilities|Array|Length stages) 1))))))
  (bind scales (Variables|Default|GetGrowthScales))
  (if (< idx (Utilities|Array|Length scales))
    (Transformation|SetActorScale3D
      :self self
      :NewScale3D (Math|Vector|MakeVector
                    :X (Utilities|Array|Get(acopy) scales idx)
                    :Y (Utilities|Array|Get(acopy) scales idx)
                    :Z (Utilities|Array|Get(acopy) scales idx))))
  (Variables|Default|SetStageIndex (+ idx 1))
  (Variables|Default|SetUnobservedTime 0.0)
  (Variables|Default|SetEligibleThisRound false)
  (Development|PrintString "GROWTH: forced a stage (anomaly)" false false "(R=0.400000,G=1.000000,B=0.400000,A=1.000000)" 4.0))
'''

GROWTH_REVERT = '''(fn RevertGrowth ()
  (bind idx (- (Variables|Default|GetStageIndex) 1))
  (if (>= idx 0)
    (Variables|Default|SetStageIndex idx)
    (bind stages (Variables|Default|GetGrowthStages))
    (if (< idx (Utilities|Array|Length stages))
      (Components|StaticMesh|SetStaticMesh
        :self (Variables|Default|GetStaticMeshComponent)
        :NewMesh (Utilities|Array|Get(acopy) stages idx)))
    (bind scales (Variables|Default|GetGrowthScales))
    (if (< idx (Utilities|Array|Length scales))
      (Transformation|SetActorScale3D
        :self self
        :NewScale3D (Math|Vector|MakeVector
                      :X (Utilities|Array|Get(acopy) scales idx)
                      :Y (Utilities|Array|Get(acopy) scales idx)
                      :Z (Utilities|Array|Get(acopy) scales idx))))))
'''


def step_growth_graphs():
    print('== growth functions')
    for n in ('ForceAdvance', 'RevertGrowth'):
        add_fn(GROWTH, n)
    write_graph(GROWTH, 'ForceAdvance', GROWTH_FORCE)
    write_graph(GROWTH, 'RevertGrowth', GROWTH_REVERT)
    compile_bp(GROWTH)


def reset_fn(bp, name, params):
    print('  reset fn', name, M.bp('remove_function_graph',
                                  {'blueprint': {'refPath': bp}, 'graph_name': name})[:120])
    add_fn(bp, name)
    for p in params:
        if p[1] == 'Actor':
            print('  param', M.bp('add_object_function_param',
                                  {'graph': g(bp, name), 'param_name': p[0],
                                   'object_class': {'refPath': '/Script/Engine.Actor'},
                                   'input_param': p[2]})[:100])
        else:
            add_param(bp, name, p[0], p[1], p[2])


SOCKET_GETTARGET = '''(fn GetTarget ()
  (bind direct (Variables|Default|GetTargetActor))
  (bind arr (Actor|GetAllActorsWithTag (Variables|Default|GetTargetTag)))
  (Utilities|IsValid direct
    (:"Is Valid"
      (return direct))
    (:"Is Not Valid"
      (if (> (Utilities|Array|Length arr) 0)
        (return (Utilities|Array|Get(acopy) arr 0))
        (else
          (return)))))
'''

SOCKET_CANAPPLY = '''(fn CanApply (Round)
  (if (< Round (Variables|Default|GetMinRound))
    (return false))
  (bind maxr (Variables|Default|GetMaxRound))
  (if (and (!= maxr 0) (> Round maxr))
    (return false))
  (bind last (Variables|Default|GetLastAppliedRound))
  (if (and (!= last 0) (<= (- Round last) (Variables|Default|GetCooldownRounds)))
    (return false))
  (return true))
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
        (:Default
          (Development|PrintString
            (Utilities|String|Append "Socket: unknown anomaly type code " (Utilities|String|ToString(Integer) (Variables|Default|GetAnomalyType)))
            false false "(R=1.000000,G=0.400000,B=0.200000,A=1.000000)" 5.0)
          (return false))))
    (:"Is Not Valid"
      (Development|PrintString "Socket: no target resolved" false false "(R=1.000000,G=0.400000,B=0.200000,A=1.000000)" 5.0)
      (return false)))
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
        (:Default)))
    (:"Is Not Valid")))
'''

SOCKET_BEGINPLAY = '''(event EventBeginPlay
  (Rendering|SetActorHiddenInGame :self self :bNewHidden true))
'''


def step_socket_graphs():
    print('== socket graphs')
    reset_fn(SOCKET, 'GetTarget', [('Target', 'Actor', False)])
    reset_fn(SOCKET, 'Apply', [('Round', 'int', True), ('Applied', 'bool', False)])
    reset_fn(SOCKET, 'Revert', [])
    write_graph(SOCKET, 'EventGraph', SOCKET_BEGINPLAY)
    write_graph(SOCKET, 'GetTarget', SOCKET_GETTARGET)
    write_graph(SOCKET, 'CanApply', SOCKET_CANAPPLY)
    write_graph(SOCKET, 'Apply', SOCKET_APPLY)
    write_graph(SOCKET, 'Revert', SOCKET_REVERT)
    compile_bp(SOCKET)


DIR_GETBUDGETMIN = '''(fn GetBudgetMin (Round)
  (return (select (<= Round 1) 0
            (select (<= Round 7) 1
              (select (<= Round 14) 2 3)))))
'''

DIR_GETBUDGETMAX = '''(fn GetBudgetMax (Round)
  (return (select (<= Round 1) 0
            (select (== Round 2) 1
              (select (<= Round 7) 2
                (select (<= Round 14) 3 5))))))
'''

DIR_PICKTYPE = '''(fn PickType (Round)
  (if (<= Round 2)
    (return 0)
    (else
      (bind roll (Math|Random|RandomFloatinRange 0.0 1.0))
      (bind late (> Round 7))
      (bind tA (select late 0.3 0.4))
      (bind tL (select late 0.55 0.8))
      (bind tG (select late 0.75 1.0))
      (if (< roll tA)
        (return 0)
        (elif (< roll tL)
          (return 1)
          (elif (< roll tG)
            (return 2)
            (else
              (return 3))))))))
'''

DIR_COUNTCANDIDATES = '''(fn CountCandidates (TypeCode Round)
  (Variables|Default|SetCandidates 0)
  (for a (Variables|Default|GetSockets)
    (bind s (Utilities|Casting|CastToBP_AnomalySocket :Object a)
      (:then
        (bind code (Class|BPAnomalySocket|GetAnomalyType :self s))
        (bind ok (Class|BPAnomalySocket|CanApply :self s :Round Round))
        (if (and (== code TypeCode) ok)
          (Variables|Default|SetCandidates (+ (Variables|Default|GetCandidates) 1))
          (else)))
      (:CastFailed)))
  (return (Variables|Default|GetCandidates)))
'''

DIR_PICKBYINDEX = '''(fn PickByIndex (TypeCode Round Wanted)
  (Variables|Default|SetScanIndex 0)
  (for a (Variables|Default|GetSockets)
    (bind s (Utilities|Casting|CastToBP_AnomalySocket :Object a)
      (:then
        (bind code (Class|BPAnomalySocket|GetAnomalyType :self s))
        (bind ok (Class|BPAnomalySocket|CanApply :self s :Round Round))
        (bind match (and (== code TypeCode) ok))
        (if (and match (== (Variables|Default|GetScanIndex) Wanted))
          (Variables|Default|SetPickSock s)
          (elif match
            (Variables|Default|SetScanIndex (+ (Variables|Default|GetScanIndex) 1))
            (else))))
      (:CastFailed)))
  (return (Variables|Default|GetPickSock)))
'''

DIR_APPLYONE = '''(fn ApplyOne (TypeCode Round)
  (bind n (CallFunction|CountCandidates :self self :TypeCode TypeCode :Round Round))
  (if (< n 1)
    (return false)
    (else
      (bind idx (Math|Random|RandomIntegerinRange 0 (- n 1)))
      (bind chosen (CallFunction|PickByIndex :self self :TypeCode TypeCode :Round Round :Wanted idx))
      (bind ok (Class|BPAnomalySocket|Apply :self chosen :Round Round))
      (if ok
        (Variables|Default|SetAppliedCount (+ (Variables|Default|GetAppliedCount) 1))
        (else))
      (return ok))))
'''

DIR_REVERTAPPLIED = '''(fn RevertApplied ()
  (for a (Variables|Default|GetSockets)
    (bind s (Utilities|Casting|CastToBP_AnomalySocket :Object a)
      (:then
        (bind live (Class|BPAnomalySocket|GetApplied :self s))
        (if live
          (Class|BPAnomalySocket|Revert :self s)
          (else)))
      (:CastFailed)))
  (Variables|Default|SetAppliedCount 0))
'''

DIR_ROLL = '''(fn RollAnomalies (Round)
  (CallFunction|RevertApplied :self self)
  (Variables|Default|SetCurrentRound Round)
  (bind budget (Math|Random|RandomIntegerinRange
                 (CallFunction|GetBudgetMin :self self :Round Round)
                 (CallFunction|GetBudgetMax :self self :Round Round)))
  (for k (range budget)
    (bind code (CallFunction|PickType :self self :Round Round))
    (bind ok (CallFunction|ApplyOne :self self :TypeCode code :Round Round))
    (if ok
      (else
        (bind fallback (CallFunction|ApplyOne :self self :TypeCode 0 :Round Round)))))
  (if (and (== Round 2) (== (Variables|Default|GetAppliedCount) 0))
    (bind forced (CallFunction|ApplyOne :self self :TypeCode 0 :Round Round))
    (else))
  (Development|PrintString
    (Utilities|String|Append
      (Utilities|String|Append "SHIFT " (Utilities|String|ToString(Integer) Round))
      (Utilities|String|Append
        (Utilities|String|Append " anomalies applied: " (Utilities|String|ToString(Integer) (Variables|Default|GetAppliedCount)))
        (Utilities|String|Append " of budget " (Utilities|String|ToString(Integer) budget))))
    true true "(R=1.000000,G=0.800000,B=0.200000,A=1.000000)" 6.0))
'''

DIR_BEGINPLAY = '''(event EventBeginPlay
  (Variables|Default|SetSockets (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C"))
  (Development|PrintString
    (Utilities|String|Append "AnomalyDirector: anomaly sockets in level = " (Utilities|String|ToString(Integer) (Utilities|Array|Length (Variables|Default|GetSockets))))
    true true "(R=1.000000,G=0.800000,B=0.200000,A=1.000000)" 5.0))
'''

SOCKET_C = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C'


def step_director_v2():
    print('== director vars v2')
    for dead in ('Sockets', 'AppliedThisRound', 'EligibleTemp', 'BandFromRound', 'BandToRound',
                 'BandMin', 'BandMax', 'WAbsence', 'WLight', 'WGrowth', 'WDisplacement'):
        M.bp('remove_variable', {'blueprint': {'refPath': DIRECTOR}, 'name': dead})
    print('  flush', M.bp('compile_blueprint', {'blueprint': {'refPath': DIRECTOR}})[:80])
    add_var(DIRECTOR, 'Sockets', None, container='ARRAY', obj_class='/Script/Engine.Actor')
    for n in ('CurrentRound', 'AppliedCount', 'Candidates', 'ScanIndex'):
        add_var(DIRECTOR, n, 'int')
    add_var(DIRECTOR, 'PickSock', None, obj_class=SOCKET_C)
    print('  flush', M.bp('compile_blueprint', {'blueprint': {'refPath': DIRECTOR}})[:80])
    check(DIRECTOR)


def step_director_graphs_v2():
    print('== director graphs v2')
    fns = ('GetBudgetMin', 'GetBudgetMax', 'PickType', 'CountCandidates',
           'PickByIndex', 'ApplyOne', 'RevertApplied', 'RollAnomalies')
    for n in fns:
        print('  drop', n, M.bp('remove_function_graph',
                                {'blueprint': {'refPath': DIRECTOR}, 'graph_name': n})[:60])
    print('  flush', M.bp('compile_blueprint', {'blueprint': {'refPath': DIRECTOR}})[:80])
    print('  graphs now:', [x['refPath'].split(':')[-1] for x in json.loads(
        M.bp('list_graphs', {'blueprint': {'refPath': DIRECTOR}}))['returnValue']])
    for n in fns:
        add_fn(DIRECTOR, n)
    add_param(DIRECTOR, 'GetBudgetMin', 'Round', 'int', True)
    add_param(DIRECTOR, 'GetBudgetMin', 'Min', 'int', False)
    add_param(DIRECTOR, 'GetBudgetMax', 'Round', 'int', True)
    add_param(DIRECTOR, 'GetBudgetMax', 'Max', 'int', False)
    add_param(DIRECTOR, 'PickType', 'Round', 'int', True)
    add_param(DIRECTOR, 'PickType', 'TypeCode', 'int', False)
    add_param(DIRECTOR, 'CountCandidates', 'TypeCode', 'int', True)
    add_param(DIRECTOR, 'CountCandidates', 'Round', 'int', True)
    add_param(DIRECTOR, 'CountCandidates', 'Count', 'int', False)
    add_param(DIRECTOR, 'PickByIndex', 'TypeCode', 'int', True)
    add_param(DIRECTOR, 'PickByIndex', 'Round', 'int', True)
    add_param(DIRECTOR, 'PickByIndex', 'Wanted', 'int', True)
    print('  ret PickByIndex', M.bp('add_object_function_param', {
        'graph': g(DIRECTOR, 'PickByIndex'), 'param_name': 'Chosen',
        'object_class': {'refPath': SOCKET_C}, 'input_param': False})[:100])
    add_param(DIRECTOR, 'ApplyOne', 'TypeCode', 'int', True)
    add_param(DIRECTOR, 'ApplyOne', 'Round', 'int', True)
    add_param(DIRECTOR, 'ApplyOne', 'Applied', 'bool', False)
    add_param(DIRECTOR, 'RollAnomalies', 'Round', 'int', True)
    for name, code in (('EventGraph', DIR_BEGINPLAY), ('GetBudgetMin', DIR_GETBUDGETMIN),
                       ('GetBudgetMax', DIR_GETBUDGETMAX), ('PickType', DIR_PICKTYPE),
                       ('CountCandidates', DIR_COUNTCANDIDATES),
                       ('PickByIndex', DIR_PICKBYINDEX), ('ApplyOne', DIR_APPLYONE),
                       ('RevertApplied', DIR_REVERTAPPLIED), ('RollAnomalies', DIR_ROLL)):
        write_graph(DIRECTOR, name, code)
    compile_bp(DIRECTOR)


if __name__ == '__main__':
    M.init()
    steps = sys.argv[1:] or ['socket_vars']
    for s in steps:
        globals()['step_' + s]()
