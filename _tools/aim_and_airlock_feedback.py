"""Two feedback fixes from the 2026-11-08 playtest (presses went to the wrong fixture, and the airlock said "log the
fixtures first" when every row was logged but one was wrong).
1. Aim readout: BP_RoundManager.UpdateAim runs every 0.2 s while a shift is open, picks the fixture E/Q would log
   (same ViewScore rule as LogLookedAtFixture: nearest within 4 m and ~37 deg of the camera) and shows
   "AIMING AT: <id>" above the terminal footer. The terminal only redraws when the aimed fixture changes.
2. Airlock lock message says how many rows are not logged, or how many are logged wrong, without naming them.
Also puts the terminal footer's hint and close-shift status on two lines instead of "a | b" (it ran off the panel).
Usage: python _tools/aim_and_airlock_feedback.py   (PIE stopped). Saves both Blueprints. Re-runnable."""
import sys, json, re
sys.path.insert(0, '_tools')
import mcpx as M
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
AL = '/Game/Substrate/Core/BP_Airlock.BP_Airlock'
FIX = '/Game/Substrate/Core/BP_Fixture.BP_Fixture_C'

UPDATE_AIM = '''(fn UpdateAim ()
  (if (and (Variables|Default|GetShiftOpen) (not (Variables|Default|GetTitleMode)))
    (Variables|Default|SetAimDist 400.0)
    (Variables|Default|SetAimBest "")
    (bind _outactors (Actor|GetAllActorsOfClass "%s"))
    (for _array_element _outactors
      (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
      (bind _score (Class|BPFixture|ViewScore _asbp_fixture (Camera|GetCameraLocation (Game|GetPlayerCameraManager 0)) (Math|Vector|GetForwardVector (Camera|GetCameraRotation (Game|GetPlayerCameraManager 0)))))
      (if (< _score (Variables|Default|GetAimDist))
        (Variables|Default|SetAimDist _score)
        (Variables|Default|SetAimBest (Utilities|String|ToString(Name) (Class|BPFixture|GetFixtureID _asbp_fixture)))))
    (if (Utilities|String|NotEqualExactly(String) (Variables|Default|GetAimBest) (Variables|Default|GetAimFixtureID))
      (Variables|Default|SetAimFixtureID (Variables|Default|GetAimBest))
      (CallFunction|RefreshTerminal))))
''' % FIX

# RefreshTerminal: an "AIMING AT:" line on top of the footer (AddRowIfMatch can't be rewritten: one of its nodes
# does not survive a DSL round trip, so the row itself is not marked)
AIM_OLD = '(Variables|Default|GetTerminalNames) (Variables|Default|GetTerminalStates) _returnvalue_22)'
AIM_NEW = ('(Variables|Default|GetTerminalNames) (Variables|Default|GetTerminalStates) (Utilities|String|Append (select (> (Utilities|String|Len (Variables|Default|GetAimFixtureID)) 0) '
           '(Utilities|String|Append (Utilities|String|Append "AIMING AT: " (Variables|Default|GetAimFixtureID)) (Variables|Default|GetNL)) "") _returnvalue_22))')
# StartShift: start the aim timer next to the existing looping lab flicker
SHIFT_OLD = '(Utilities|Time|SetTimerbyFunctionName _self "FlickerDLab" 0.15 true)'
SHIFT_NEW = SHIFT_OLD + '\n  (Utilities|Time|SetTimerbyFunctionName _self "UpdateAim" 0.2 true)'
# RefreshTerminal footer: hint and status on separate lines
FOOT_OLD = '(Utilities|String|Append _lastloggedaction " | ")'
FOOT_NEW = '(Utilities|String|Append _lastloggedaction (Variables|Default|GetNL))'

LOCKED_OLD = '"AIRLOCK LOCKED - LOG THE FIXTURES ON THIS SIDE FIRST"'
LOCKED_NEW = ('(select (> (Variables|Default|GetUnlogged) 0) '
              '(Utilities|String|Append (Utilities|String|Append "AIRLOCK LOCKED - " (Utilities|String|ToString(Integer) (Variables|Default|GetUnlogged))) " ROW(S) NOT LOGGED") '
              '(Utilities|String|Append (Utilities|String|Append "AIRLOCK LOCKED - " (Utilities|String|ToString(Integer) (Variables|Default|GetPending))) " ROW(S) LOGGED WRONG"))')
GATE_OLD = '(Variables|Default|SetPending 0)'
GATE_NEW = '(Variables|Default|SetPending 0)\n  (Variables|Default|SetUnlogged 0)'
PEND_OLD = '(Variables|Default|SetPending (+ (Variables|Default|GetPending) 1))'
PEND_NEW = PEND_OLD + '\n      (if (== (Class|BPFixture|GetLogResult _asbp_fixture) 0) (Variables|Default|SetUnlogged (+ (Variables|Default|GetUnlogged) 1)))'

def ok(r, what):
    if any(m in str(r).lower() for m in ('"iserror": true', '"iserror":true', 'does not exist', 'could not', 'traceback', 'cannot rebind', 'assertionerror', 'expects only')):
        raise SystemExit(f'{what} failed; nothing saved:\n{str(r)[:1500]}')
    return r

def read(bp, g):
    return json.loads(ok(M.bp('read_graph_dsl', {'graph': {'refPath': f'{bp}:{g}'}}), 'read ' + g)).get('returnValue', '')

def inline_literals(src):
    """Readback emits (bind _x 10) / (bind _x "text") lines that write_graph_dsl rejects; inline them."""
    for name, lit in re.findall(r'^\s*\(bind (_\w+) (-?\d+(?:\.\d+)?|"[^"]*")\)\s*$', src, re.M):
        src = re.sub(r'^\s*\(bind %s %s\)\s*\n' % (re.escape(name), re.escape(lit)), '', src, flags=re.M)
        src = re.sub(r'%s(?![\w])' % re.escape(name), lit.replace('\\', '\\\\'), src)
    return src

# readback drops the explicit self target on some self calls; writing it back then binds the first arg to self
ROUNDTRIP_FIXES = (('(CallFunction|Transit (Game|GetPlayerPawn 0))', '(CallFunction|Transit self (Game|GetPlayerPawn 0))'),)

def write(bp, g, code, must):
    code = inline_literals(code)
    for a, b in ROUNDTRIP_FIXES: code = code.replace(a, b)
    r = M.bp('write_graph_dsl', {'graph': {'refPath': f'{bp}:{g}'}, 'code': code})
    if not r.lstrip().startswith('{'): raise SystemExit(f'write {g} failed; nothing saved:\n{r[:1500]}')
    ok(r, 'write ' + g)
    back = read(bp, g)
    miss = [m for m in must if m not in back]
    if miss: raise SystemExit(f'{g} readback missing {miss}; nothing saved')
    print(g, 'written and read back')

def patch(bp, g, old, new, marker):
    src = read(bp, g)
    if marker in src: print(g, 'already patched'); return
    if src.count(old) != 1: raise SystemExit(f'{g}: expected exactly one {old!r}, found {src.count(old)}; nothing saved')
    write(bp, g, src.replace(old, new), (marker,))

def add_var(bp, name, type_name):
    if name not in M.bp('list_variables', {'blueprint': {'refPath': bp}}):
        ok(M.bp('add_variable', {'blueprint': {'refPath': bp}, 'name': name, 'type_name': type_name}), 'add ' + name)

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    for n, t in (('AimFixtureID', 'string'), ('AimBest', 'string'), ('AimDist', 'float')): add_var(RM, n, t)
    add_var(AL, 'Unlogged', 'int')
    graphs = [g['refPath'].split(':')[-1] for g in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': RM}}))['returnValue']]
    if 'UpdateAim' not in graphs: ok(M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': 'UpdateAim'}), 'add UpdateAim')
    write(RM, 'UpdateAim', UPDATE_AIM, ('ViewScore', 'SetAimFixtureID', 'RefreshTerminal'))
    patch(RM, 'RefreshTerminal', AIM_OLD, AIM_NEW, 'AIMING AT')
    patch(RM, 'StartShift', SHIFT_OLD, SHIFT_NEW, '"UpdateAim"')
    patch(RM, 'RefreshTerminal', FOOT_OLD, FOOT_NEW, 'Append _lastloggedaction _nl')
    patch(AL, 'GateOpen', GATE_OLD, GATE_NEW, 'SetUnlogged 0')
    patch(AL, 'GateOpen', PEND_OLD, PEND_NEW, 'GetLogResult')
    patch(AL, 'TryTransit', LOCKED_OLD, LOCKED_NEW, 'NOT LOGGED')
    for bp in (AL, RM):
        print('compile', bp.split('.')[-1], ok(M.bp('compile_blueprint', {'blueprint': {'refPath': bp}}), 'compile')[:120])
    print('save', M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [AL, RM]}})[:100])
