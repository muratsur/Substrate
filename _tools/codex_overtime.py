"""Codex and Overtime decay: two systems that had their storage built but never ran.
- RecordDiscoveredAnomalies was empty although DiscoveredMask / DiscoveredCount are saved and loaded. It now runs as
  intended from TryCloseShift on a clean close: every anomaly type (0-13) with an applied socket that shift sets its bit
  in DiscoveredMask and bumps DiscoveredCount. The title shows DOCUMENTED n / 14 ANOMALY TYPES (overtime_title.py).
  The bit for type t is built by doubling CodexBit through the loop (no shift or power node needed).
- ApplyOvertimeDecay (ambient pitch sinks, fixture catch-lights dim as OvertimeShift grows) was never called; StartShift
  now calls it 0.6 s in. It does nothing outside Overtime.
Usage: python _tools/codex_overtime.py   (PIE stopped), then save BP_RoundManager."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
SOCK = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C'
TYPES = 14
read = lambda g: json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': RM + ':' + g}})).get('returnValue', '')
RECORD = f'''(fn RecordDiscoveredAnomalies ()
  (Variables|Default|SetCodexBit 1)
  (for t (range {TYPES})
    (Variables|Default|SetCodexHit false)
    (for s (Actor|GetAllActorsOfClass "{SOCK}")
      (bind _k (Utilities|Casting|CastToBP_AnomalySocket s))
      (if (and (Class|BPAnomalySocket|GetApplied _k) (== (Class|BPAnomalySocket|GetAnomalyType _k) t))
        (Variables|Default|SetCodexHit true)))
    (if (and (Variables|Default|GetCodexHit) (== (Math|Integer|BitwiseAND (Variables|Default|GetDiscoveredMask) (Variables|Default|GetCodexBit)) 0))
      (Variables|Default|SetDiscoveredMask (Math|Integer|BitwiseOR (Variables|Default|GetDiscoveredMask) (Variables|Default|GetCodexBit)))
      (Variables|Default|SetDiscoveredCount (+ (Variables|Default|GetDiscoveredCount) 1)))
    (Variables|Default|SetCodexBit (* (Variables|Default|GetCodexBit) 2))))
'''

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    have = [v['name'] if isinstance(v, dict) else v for v in json.loads(M.bp('list_variables', {'blueprint': {'refPath': RM}}))['returnValue']]
    if 'CodexBit' not in have: B.add_var(RM, 'CodexBit', 'int')
    if 'CodexHit' not in have: B.add_var(RM, 'CodexHit', 'bool')
    B.compile_bp(RM)
    before = read('RecordDiscoveredAnomalies')
    print('Record ->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':RecordDiscoveredAnomalies'}, 'code': RECORD})[:250])
    print(''.join(difflib.unified_diff(before.splitlines(True), read('RecordDiscoveredAnomalies').splitlines(True), 'before', 'after')))
    s = read('StartShift')
    if 'ApplyOvertimeDecay' not in s:
        old = '  (Utilities|Time|SetTimerbyFunctionName _self "AttachFlashlight" 0.5)\n'
        assert s.count(old) == 1
        print('StartShift ->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':StartShift'}, 'code': s.replace(old, old +
              '  (Utilities|Time|SetTimerbyFunctionName :Object _self :FunctionName "ApplyOvertimeDecay" :Time 0.6)\n')})[:200])
    B.compile_bp(RM)
