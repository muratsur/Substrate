"""Player hints used PrintString, which Shipping builds compile out, so a locked airlock or an E press with nothing in
range did nothing visible. BP_RoundManager.ShowHint(Text) puts the hint in the terminal footer (the LastLoggedAction slot
RefreshTerminal already prepends) and raises the terminal; ClearHint drops it after 4 s if nothing replaced it.
Routed: airlock locked, nothing in range, west gate open, the first-shift F tip; EnterSectorD / EndDemo already push
their text to the terminal, so they now only raise it. Debug prints (director, saves, achievements) stay as they are.
Usage: python _tools/hints_on_terminal.py   (PIE stopped)"""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
M.init()
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
AL = '/Game/Substrate/Core/BP_Airlock.BP_Airlock'
read = lambda g: json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': g}})).get('returnValue', '')

def write(g, code):
    before = read(g)
    print(g.split(':')[-1], '->', M.bp('write_graph_dsl', {'graph': {'refPath': g}, 'code': code})[:300])
    print(''.join(difflib.unified_diff(before.splitlines(True), read(g).splitlines(True), 'before', 'after')))

def patch(g, old, new):
    s = read(g)
    if new in s or old not in s: print(g.split(':')[-1], 'already patched'); return
    assert s.count(old) == 1, (g, old)
    write(g, s.replace(old, new))

RAISE = '''(bind _t (Variables|Default|GetTerminal))
  (Utilities|IsValid _t
    (:"Is Valid"
      (if (not (Class|BPTerminal|GetRaised _t))
        (Class|BPTerminal|ApplyRaised _t true))))'''
CODE = {
    'RaiseTerminal': f'(fn RaiseTerminal ()\n  {RAISE})\n',
    'ShowHint': '''(fn ShowHint (Text)
  (if (Utilities|String|NotEqualExactly(String) (Variables|Default|GetLastLoggedAction) Text)
    (Variables|Default|SetHintText Text)
    (Variables|Default|SetLastLoggedAction Text)
    (CallFunction|RefreshTerminal)
    (CallFunction|RaiseTerminal)
    (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ClearHint" :Time 4.0)))
''',
    'ClearHint': '''(fn ClearHint ()
  (if (Utilities|String|EqualExactly(String) (Variables|Default|GetLastLoggedAction) (Variables|Default|GetHintText))
    (Variables|Default|SetLastLoggedAction "")
    (CallFunction|RefreshTerminal)))
''',
    'ShowFTip': '''(fn ShowFTip ()
  (if (== (Variables|Default|GetCurrentRound) 1)
    (CallFunction|ShowHint :Text "F: RAISE / STOW THIS TERMINAL")))
''',
    # rewritten whole: its read-back has '_' branches, which can't be written back
    'OpenWestGate': '''(fn OpenWestGate ()
  (if (not (Variables|Default|GetGateOpen))
    (if (<= (Variables|Default|GetTerminalRemaining) 0)
      (Variables|Default|SetGateOpen true)
      (for b (Actor|GetAllActorsWithTag "WestGateBlock")
        (CallFunction|GateHideBlock :self self :a b))
      (for l (Actor|GetAllActorsWithTag "WestGateLight")
        (Rendering|SetActorHiddenInGame :self l :bNewHidden true))
      (for g (Actor|GetAllActorsWithTag "WestGateLightGreen")
        (Rendering|SetActorHiddenInGame :self g :bNewHidden false))
      (CallFunction|ShowHint :Text "WEST GATE OPEN - ALL FIXTURES LOGGED"))))
'''}

if __name__ == '__main__':
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    have = [v['name'] if isinstance(v, dict) else v for v in json.loads(M.bp('list_variables', {'blueprint': {'refPath': RM}}))['returnValue']]
    if 'HintText' not in have: B.add_var(RM, 'HintText', 'string')
    for g in ('RaiseTerminal', 'ShowHint', 'ClearHint', 'ShowFTip'):
        try:
            M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': g})
            if g == 'ShowHint':
                print('param ->', M.bp('add_function_param', {'graph': {'refPath': RM + ':ShowHint'}, 'param_name': 'Text', 'param_type': 'string', 'input_param': True})[:120])
        except Exception as e: print(g, 'exists:', str(e)[:80])
    B.compile_bp(RM)
    for g, c in CODE.items(): write(RM + ':' + g, c)
    B.compile_bp(RM)
    patch(RM + ':LogLookedAtFixture', '(Development|PrintString "Nothing in range - look at a fixture, get within 4 m" true true "(R=0.200000,G=0.800000,B=1.000000,A=1.000000)" 4.0)',
          '(CallFunction|ShowHint :Text "NOTHING IN RANGE - LOOK AT A FIXTURE WITHIN 4 M")')
    fix_push = lambda g, h, n, st, f: patch(RM + ':' + g, f'(CallFunction|PushTerminal "{n}" "{st}" "{f}")', f'(CallFunction|PushTerminal :Header "{h}" :Names "{n}" :States "{st}" :Footer "{f}")')
    fix_push('EnterSectorD', 'SECTOR D - ACCESS GRANTED', 'C-06 RELIEF VALVE', '[ ]', 'PROCEED TO RELIEF VALVE')
    fix_push('EndDemo', 'SHIFT TERMINATED', 'SUBSTRATE DEMO COMPLETE', '', 'THANK YOU FOR PLAYING')
    patch(RM + ':EnterSectorD', '(Development|PrintString "SECTOR D - ACCESS GRANTED. PROCEED TO RELIEF VALVE." true true "(R=1.000000,G=0.800000,B=0.200000,A=1.000000)" 8.0)', '(CallFunction|RaiseTerminal)')
    patch(RM + ':EndDemo', '(Development|PrintString "SUBSTRATE DEMO COMPLETE - THANK YOU FOR PLAYING" true true "(R=0.200000,G=1.000000,B=0.500000,A=1.000000)" 10.0)', '(CallFunction|RaiseTerminal)')
    if 'ShowFTip' not in read(RM + ':StartShift'): patch(RM + ':StartShift', '  (CallFunction|SaveShiftState)\n', '  (CallFunction|SaveShiftState)\n  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ShowFTip" :Time 1.0)\n')
    B.compile_bp(RM)
    t = read(AL + ':TryTransit').replace('(CallFunction|Transit (Game|GetPlayerPawn 0))', '(CallFunction|Transit :Traveler (Game|GetPlayerPawn 0))')   # read-back is positional
    if 'ShowHint' not in t: write(AL + ':TryTransit', t.replace('(Development|PrintString "AIRLOCK LOCKED - log the fixtures on this side first (E = PASS, Q = FLAG)" true true "(R=0.000000,G=0.660000,B=1.000000,A=1.000000)" 4.0)',
          '''(bind _rm (Utilities|Casting|CastToBP_RoundManager :Object (Actor|GetActorOfClass "/Game/Substrate/Core/BP_RoundManager.BP_RoundManager_C"))
          (:then
            (Class|BPRoundManager|ShowHint :self _rm :Text "AIRLOCK LOCKED - LOG THE FIXTURES ON THIS SIDE FIRST"))
          (:CastFailed))'''))
    B.compile_bp(AL)
