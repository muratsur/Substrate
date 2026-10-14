"""T1.4 terminal: temporary timer hook to exercise the log -> refresh path in PIE.

Run:  python _tools/terminal_livetest.py add
      python _tools/terminal_livetest.py remove
"""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
EG = RM + ':EventGraph'

TEMP = '''(fn TempLog ()
  (CallFunction|LogLookedAtFixture :self self :Result 1))
'''


def info(refs):
    return json.loads(M.bp('get_node_infos', {'nodes': refs}))['returnValue']


def find(title, graph=EG):
    for t in (title, title.replace(' ', ''), title.title()):
        r = json.loads(M.bp('find_nodes', {'graph': {'refPath': graph}, 'title': t}))['returnValue']
        if r:
            return r
    print('  NOT FOUND:', title)
    return []


def pins(node, direction, type_id=None, name=None):
    infos = info([{'refPath': node}])[0]
    key = 'input_pins' if direction == 'in' else 'output_pins'
    out = infos[key]
    if type_id:
        out = [p for p in out if p['type_id'] == type_id]
    if name:
        out = [p for p in out if p['name'] == name]
    return out


def add():
    print('add fn:', M.bp('add_function_graph', {'blueprint': {'refPath': RM},
                                                'graph_name': 'TempLog'})[:150])
    print('write:', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':TempLog'},
                                            'code': TEMP})[:200])
    begin = find('Event BeginPlay')[0]['refPath']
    start = find('StartShift')[0]['refPath']
    timer = json.loads(M.bp('create_node', {'graph': {'refPath': EG},
                                            'type_id': 'Utilities|Time|SetTimerbyFunctionName',
                                            'pos': {'x': 200, 'y': 900}}))['returnValue']['refPath']
    print('begin', begin.split('.')[-1], 'start', start.split('.')[-1], 'timer', timer.split('.')[-1])
    b_then = pins(begin, 'out', 'Exec')[0]
    s_exec = pins(start, 'in', 'Exec')[0]
    t_exec = pins(timer, 'in', 'Exec')[0]
    t_then = pins(timer, 'out', 'Exec')[0]
    # insert: BeginPlay -> timer -> StartShift
    print('break:', M.bp('break_pins', {'output_pin': b_then['pin_id'],
                                        'input_pin': s_exec['pin_id']})[:100])
    print('bp->timer:', M.bp('connect_pins', {'output_pin': b_then['pin_id'],
                                              'input_pin': t_exec['pin_id']})[:100])
    print('timer->start:', M.bp('connect_pins', {'output_pin': t_then['pin_id'],
                                                 'input_pin': s_exec['pin_id']})[:100])
    for pname, val in (('FunctionName', 'TempLog'), ('Time', '5.0'), ('bLooping', 'true')):
        p = [q for q in pins(timer, 'in', name=pname)]
        if p:
            print('  pin', pname, M.bp('set_pin_value', {'pin': p[0]['pin_id'], 'value': val})[:80])
    print('compile:', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:200])


def remove():
    for n in find('Set Timer by Function Name'):
        print('drop timer', M.bp('delete_node', {'node': {'refPath': n['refPath']}})[:80])
    begin = find('Event BeginPlay')[0]['refPath']
    start = find('StartShift')[0]['refPath']
    b_then = pins(begin, 'out', 'Exec')[0]
    s_exec = pins(start, 'in', 'Exec')[0]
    print('reconnect:', M.bp('connect_pins', {'output_pin': b_then['pin_id'],
                                              'input_pin': s_exec['pin_id']})[:100])
    print('rm fn:', M.bp('remove_function_graph', {'blueprint': {'refPath': RM},
                                                  'graph_name': 'TempLog'})[:120])
    print('compile:', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:200])


if __name__ == '__main__':
    M.init()
    {'add': add, 'remove': remove}[sys.argv[1] if len(sys.argv) > 1 else 'add']()
