"""Recreate the E (PASS) / Q (FLAG) key handlers on BP_RoundManager.

The graph prune deleted them (keyboard events are not reachable from an
AddEvent node, so they looked orphaned).  Also fixes prune.py's root rule.
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
EG = {'refPath': RM + ':EventGraph'}


def make_key(key, result, y):
    print('--', key, 'result', result)
    n_key = json.loads(M.bp('create_node', {
        'graph': EG, 'type_id': 'Input|KeyboardEvents|' + key, 'pos': {'x': 0, 'y': y}}))['returnValue']
    n_call = json.loads(M.bp('create_node', {
        'graph': EG, 'type_id': 'CallFunction|LogLookedAtFixture', 'pos': {'x': 420, 'y': y}}))['returnValue']
    info = json.loads(M.bp('get_node_infos', {'nodes': [n_key, n_call]}))['returnValue']
    kref = n_key['refPath'] if isinstance(n_key, dict) else n_key
    cref = n_call['refPath'] if isinstance(n_call, dict) else n_call
    ki = [i for i in info if i['node']['refPath'] == kref][0]
    ci = [i for i in info if i['node']['refPath'] == cref][0]
    print('   key out', [p['name'] for p in ki['output_pins']])
    print('   call in ', [p['name'] for p in ci['input_pins']])
    pressed = [p for p in ki['output_pins'] if p['name'] == 'Pressed'][0]
    ex = [p for p in ci['input_pins'] if p['type_id'] == 'Exec'][0]
    res = [p for p in ci['input_pins'] if p['name'] == 'Result'][0]
    print('   set Result', M.bp('set_pin_value', {'pin': res['pin_id'], 'value': str(result)})[:120])
    print('   connect', M.bp('connect_pins', {'output_pin': pressed['pin_id'],
                                             'input_pin': ex['pin_id']})[:120])
    return n_key, n_call


if __name__ == '__main__':
    M.init()
    make_key('E', 1, 700)
    make_key('Q', 2, 1000)
    print('compile', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:200])
