"""F (raise/stow the terminal) never fired: BP_Terminal's own F key event needs the actor to receive input, and enabling
it there (EnableInput at BeginPlay) still did not make F reach it in PIE. BP_RoundManager provably receives keyboard
input (E/Q logging), so F is handled there and calls Toggle on its Terminal reference; the terminal's own EnableInput is
removed again so the two can never both toggle. write_graph_dsl replaces an event's body, so bodies are restated in full."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
T = '/Game/Substrate/Core/BP_Terminal.BP_Terminal'
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
TERMINAL_BEGINPLAY = '''(event EventBeginPlay
  (CallFunction|AttachToPlayer)
  (Development|PrintString "TERMINAL: F raises / stows the checklist" true true "(R=0.000000,G=0.660000,B=1.000000,A=1.000000)" 5.0))
'''
RM_F = '''(event F (Key)
  (Class|BPTerminal|Toggle (Variables|Default|GetTerminal)))
'''
read = lambda B: json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'read_graph_dsl', 'arguments': {'graph': {'refPath': B + ':EventGraph'}}})).get('returnValue', '')
for B, code in ((T, TERMINAL_BEGINPLAY), (RM, RM_F)):
    before = read(B)
    print(B.split('.')[-1], M.bp('write_graph_dsl', {'graph': {'refPath': B + ':EventGraph'}, 'code': code})[:300])
    print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': B}})[:200])
    print(''.join(difflib.unified_diff(before.splitlines(True), read(B).splitlines(True), 'before', 'after')))
