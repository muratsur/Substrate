"""Player left tipped over (pawn pitch 90) and sliding through walls. The graph DSL's MakeRotator positional order is
(Roll, Pitch, Yaw); two-argument calls like (MakeRotator 0.0 90.0) meant 'yaw 90' but set PITCH 90 on the pawn, tipping
its capsule. Affected: EnterSectorD and StepSteamCapture. The K key ran the Steam screenshot tour (a dev tool) and is
removed like Backspace/Delete; RunSteamCapture/StepSteamCapture stay for dev use, with their rotators fixed too."""
import sys, json, re, difflib
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
call = lambda t, a: json.loads(M.bp(t, a))['returnValue']
read = lambda g: json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'read_graph_dsl', 'arguments': {'graph': {'refPath': RM + ':' + g}}})).get('returnValue', '')
TWO = re.compile(r'\(Math\|Rotator\|MakeRotator (-?[0-9.]+) (-?[0-9.]+)\)')   # (Roll=a Pitch=b) -> meant (Pitch=a Yaw=b)
for g in ('EnterSectorD', 'StepSteamCapture'):
    before = read(g)
    after = TWO.sub(r'(Math|Rotator|MakeRotator 0.0 \1 \2)', before)
    print(g, 'two-arg rotators:', len(TWO.findall(before)))
    if after == before: continue
    print(M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':' + g}, 'code': after})[:300])
    print(''.join(difflib.unified_diff(before.splitlines(True), read(g).splitlines(True), 'before', 'after'))[:2500])
G = {'refPath': RM + ':EventGraph'}
for k in call('find_nodes', {'graph': G, 'title': '', 'node_class': {'refPath': '/Script/BlueprintGraph.K2Node_InputKey'}}):
    if call('get_node_infos', {'nodes': [k]})[0].get('type_id') != 'Input|KeyboardEvents|K': continue
    sub = call('get_connected_subgraph', {'node': k})
    assert all(s.get('type_id') in ('Input|KeyboardEvents|K', '|RunSteamCapture') for s in sub), sub
    for s in sub: print('delete', s.get('type_id'), M.bp('delete_node', {'node': s['node']})[:60])
print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:200])
for k in call('find_nodes', {'graph': G, 'title': '', 'node_class': {'refPath': '/Script/BlueprintGraph.K2Node_InputKey'}}):
    print('remaining key:', [s.get('type_id') for s in call('get_connected_subgraph', {'node': k})])
