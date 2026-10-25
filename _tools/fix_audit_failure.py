"""Failure model per DESIGN.md section 3: 'Failure is the round not closing... you walk the route again - and the
growth has advanced. Tension escalates on failure instead of resetting.' Before: a failed audit reset the run to SHIFT 001
(SetCurrentRound 0 + StartShift), and the save file still held the old round. Now: the shift stays open, anomalies and
logged rows stay, growth is re-armed (ArmGrowth: each node may advance once more when unobserved), and the terminal
returns to the checklist. Backups: _backups/failure_20261025/."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
RED = '"(R=0.900000,G=0.050000,B=0.020000,A=1.000000)"'
CODE = {
    'OnShiftAuditFailed': f'''(fn OnShiftAuditFailed ()
  (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Invalid_Action.Invalid_Action" 1.0 0.5)
  (CameraFades|StartCameraFade (Game|GetPlayerCameraManager 0) 0.0 0.5 0.4 {RED} false true)
  (CallFunction|PushTerminal :Header "AUDIT FAILED" :Names "" :States "" :Footer (select (Variables|Default|GetAuditMissedAnomaly) "UNREPORTED CONTAMINATION | SHIFT REMAINS OPEN" "FALSE ALARM | SHIFT REMAINS OPEN"))
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "FinishAuditFailureReset" :Time 2.0))
''',
    'FinishAuditFailureReset': f'''(fn FinishAuditFailureReset ()
  (CameraFades|StopCameraFade (Game|GetPlayerCameraManager 0))
  (CameraFades|StartCameraFade (Game|GetPlayerCameraManager 0) 0.5 0.0 0.8 {RED})
  (CallFunction|ArmGrowth)
  (CallFunction|RefreshTerminal))
'''}
read = lambda g: json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'read_graph_dsl', 'arguments': {'graph': {'refPath': RM + ':' + g}}})).get('returnValue', '')
for g, code in CODE.items():
    before = read(g)
    print(g, '->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':' + g}, 'code': code})[:300])
    print(''.join(difflib.unified_diff(before.splitlines(True), read(g).splitlines(True), 'before', 'after')))
print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:200])
