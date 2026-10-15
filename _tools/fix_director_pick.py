"""Fix PickByIndex, CountCandidates, and ApplyOne in BP_AnomalyDirector."""
import sys
sys.path.insert(0, '_tools')
import mcpx as M

DIR = '/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

def write_graph(name, code):
    r = M.bp('write_graph_dsl', {'graph': {'refPath': f'{DIR}:{name}'}, 'code': balance(code)})
    print(f'  write {name} -> {r[:150]}')
    return r

COUNTCANDIDATES = '''(fn CountCandidates (TypeCode Round)
  (Variables|Default|SetCandidates 0)
  (for _array_element (Variables|Default|GetSockets)
    (bind s (Utilities|Casting|CastToBP_AnomalySocket :Object _array_element)
      (:then
        (bind code (Class|BPAnomalySocket|GetAnomalyType :self s))
        (bind ok (Class|BPAnomalySocket|CanApply :self s :Round Round))
        (if (and (== code TypeCode) ok)
          (Variables|Default|SetCandidates (+ (Variables|Default|GetCandidates) 1))))
      (:CastFailed)))
  (return (Variables|Default|GetCandidates)))
'''

PICKBYINDEX = '''(fn PickByIndex (TypeCode Round Wanted)
  (Variables|Default|SetScanIndex 0)
  (for _array_element (Variables|Default|GetSockets)
    (bind s (Utilities|Casting|CastToBP_AnomalySocket :Object _array_element)
      (:then
        (bind code (Class|BPAnomalySocket|GetAnomalyType :self s))
        (bind ok (Class|BPAnomalySocket|CanApply :self s :Round Round))
        (if (and (== code TypeCode) ok)
          (if (== (Variables|Default|GetScanIndex) Wanted)
            (Variables|Default|SetPickSock s)
            (else
              (Variables|Default|SetScanIndex (+ (Variables|Default|GetScanIndex) 1))))))
      (:CastFailed)))
  (return (Variables|Default|GetPickSock)))
'''

APPLYONE = '''(fn ApplyOne (TypeCode Round)
  (bind _count (CallFunction|CountCandidates :self self :TypeCode TypeCode :Round Round))
  (if (< _count 1)
    (return false)
    (else
      (bind _wanted (Math|Random|RandomIntegerInRange 0 (- _count 1)))
      (bind _chosen (CallFunction|PickByIndex :self self :TypeCode TypeCode :Round Round :Wanted _wanted))
      (bind _applied (Class|BPAnomalySocket|Apply :self _chosen :Round Round))
      (if _applied
        (Variables|Default|SetAppliedCount (+ (Variables|Default|GetAppliedCount) 1)))
      (return _applied))))
'''

def main():
    M.init()
    write_graph('CountCandidates', COUNTCANDIDATES)
    write_graph('PickByIndex', PICKBYINDEX)
    write_graph('ApplyOne', APPLYONE)
    c = M.bp('compile_blueprint', {'blueprint': {'refPath': DIR}})
    print('compile DIR ->', c[:200])
    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}})
    print('save dirty ->', s[:100])

if __name__ == '__main__':
    main()
