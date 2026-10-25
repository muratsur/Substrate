"""E away from any fixture printed LastLoggedAction (empty at shift start), so E looked dead. Rewrite LogLookedAtFixture
from its own read-back with only that print changed."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
G = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager:LogLookedAtFixture'
read = lambda: json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'read_graph_dsl', 'arguments': {'graph': {'refPath': G}}})).get('returnValue', '')
before = read()
OLD = '(Development|PrintString (Variables|Default|GetLastLoggedAction) true true'
NEW = '(Development|PrintString "Nothing in range - look at a fixture, get within 4 m" true true'
assert before.count(OLD) == 1, 'unexpected graph shape'
print(M.bp('write_graph_dsl', {'graph': {'refPath': G}, 'code': before.replace(OLD, NEW)})[:300])
print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': G.split(':')[0]}})[:200])
print(''.join(difflib.unified_diff(before.splitlines(True), read().splitlines(True), 'before', 'after')))
