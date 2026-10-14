"""Build the west-end gate.

Gate design:
  - The four concrete blockade blocks (tagged WestGateBlock) hide + lose
    collision when every fixture the terminal requires is logged.
  - The red end light (tagged WestGateLight) turns green at the same moment.
  - Trigger: at the end of RefreshTerminal (runs after every E/Q log and on
    StartShift/BeginPlay), so the check is simply TerminalRemaining == 0.
  - One-way per session: GateOpen latches; StartShift never closes the gate
    again once the player has earned it.

Usage:
  python _tools/build_west_gate.py tag     # tag level actors (needs editor, no PIE)
  python _tools/build_west_gate.py bp      # vars + graphs + compile
  python _tools/build_west_gate.py save    # save level + BP
"""
import sys
import json
import os
import time
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B

URT = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
LEV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'

GREEN = '(R=0.100000,G=1.000000,B=0.250000,A=1.000000)'


def app_pie():
    r = M.app('IsPIERunning', {})
    return 'true' in r


# ---------------------------------------------------------------- tag step

ACT = 'editor_toolset.toolsets.actor.ActorTools'


def find_tag_tool():
    d = json.loads(M.call('describe_toolset', {'toolset_name': ACT}))
    names = [t['name'].split('.')[-1].lower() for t in d.get('tools', [])]
    for cand in ('add_tag', 'set_actor_tags', 'set_actor_tag'):
        if cand in names:
            return cand
    print('tag-bearing tools:', [n for n in names if 'tag' in n])
    return None


def transform(name):
    r = json.loads(M.call('call_tool', {
        'toolset_name': ACT, 'tool_name': 'get_actor_transform',
        'arguments': {'actor': {'refPath': LEV + name}}}))
    loc = r['returnValue'].get('location', {})
    return round(loc.get('x', 0)), round(loc.get('y', 0))


def tag_actors():
    candidates = ['StaticMeshActor_3692', 'StaticMeshActor_3693',
                  'StaticMeshActor_3694', 'StaticMeshActor_3695',
                  'PointLight_22']
    tag_tool = find_tag_tool()
    if not tag_tool:
        sys.exit(1)

    found = []
    for name in candidates:
        try:
            x, y = transform(name)
            found.append((name, x, y))
        except Exception as e:
            print('MISSING:', name, str(e)[:80])
    for name, x, y in found:
        print('found: %-22s (%d, %d)' % (name, x, y))
    if not found:
        sys.exit('no gate actors found by name - enumerate blocks near x=-25060 instead')

    for i, (name, x, y) in enumerate(found):
        role = 'WestGateLight' if name.startswith('PointLight') else 'WestGateBlock'
        ref = {'refPath': LEV + name}
        try:
            r = M.call('call_tool', {'toolset_name': ACT, 'tool_name': tag_tool,
                                     'arguments': {'actor': ref, 'tag': role}})
            chk = M.call('call_tool', {'toolset_name': ACT, 'tool_name': 'has_tag',
                                       'arguments': {'actor': ref, 'tag': role}})
            print('tag %-22s %-14s %s | has: %s' % (name, role, r[:80], chk[:40]))
        except Exception as e:
            print('  FAILED', name, '|', str(e)[:120])
    print('done')


# ------------------------------------------------------------ bp step

def clear_graph(graph, keep=('K2Node_FunctionEntry', 'K2Node_FunctionResult')):
    if isinstance(graph, dict):
        graph = graph['refPath']
    try:
        r = json.loads(M.bp('find_nodes', {'graph': {'refPath': graph}, 'title': ''}))['returnValue']
    except Exception:
        print('  clear: graph missing/unreadable', graph.split(':')[-1])
        return
    if not r:
        print('  clear: empty', graph.split(':')[-1])
        return
    infos = json.loads(M.bp('get_node_infos', {'nodes': r}))['returnValue']
    n = 0
    for node in infos:
        ref = node['node']['refPath']
        tid = node.get('type_id', '')
        if any(k in ref or k in tid for k in keep):
            continue
        M.bp('delete_node', {'node': {'refPath': ref}})
        n += 1
    print('  cleared', n, 'of', len(infos), 'in', graph.split(':')[-1])


def balanced(code):
    d = code.count('(') - code.count(')')
    return code.rstrip('\n') + ')' * d + '\n' if d > 0 else code


def write(graph, code):
    if isinstance(graph, dict):
        graph = graph['refPath']
    r = M.bp('write_graph_dsl', {'graph': {'refPath': graph}, 'code': balanced(code)})
    print('  write', graph.split(':')[-1], '->', r[:260])
    return r


def ensure_fn(bp, name, params=''):
    """Create the function graph if needed (DSL fn header declares the params)."""
    try:
        r = M.bp('add_function_graph', {'blueprint': {'refPath': bp}, 'graph_name': name})
        print('  fn', name, '->', r[:120])
    except Exception as e:
        print('  fn', name, 'exists or err:', str(e)[:80])
    params_old = ''
    if params:
        try:
            r = M.bp('add_function_param', {'graph': {'refPath': bp + ':' + name},
                                            'param_name': params, 'param_type': 'object',
                                            'input_param': True})
            params_old = True
            print('  param', params, '->', r[:100])
        except Exception as e:
            print('  param err', str(e)[:80])


def bp_step():
    if app_pie():
        sys.exit('PIE is running - stop it before BP edits')

    # 1. GateOpen bool (idempotent)
    have = json.loads(M.bp('list_variables', {'blueprint': {'refPath': URT}}))['returnValue']
    names = [v['name'] if isinstance(v, dict) else str(v) for v in have]
    if 'GateOpen' not in names:
        B.add_var(URT, 'GateOpen', 'bool')
    B.compile_bp(URT)

    # 2. helpers
    ensure_fn(URT, 'GateHideBlock')
    clear_graph({'refPath': URT + ':GateHideBlock'})
    write({'refPath': URT + ':GateHideBlock'}, '''(fn GateHideBlock (a)
  (Rendering|SetActorHiddenInGame :self a :bNewHidden true)
  (Collision|SetActorEnableCollision :self a :bNewActorEnableCollision false)
)''')
    ensure_fn(URT, 'SetGateLightGreen')
    clear_graph({'refPath': URT + ':SetGateLightGreen'})
    write({'refPath': URT + ':SetGateLightGreen'}, '''(fn SetGateLightGreen ()
  (bind lights (Actor|GetAllActorsWithTag "WestGateLight"))
  (for lt lights
    (bind comps (Actor|GetComponentsByClass lt "/Script/Engine.PointLightComponent"))
    (for c comps
      (Component|Light|SetLightColor :Component c :NewColor %s)))
)''' % GREEN)

    # 3. main gate function
    ensure_fn(URT, 'OpenWestGate')
    clear_graph({'refPath': URT + ':OpenWestGate'})
    write({'refPath': URT + ':OpenWestGate'}, '''(fn OpenWestGate ()
  (if (Variables|Default|GetGateOpen)
    (else
      (bind rem (Variables|Default|GetTerminalRemaining))
      (if (<= rem 0)
        (Variables|Default|SetGateOpen true)
        (Development|PrintString " WEST GATE OPEN - all fixtures logged")
        (bind blocks (Actor|GetAllActorsWithTag "WestGateBlock"))
        (for b blocks
          (CallFunction|GateHideBlock :self self :a b))
        (CallFunction|SetGateLightGreen))))
)''')
    B.compile_bp(URT)

    # 4. hook into RefreshTerminal: clear + rewrite with the gate call appended
    cur = json.loads(M.bp('read_graph_dsl',
                          {'graph': {'refPath': URT + ':RefreshTerminal'}}))['returnValue']
    if 'OpenWestGate' in cur:
        print('  RefreshTerminal already hooked')
        return
    clear_graph({'refPath': URT + ':RefreshTerminal'})
    body = cur.rstrip('\n')
    assert body.endswith(')'), 'unexpected dsl shape: %r...' % body[-40:]
    body = body[:-1] + '\n  (CallFunction|OpenWestGate))\n'
    write({'refPath': URT + ':RefreshTerminal'}, body)
    B.compile_bp(URT)
    tail = json.loads(M.bp('read_graph_dsl',
                           {'graph': {'refPath': URT + ':RefreshTerminal'}}))['returnValue'][-200:]
    print('  RefreshTerminal tail:', tail)
    print('  tail ok:', 'OpenWestGate' in tail)


# ------------------------------------------------------------- save step

UMAP = os.path.join('Content', 'Substrate', 'Maps', 'L_SectorC.umap')


def save_step():
    r = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                             'arguments': {'asset_paths': [
                                 '/Game/Substrate/Maps/L_SectorC',
                                 '/Game/Substrate/Core/BP_RoundManager']}})[:160]
    print('save:', r)
    time.sleep(2)
    st = os.stat(UMAP)
    print('umap: %d bytes  %s' % (st.st_size, time.strftime('%m-%d %H:%M:%S',
                                                            time.localtime(st.st_mtime))))


if __name__ == '__main__':
    M.init()
    step = sys.argv[1] if len(sys.argv) > 1 else 'tag'
    if step == 'tag':
        tag_actors()
    elif step == 'bp':
        bp_step()
    elif step == 'save':
        save_step()
    else:
        sys.exit('usage: tag|bp|save')
