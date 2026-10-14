"""T1.4 terminal: BP_RoundManager builds the checklist and pushes it to the terminal.

Run:  python _tools/terminal_manager.py fn        # create functions + params
      python _tools/terminal_manager.py graphs    # write function bodies
      python _tools/terminal_manager.py callers   # StartShift / LogLookedAtFixture
      python _tools/terminal_manager.py verify
"""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
FXCLS = '/Game/Substrate/Core/BP_Fixture.BP_Fixture_C'
TMCLS = '/Game/Substrate/Core/BP_Terminal.BP_Terminal_C'


def g(n):
    return {'refPath': RM + ':' + n}


def balance(code):
    depth = 0
    for ch in code:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
    if depth > 0:
        print('  (auto-closing', depth, 'parens)')
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code


def write(name, code):
    r = M.bp('write_graph_dsl', {'graph': g(name), 'code': balance(code)})
    print('  graph', name, '->', r[:400])
    return r


def compile_bp():
    print('  compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:300])


def add_fn(name):
    print('  fn', name, M.bp('add_function_graph', {'blueprint': {'refPath': RM},
                                                  'graph_name': name})[:150])


def add_param(fn, pname, ptype, is_input=True, obj_class=None):
    args = {'graph': g(fn), 'param_name': pname, 'input_param': is_input}
    if obj_class:
        args['object_class'] = {'refPath': obj_class}
        r = M.bp('add_object_function_param', args)
    else:
        args['param_type'] = ptype
        r = M.bp('add_function_param', args)
    print('  param', fn + '.' + pname, r[:110])


FINDT = '''(fn FindTerminal ()
  (bind terms (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Terminal.BP_Terminal_C"))
  (if (> (Utilities|Array|Length terms) 0)
    (Variables|Default|SetTerminal (Utilities|Array|Get(acopy) terms 0)))
  (bind term (Variables|Default|GetTerminal))
  (Utilities|IsValid term
    (:"Is Valid"
      (Class|BPTerminal|AttachToPlayer :self term))))
'''

ADDROW = '''(fn AddRowIfMatch (Fixture Row)
  (bind fc (Utilities|Casting|CastToBP_Fixture :Object Fixture)
    (:then
      (if (== (Class|BPFixture|GetRowOrder :self fc) Row)
        (Variables|Default|SetTerminalNames
          (Utilities|String|Append
            (Variables|Default|GetTerminalNames)
            (Utilities|String|Append
              (Utilities|String|ToString(Name) (Class|BPFixture|GetFixtureID :self fc))
              (Variables|Default|GetNL))))
        (Variables|Default|SetTerminalStates
          (Utilities|String|Append
            (Variables|Default|GetTerminalStates)
            (Utilities|String|Append
              (select (== (Class|BPFixture|GetLogResult :self fc) 0)
                "[ ]"
                (select (== (Class|BPFixture|GetLogResult :self fc) 1) "[PASS]" "[FLAG]"))
              (Variables|Default|GetNL))))
        (if (== (Class|BPFixture|IsLoggedCorrectly :self fc) false)
          (Variables|Default|SetTerminalRemaining
            (+ (Variables|Default|GetTerminalRemaining) 1)))))))
'''

PUSH = '''(fn PushTerminal (Header Names States Footer)
  (bind term (Variables|Default|GetTerminal))
  (Utilities|IsValid term
    (:"Is Valid"
      (Class|BPTerminal|ShowChecklist
        :self term
        :Header Header
        :Names Names
        :States States
        :Footer Footer))))
'''

REFRESH = '''(fn RefreshTerminal ()
  (Variables|Default|SetTerminalNames "")
  (Variables|Default|SetTerminalStates "")
  (Variables|Default|SetTerminalRemaining 0)
  (bind fxs (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (bind rowmax (+ (Variables|Default|GetRequiredRowMax) 1))
  (for i (range rowmax)
    (for f fxs
      (CallFunction|AddRowIfMatch :self self :Fixture f :Row i)))
  (bind r (Variables|Default|GetCurrentRound))
  (bind rs (Utilities|String|ToString(Integer) r))
  (bind hdr (Utilities|String|Append "SHIFT "
    (select (< r 10)
      (Utilities|String|Append "00" rs)
      (select (< r 100) (Utilities|String|Append "0" rs) rs))))
  (bind rem (Variables|Default|GetTerminalRemaining))
  (bind ftr (select (> rem 0)
    (Utilities|String|Append "CLOSE SHIFT: BLOCKED ("
      (Utilities|String|Append (Utilities|String|ToString(Integer) rem) " left)"))
    "CLOSE SHIFT: READY"))
  (if (Variables|Default|GetDebugTerminal)
    (Development|PrintString :InString (Utilities|String|Append (Utilities|String|Append hdr (Variables|Default|GetNL)) (Variables|Default|GetTerminalNames)) :Duration 6.0)
    (Development|PrintString :InString (Utilities|String|Append (Variables|Default|GetTerminalStates) ftr) :Duration 6.0))
  (CallFunction|PushTerminal
    :self self
    :Header hdr
    :Names (Variables|Default|GetTerminalNames)
    :States (Variables|Default|GetTerminalStates)
    :Footer ftr))
'''

START = '''(fn StartShift ()
  (Variables|Default|SetCurrentRound (+ (Variables|Default|GetCurrentRound) 1))
  (Variables|Default|SetShiftOpen true)
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _array_element _outactors
    (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
    (Class|BPFixture|ResetLog _asbp_fixture))
  (CallFunction|ArmGrowth)
  (CallFunction|FindTerminal)
  (CallFunction|RefreshTerminal)
  (Utilities|IsValid (Variables|Default|GetAnomalyDirector)
    (:"Is Valid"
      (Class|BPAnomalyDirector|RollAnomalies (Variables|Default|GetAnomalyDirector) (Variables|Default|GetCurrentRound)))))
'''

LOG = '''(fn LogLookedAtFixture (Result)
  (Variables|Default|SetBestDist 400.0)
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _array_element _outactors
    (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
    (bind _score (Class|BPFixture|ViewScore _asbp_fixture (Camera|GetCameraLocation (Game|GetPlayerCameraManager 0)) (Math|Vector|GetForwardVector (Camera|GetCameraRotation (Game|GetPlayerCameraManager 0)))))
    (if (< _score (Variables|Default|GetBestDist))
      (Variables|Default|SetBestDist _score)
      (Variables|Default|SetBestFixture _asbp_fixture)))
  (if (< (Variables|Default|GetBestDist) 400.0)
    (Class|BPFixture|LogFixture (Variables|Default|GetBestFixture) Result)
    (else
      (Development|PrintString "Nothing in range - look at a fixture, get within 4 m")))
  (CallFunction|RefreshTerminal))
'''


def make_fns():
    for n in ('FindTerminal', 'AddRowIfMatch', 'PushTerminal', 'RefreshTerminal'):
        add_fn(n)
    add_param('AddRowIfMatch', 'Fixture', None, True, obj_class=FXCLS)
    add_param('AddRowIfMatch', 'Row', 'int', True)
    for p in ('Header', 'Names', 'States', 'Footer'):
        add_param('PushTerminal', p, 'string', True)
    compile_bp()


def graphs():
    write('FindTerminal', FINDT)
    write('AddRowIfMatch', ADDROW)
    write('PushTerminal', PUSH)
    write('RefreshTerminal', REFRESH)
    compile_bp()


def callers():
    write('StartShift', START)
    write('LogLookedAtFixture', LOG)
    compile_bp()


def verify():
    for n in ('FindTerminal', 'AddRowIfMatch', 'PushTerminal', 'RefreshTerminal', 'StartShift',
              'LogLookedAtFixture'):
        print('==', n)
        print(json.loads(M.bp('read_graph_dsl', {'graph': g(n)}))['returnValue'])


if __name__ == '__main__':
    M.init()
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'fn'
    {'fn': make_fns, 'graphs': graphs, 'callers': callers, 'verify': verify}[cmd]()
