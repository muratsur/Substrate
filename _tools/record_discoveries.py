"""Fill in BP_RoundManager.RecordDiscoveredAnomalies, which was an empty function, so the debrief's
"CATALOGUED: n / 14" always read 0 (playtest 2026-11-08). TryCloseShift calls it on a clean close, before the debrief:
every anomaly type applied that shift (sockets stay Applied until the next StartShift) sets its bit in
DiscoveredMask, and each newly seen type adds 1 to DiscoveredCount. SaveShiftState/LoadShiftState already persist both.
Bit = 2^type via Float Power + Truncate (there is no integer shift node); exact for the 14 types (0..13).
Usage: python _tools/record_discoveries.py   (PIE stopped). Saves BP_RoundManager. Re-runnable."""
import sys
sys.path.insert(0, '_tools')
import mcpx as M
from aim_and_airlock_feedback import RM, write, ok

SOCK = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C'
RECORD = '''(fn RecordDiscoveredAnomalies ()
  (bind _outactors (Actor|GetAllActorsOfClass "%s"))
  (for _array_element _outactors
    (bind _asbp_anomaly_socket (Utilities|Casting|CastToBP_AnomalySocket _array_element))
    (bind _bit (Math|Float|Truncate (Math|Float|Power 2.0 (Class|BPAnomalySocket|GetAnomalyType _asbp_anomaly_socket))))
    (if (and (Class|BPAnomalySocket|GetApplied _asbp_anomaly_socket) (== (Math|Integer|BitwiseAND (Variables|Default|GetDiscoveredMask) _bit) 0))
      (Variables|Default|SetDiscoveredMask (Math|Integer|BitwiseOR (Variables|Default|GetDiscoveredMask) _bit))
      (Variables|Default|SetDiscoveredCount (+ (Variables|Default|GetDiscoveredCount) 1)))))
''' % SOCK

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    write(RM, 'RecordDiscoveredAnomalies', RECORD, ('BitwiseOR', 'SetDiscoveredCount', 'GetApplied'))
    print('compile', ok(M.bp('compile_blueprint', {'blueprint': {'refPath': RM}}), 'compile')[:100])
    print('save', M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM]}})[:80])
