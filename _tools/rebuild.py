"""Clear every authored graph and write it once, cleanly.

write_graph_dsl appends, and pruning orphans turned out to be unsafe (it can
delete pure data nodes whose pin connections the tool does not report on the
output side).  Clearing the nodes first and writing once leaves exactly one
chain per graph.
"""
import sys
import json
import time
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B

PINK = '(R=1.000000,G=0.400000,B=0.400000,A=1.000000)'
ORANGE = '(R=1.000000,G=0.800000,B=0.200000,A=1.000000)'
CYAN = '(R=0.600000,G=1.000000,B=1.000000,A=1.000000)'


def balanced(code):
    d = code.count('(') - code.count(')')
    return code.rstrip('\n') + ')' * d + '\n' if d > 0 else code


def clear(graph, keep=('K2Node_FunctionEntry', 'K2Node_FunctionResult', 'AddEvent', 'KeyboardEvents')):
    r = json.loads(M.bp('find_nodes', {'graph': {'refPath': graph}, 'title': ''}))['returnValue']
    infos = json.loads(M.bp('get_node_infos', {'nodes': r}))['returnValue'] if r else []
    n = 0
    for node in infos:
        ref = node['node']['refPath']
        tid = node.get('type_id', '')
        if any(k in ref or k in tid for k in keep):
            continue
        M.bp('delete_node', {'node': {'refPath': ref}})
        n += 1
    print('  cleared', n, 'of', len(infos), 'in', graph.split(':')[-1])


def write(graph, code):
    r = M.bp('write_graph_dsl', {'graph': {'refPath': graph}, 'code': balanced(code)})
    print('  wrote', graph.split(':')[-1], r[:200])
    return r


SOCKET = B.SOCKET
DIRECTOR = B.DIRECTOR

SOCKET_APPLY = '''(fn Apply (Round)
  (Variables|Default|SetApplied false)
  (if (not (CallFunction|CanApply :self self :Round Round))
    (return false))
  (bind target (CallFunction|GetTarget))
  (bind kind (Variables|Default|GetAnomalyType))
  (Utilities|IsValid target
    (:"Is Valid"
      (if (== kind 0)
        (bind fixA (Utilities|Casting|CastToBP_Fixture :Object target)
          (:then
            (Variables|Default|SetCachedState (Class|BPFixture|GetFixtureState :self fixA))
            (Class|BPFixture|ApplyFixtureState :self fixA :NewState 2)
            (Development|PrintString "ANOMALY: a checklist fixture has gone - it is still on your list" true true "%(pink)s" 7.0)
            (Variables|Default|SetApplied true)
            (Variables|Default|SetLastAppliedRound Round)
            (return true))
          (:CastFailed
            (Variables|Default|SetCachedState 0)
            (Rendering|SetActorHiddenInGame :self target :bNewHidden true)
            (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision false)
            (Development|PrintString "ANOMALY: something that was here is gone" true true "%(pink)s" 7.0)
            (Variables|Default|SetApplied true)
            (Variables|Default|SetLastAppliedRound Round)
            (return true))))
      (if (== kind 1)
        (bind compL (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.LightComponent"))
        (bind lightL (Utilities|Casting|CastToLightComponent :Object compL)
          (:then
            (Variables|Default|SetCachedIntensity (Class|LightComponentBase|GetIntensity :self lightL))
            (Rendering|Components|Light|SetIntensity :self lightL :NewIntensity (Variables|Default|GetLightIntensity))
            (Development|PrintString "ANOMALY: a light is wrong" true true "%(pink)s" 7.0)
            (Variables|Default|SetApplied true)
            (Variables|Default|SetLastAppliedRound Round)
            (return true))
          (:CastFailed
            (return false))))
      (if (== kind 2)
        (bind growG (Utilities|Casting|CastToBP_GrowthNode :Object target)
          (:then
            (Class|BPGrowthNode|ForceAdvance :self growG)
            (Variables|Default|SetApplied true)
            (Variables|Default|SetLastAppliedRound Round)
            (return true))
          (:CastFailed
            (return false))))
      (if (== kind 3)
        (Variables|Default|SetCachedTransform (Transformation|GetActorTransform :self target))
        (bind locD (Transformation|GetActorLocation :self target))
        (Transformation|SetActorLocation
          :self target
          :NewLocation (+ locD (Variables|Default|GetOffset))
          :bSweep false)
        (Development|PrintString "ANOMALY: not where it was" true true "%(pink)s" 7.0)
        (Variables|Default|SetApplied true)
        (Variables|Default|SetLastAppliedRound Round)
        (return true))
      (Development|PrintString "ANOMALY: socket has an unknown type code" false false "%(pink)s" 5.0)
      (return false))
    (:"Is Not Valid"
      (Development|PrintString "ANOMALY socket has no target - check the level" false false "%(pink)s" 6.0)
      (return false)))
''' % {'pink': PINK}

SOCKET_REVERT = '''(fn Revert ()
  (if (not (Variables|Default|GetApplied))
    (return))
  (if (== (Variables|Default|GetRevertRule) 1)
    (return))
  (Variables|Default|SetApplied false)
  (bind target (CallFunction|GetTarget))
  (bind kind (Variables|Default|GetAnomalyType))
  (Utilities|IsValid target
    (:"Is Valid"
      (if (== kind 0)
        (bind fixR (Utilities|Casting|CastToBP_Fixture :Object target)
          (:then
            (Class|BPFixture|ApplyFixtureState :self fixR :NewState (Variables|Default|GetCachedState))
            (Development|PrintString "ANOMALY reverted: it is back on the rack" false false "%(cyan)s" 4.0))
          (:CastFailed
            (Rendering|SetActorHiddenInGame :self target :bNewHidden false)
            (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision true)
            (Development|PrintString "ANOMALY reverted: it is back" false false "%(cyan)s" 4.0))))
      (if (== kind 1)
        (bind compR (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.LightComponent"))
        (bind lightR (Utilities|Casting|CastToLightComponent :Object compR)
          (:then
            (Rendering|Components|Light|SetIntensity :self lightR :NewIntensity (Variables|Default|GetCachedIntensity))
            (Development|PrintString "ANOMALY reverted: the light is back" false false "%(cyan)s" 4.0))
          (:CastFailed)))
      (if (== kind 2)
        (Development|PrintString "ANOMALY: growth stays - it never reverts" false false "%(cyan)s" 4.0))
      (if (== kind 3)
        (Transformation|SetActorTransform :self target :NewTransform (Variables|Default|GetCachedTransform) :bSweep false)
        (Development|PrintString "ANOMALY reverted: it is where it was" false false "%(cyan)s" 4.0)))
    (:"Is Not Valid")))
''' % {'cyan': CYAN}

DIR_APPLYONE = '''(fn ApplyOne (TypeCode Round)
  (bind n (CallFunction|CountCandidates :self self :TypeCode TypeCode :Round Round))
  (if (< n 1)
    (return false))
  (bind idx (Math|Random|RandomIntegerinRange 0 (- n 1)))
  (bind chosen (CallFunction|PickByIndex :self self :TypeCode TypeCode :Round Round :Wanted idx))
  (bind ok (Class|BPAnomalySocket|Apply :self chosen :Round Round))
  (if ok
    (Variables|Default|SetAppliedCount (+ (Variables|Default|GetAppliedCount) 1))
    (else))
  (if ok
    (Development|PrintString (Class|BPAnomalySocket|GetNote :self chosen) true true "%(pink)s" 7.0)
    (else))
  (return ok))
''' % {'pink': PINK}

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


DIR_CACHESOCKETS = '''(fn CacheSockets ()
  (Variables|Default|SetSockets (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C"))
  (Development|PrintString
    (Utilities|String|Append "AnomalyDirector: anomaly sockets = " (Utilities|String|ToString(Integer) (Utilities|Array|Length (Variables|Default|GetSockets))))
    true true "(R=1.000000,G=0.800000,B=0.200000,A=1.000000)" 5.0))
'''

DIR_BEGINPLAY = '''(event EventBeginPlay
  (CallFunction|CacheSockets))
'''

DIR_ROLL = '''(fn RollAnomalies (Round)
  (CallFunction|CacheSockets :self self)
  (CallFunction|RevertApplied :self self)
  (Variables|Default|SetCurrentRound Round)
  (Variables|Default|SetBudget (Math|Random|RandomIntegerinRange
                                 (CallFunction|GetBudgetMin :self self :Round Round)
                                 (CallFunction|GetBudgetMax :self self :Round Round)))
  (for k (range (Variables|Default|GetBudget))
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
        (Utilities|String|Append " of budget " (Utilities|String|ToString(Integer) (Variables|Default|GetBudget)))))
    true true "(R=1.000000,G=0.800000,B=0.200000,A=1.000000)" 6.0))
'''


def director_cache():
    print('== director socket caching')
    M.bp('add_function_graph', {'blueprint': {'refPath': B.DIRECTOR},
                                'graph_name': 'CacheSockets'})
    if 'Budget' not in json.loads(M.bp('list_variables', {'blueprint': {'refPath': B.DIRECTOR}}))['returnValue']:
        B.add_var(B.DIRECTOR, 'Budget', 'int')
    for name, code in (('CacheSockets', DIR_CACHESOCKETS), ('EventGraph', DIR_BEGINPLAY),
                       ('RollAnomalies', DIR_ROLL)):
        g = B.DIRECTOR + ':' + name
        clear(g)
        write(g, code)
    print('  compile', M.bp('compile_blueprint', {'blueprint': {'refPath': B.DIRECTOR}})[:120])


def socket():
    print('== socket')
    for name, code in (('GetTarget', B.SOCKET_GETTARGET), ('CanApply', B.SOCKET_CANAPPLY),
                       ('Apply', SOCKET_APPLY), ('Revert', SOCKET_REVERT),
                       ('EventGraph', B.SOCKET_BEGINPLAY)):
        g = SOCKET + ':' + name
        clear(g)
        write(g, code)
    print('  compile', M.bp('compile_blueprint', {'blueprint': {'refPath': SOCKET}})[:120])


def director():
    print('== director')
    for name, code in (('EventGraph', B.DIR_BEGINPLAY), ('GetBudgetMin', B.DIR_GETBUDGETMIN),
                       ('GetBudgetMax', B.DIR_GETBUDGETMAX), ('PickType', B.DIR_PICKTYPE),
                       ('CountCandidates', B.DIR_COUNTCANDIDATES), ('PickByIndex', B.DIR_PICKBYINDEX),
                       ('ApplyOne', DIR_APPLYONE), ('RevertApplied', DIR_REVERTAPPLIED),
                       ('RollAnomalies', B.DIR_ROLL)):
        g = DIRECTOR + ':' + name
        clear(g)
        write(g, code)
    print('  compile', M.bp('compile_blueprint', {'blueprint': {'refPath': DIRECTOR}})[:120])


def main():
    M.init()
    socket()
    director()


if __name__ == '__main__':
    main()
