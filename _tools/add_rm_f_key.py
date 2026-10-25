"""Build 'F pressed -> Terminal.Toggle()' in BP_RoundManager's EventGraph with create_node/connect_pins (the graph DSL
cannot create key events). Idempotent: skips if an F InputKey node already exists there."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
G = {'refPath': '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager:EventGraph'}
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
call = lambda tool, args: json.loads(M.bp(tool, args))['returnValue']
for k in call('find_nodes', {'graph': G, 'title': '', 'node_class': {'refPath': '/Script/BlueprintGraph.K2Node_InputKey'}}):
    if call('get_node_infos', {'nodes': [k]})[0].get('type_id') == 'Input|KeyboardEvents|F':
        sys.exit('F key node already present: ' + k['refPath'])
def make(type_id, x, y):
    n = call('create_node', {'graph': G, 'type_id': type_id, 'pos': {'x': x, 'y': y}})
    return n if isinstance(n, dict) and 'refPath' in n else n['node']
key = make('Input|KeyboardEvents|F', 0, 2400)
get = make('Variables|Default|GetTerminal', 250, 2550)
tog = make('Class|BPTerminal|Toggle', 450, 2400)
def pins(node):
    i = call('get_node_infos', {'nodes': [node]})[0]
    return {(p['pin_id']['direction'], p['name']): p['pin_id'] for p in i.get('input_pins', []) + i.get('output_pins', [])}
pk, pg, pt = pins(key), pins(get), pins(tog)
print('key pins', [k[1] for k in pk], '| get pins', [k[1] for k in pg], '| toggle pins', [k[1] for k in pt])
out_term = next(v for (d, n), v in pg.items() if d == 'EGPD_Output')
print(M.bp('connect_pins', {'output_pin': pk[('EGPD_Output', 'Pressed')], 'input_pin': pt[('EGPD_Input', 'execute')]})[:200])
print(M.bp('connect_pins', {'output_pin': out_term, 'input_pin': pt[('EGPD_Input', 'self')]})[:200])
print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:200])
