"""Dispatcher radio: one short message per shift on the terminal (story with no art cost).
BP_RoundManager.ShowDispatch pushes INCOMING DISPATCH over the checklist, raises the terminal, plays a radio blip, and
brings the checklist back 9 s later (any log brings it back sooner). StartShift calls it at 1.5 s, or 10 s on shift 1
so the key and route tips go first. Lines start ordinary and drift; rounds 9+ (Overtime) all get the last one.
Lines are at most 28 characters (the terminal's name column) and are joined with the manager's NL variable, since the
graph DSL cannot write a newline.
Usage: python _tools/dispatcher.py   (PIE stopped), then save BP_RoundManager."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
LINES = [   # index = shift - 1
    ['MORNING, TECHNICIAN.', 'STANDARD ROUTE. LOG WHAT', 'YOU SEE, NOT WHAT YOU', 'EXPECT.'],
    ['OVERNIGHT REPORT SAYS ONE', 'FIXTURE IS OFFLINE.', 'PROBABLY PAPERWORK.'],
    ['PRESSURE IS NORMAL.', 'IGNORE THE HUM.', 'THE HUM IS ALSO NORMAL.'],
    ['SOMEONE REPORTED YOUR STOOL', 'MOVED. YOU ARE THE ONLY ONE', 'ON SHIFT.'],
    ['DO NOT LOG THE GROWTH.', 'IT IS NOT ON YOUR LIST.', 'KEEP IT THAT WAY.'],
    ['WE HEARD YOU KNOCKING', 'LAST NIGHT.', 'PLEASE STOP KNOCKING.'],
    ['YOUR LAST REPORT HAD', 'TWELVE ROWS.', 'THERE ARE ELEVEN.'],
    ['SECTOR D IS NOT ON THE', 'ROUTE. IF THE ROUTE SAYS', 'OTHERWISE, FOLLOW IT.'],
    ['...', 'THIS CHANNEL IS NOT IN USE.']]
assert all(len(l) <= 28 for m in LINES for l in m)

def joined(lines):
    """nested Append with the NL variable between lines"""
    expr = f'"{lines[-1]}"'
    for l in reversed(lines[:-1]):
        expr = f'(Utilities|String|Append "{l}" (Utilities|String|Append (Variables|Default|GetNL) {expr}))'
    return expr

def by_round(i=0):
    if i == len(LINES) - 1: return joined(LINES[i])
    return f'(select (== (Variables|Default|GetCurrentRound) {i + 1}) {joined(LINES[i])}\n      {by_round(i + 1)})'

SHOW = f'''(fn ShowDispatch ()
  (CallFunction|PushTerminal :Header "INCOMING DISPATCH" :Names
      {by_round()}
    :States "" :Footer "CHECKLIST RESUMES SHORTLY")
  (CallFunction|RaiseTerminal)
  (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Floating_UI_Open-002.Floating_UI_Open-002" 0.6 0.7)
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshTerminal" :Time 9.0))
'''

def read(g): return json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': RM + ':' + g}})).get('returnValue', '')

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    try: M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': 'ShowDispatch'})
    except Exception as e: print('ShowDispatch exists:', str(e)[:60])
    B.compile_bp(RM)
    print('ShowDispatch ->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':ShowDispatch'}, 'code': SHOW})[:300])
    s = read('StartShift')
    if 'ShowDispatch' not in s:
        old = '  (Utilities|Time|SetTimerbyFunctionName _self "ShowRouteTip" 5.5)\n'
        assert s.count(old) == 1
        new = s.replace(old, old + '  (Utilities|Time|SetTimerbyFunctionName :Object _self :FunctionName "ShowDispatch" :Time (select (== (Variables|Default|GetCurrentRound) 1) 10.0 1.5))\n')
        print('StartShift ->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':StartShift'}, 'code': new})[:200])
        print(''.join(difflib.unified_diff(s.splitlines(True), read('StartShift').splitlines(True), 'before', 'after')))
    B.compile_bp(RM)
