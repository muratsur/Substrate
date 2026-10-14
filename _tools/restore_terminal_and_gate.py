"""1) Restore BP_RoundManager.RefreshTerminal from terminal_manager's template
(cleared by build_west_gate.py before the hook rewrite failed).
2) Rebuild the west-gate functions with DSL patterns proven by rebuild.py:

   - function params are added via add_object_function_param (NOT declared in
     the fn line - write_graph_dsl rejects fn-header params on this server)
   - early-return functions instead of if/else-blocks
   - no runtime light-color API: pre-place a green light, tagged
     WestGateLightGreen, hidden in editor; on open hide red + show green.

Run: python _tools/restore_terminal_and_gate.py
"""
import sys
import json
import time
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
import terminal_manager as TM

URT = TM.RM
LEV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'


def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        print(' (auto-closing %d parens)' % depth)
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code


def ensure_fn(name):
    r = M.bp('add_function_graph', {'blueprint': {'refPath': URT}, 'graph_name': name})
    print('  fn', name, '->', r[:110])


def clear(name):
    r = json.loads(M.bp('find_nodes', {'graph': {'refPath': URT + ':' + name},
                                       'title': ''}))['returnValue']
    if not r:
        print('  clear: empty', name)
        return
    infos = json.loads(M.bp('get_node_infos', {'nodes': r}))['returnValue']
    keep = ('K2Node_FunctionEntry', 'K2Node_FunctionResult')
    n = 0
    for node in infos:
        ref = node['node']['refPath']
        tid = node.get('type_id', '')
        if any(k in ref or k in tid for k in keep):
            continue
        M.bp('delete_node', {'node': {'refPath': ref}})
        n += 1
    print('  cleared', n, 'of', len(infos), 'in', name)


def write(name, code, expect=None):
    r = M.bp('write_graph_dsl', {'graph': {'refPath': URT + ':' + name},
                                 'code': balance(code)})
    print('  write', name, '->', r[:240])
    if expect:
        tail = json.loads(M.bp('read_graph_dsl',
                               {'graph': {'refPath': URT + ':' + name}}))['returnValue']
        # read returns only if full; fallback: find_nodes titles
        ok = expect in json.dumps(tail)
        print('  contains %r: %s' % (expect, ok))


def graph_text(name):
    try:
        return json.loads(M.bp('read_graph_dsl',
                               {'graph': {'refPath': URT + ':' + name}}))['returnValue']
    except Exception:
        return ''


# ------------------------------------------------------------- 1. restore

def restore_refresh():
    txt = graph_text('RefreshTerminal')
    print('RefreshTerminal current length:', len(txt), 'has PushTerminal:',
          'PushTerminal' in txt)
    if 'PushTerminal' in txt and 'OpenWestGate' in txt:
        print('  already restored + hooked')
        return
    if 'PushTerminal' in txt:
        print('  already restored (hook check next)')
    clear('RefreshTerminal')
    code = TM.REFRESH
    # hook: insert the gate call as the last statement before the fn close
    assert code.rstrip().endswith(')'), 'REFRESH template shape changed'
    code = code.rstrip()[:-1] + '\n  (CallFunction|OpenWestGate))\n'
    r = M.bp('write_graph_dsl', {'graph': {'refPath': URT + ':RefreshTerminal'},
                                 'code': balance(code)})
    print('  restore write ->', r[:300])
    B.compile_bp(URT)
    nodes = json.loads(M.bp('find_nodes', {'graph': {'refPath': URT + ':RefreshTerminal'},
                                           'title': ''}))['returnValue']
    print('  RefreshTerminal nodes now:', len(nodes))
    if len(nodes) < 10:
        sys.exit('RefreshTerminal restore failed - stops here, nothing else touched')


# ------------------------------------------------------------- 2. gate fns

def gate_functions():
    # param for GateHideBlock
    try:
        r = M.bp('add_object_function_param',
                 {'graph': {'refPath': URT + ':GateHideBlock'},
                  'param_name': 'a', 'input_param': True,
                  'object_class': {'refPath': '/Script/Engine.Actor'}})
        print('  param GateHideBlock.a ->', r[:110])
    except Exception as e:
        print('  param a err (probably exists):', str(e)[:80])

    ensure_fn('GateHideBlock')
    clear('GateHideBlock')
    write('GateHideBlock', '''(fn GateHideBlock (a)
  (Rendering|SetActorHiddenInGame :self a :bNewHidden true)
  (Collision|SetActorEnableCollision :self a :bNewActorEnableCollision false)
)''')

    ensure_fn('OpenWestGate')
    clear('OpenWestGate')
    write('OpenWestGate', '''(fn OpenWestGate ()
  (if (Variables|Default|GetGateOpen)
    (return))
  (if (> (Variables|Default|GetTerminalRemaining) 0)
    (return))
  (Variables|Default|SetGateOpen true)
  (Development|PrintString "WEST GATE OPEN - all fixtures logged")
  (bind blocks (Actor|GetAllActorsWithTag "WestGateBlock"))
  (for b blocks
    (CallFunction|GateHideBlock :self self :a b))
  (bind redlights (Actor|GetAllActorsWithTag "WestGateLight"))
  (for lt redlights
    (Rendering|SetActorHiddenInGame :self lt :bNewHidden true))
  (bind greens (Actor|GetAllActorsWithTag "WestGateLightGreen"))
  (for g greens
    (Rendering|SetActorHiddenInGame :self g :bNewHidden false))
)''')
    B.compile_bp(URT)
    for fn in ('GateHideBlock', 'OpenWestGate'):
        nodes = M.bp('find_nodes', {'graph': {'refPath': URT + ':' + fn}, 'title': ''})
        cnt = len(json.loads(nodes)['returnValue'])
        print('  %s nodes: %d' % (fn, cnt))


def main():
    M.init()
    if 'true' in M.app('IsPIERunning', {}):
        sys.exit('PIE running - stop it first')
    print('== restore RefreshTerminal')
    restore_refresh()
    print('== gate functions')
    gate_functions()
    print('== compile')
    B.compile_bp(URT)
    print('var GateOpen present:',
          json.loads(M.bp('list_variables', {'blueprint': {'refPath': URT}}))['returnValue'])


if __name__ == '__main__':
    main()
