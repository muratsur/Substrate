"""Rewriting EnterSectorD from its read-back dropped PushTerminal's first argument (positional values go to the hidden self
pin first), losing the 'SECTOR D - ACCESS GRANTED' header. Restate that call with named pins."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
G = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager:EnterSectorD'
read = lambda: json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'read_graph_dsl', 'arguments': {'graph': {'refPath': G}}})).get('returnValue', '')
before = read()
OLD = '(CallFunction|PushTerminal "C-06 RELIEF VALVE" "[ ]" "PROCEED TO RELIEF VALVE")'
NEW = '(CallFunction|PushTerminal :Header "SECTOR D - ACCESS GRANTED" :Names "C-06 RELIEF VALVE" :States "[ ]" :Footer "PROCEED TO RELIEF VALVE")'
assert before.count(OLD) == 1, before
print(M.bp('write_graph_dsl', {'graph': {'refPath': G}, 'code': before.replace(OLD, NEW)})[:300])
print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': G.split(':')[0]}})[:200])
print(''.join(difflib.unified_diff(before.splitlines(True), read().splitlines(True), 'before', 'after')))
