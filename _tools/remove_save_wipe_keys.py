"""Backspace and Delete called ResetSaveData (a debug shortcut): with loading now working, one stray key press wiped the
player's progress. Delete those two key nodes and the ResetSaveData calls they drove. Pause > Restart remains the
deliberate way to start over. ResetSaveData itself is kept."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
G = {'refPath': '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager:EventGraph'}
call = lambda t, a: json.loads(M.bp(t, a))['returnValue']
for k in call('find_nodes', {'graph': G, 'title': '', 'node_class': {'refPath': '/Script/BlueprintGraph.K2Node_InputKey'}}):
    t = call('get_node_infos', {'nodes': [k]})[0].get('type_id')
    if t not in ('Input|KeyboardEvents|Backspace', 'Input|KeyboardEvents|Delete'): continue
    sub = call('get_connected_subgraph', {'node': k})
    for s in sub:
        assert s.get('type_id') in (t, '|ResetSaveData'), f'unexpected node attached to {t}: {s.get("type_id")}'
    for s in sub:
        print('delete', s.get('type_id'), M.bp('delete_node', {'node': s['node']})[:80])
print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': G['refPath'].split(':')[0]}})[:200])
for k in call('find_nodes', {'graph': G, 'title': '', 'node_class': {'refPath': '/Script/BlueprintGraph.K2Node_InputKey'}}):
    print('remaining key:', [s.get('type_id') for s in call('get_connected_subgraph', {'node': k})])
