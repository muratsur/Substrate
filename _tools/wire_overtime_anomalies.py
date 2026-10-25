"""Overtime anomalies 11 and 13 had no TargetActor, and BP_AnomalySocket.Apply refuses targetless sockets, so they never
fired. Hyper-Growth (11): target Growth_Late (BP_GrowthNode_C_1, unused by any other socket). Schizo Ledger (13): target
B-02 HEAT EXCHANGER and show 'F-01 CRYSTAL VEIN' in its row while applied (DESIGN.md round 15+: checklist items reference
sectors that don't exist); BP_RoundManager.AddRowIfMatch is extended to treat type 13 like type 8."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
L = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
def setp(n, vals):
    M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': L + n}, 'values': json.dumps(vals)}})
    print(n, M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': L + n}, 'properties': list(vals)}}))
setp('BP_AnomalySocket_C_12', {'TargetActor': {'refPath': L + 'BP_GrowthNode_C_1'}})
setp('BP_AnomalySocket_C_14', {'TargetActor': {'refPath': L + 'BP_Fixture_C_6'}})
setp('BP_AnomalySocket_C_14', {'Note': 'F-01 CRYSTAL VEIN'})
G = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager:AddRowIfMatch'
read = lambda: json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'read_graph_dsl', 'arguments': {'graph': {'refPath': G}}})).get('returnValue', '')
import build_checklist_corruption as B   # reuse its AddRowIfMatch source
OLD = '(== (Class|BPAnomalySocket|GetAnomalyType _socket) 8)'
NEW = '(or (== (Class|BPAnomalySocket|GetAnomalyType _socket) 8) (== (Class|BPAnomalySocket|GetAnomalyType _socket) 13))'
assert B.CODE.count(OLD) == 1
before = read()
if '13)' not in before:
    print(M.bp('write_graph_dsl', {'graph': {'refPath': G}, 'code': B.CODE.replace(OLD, NEW)})[:300])
    print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': G.split(':')[0]}})[:200])
    print(''.join(difflib.unified_diff(before.splitlines(True), read().splitlines(True), 'before', 'after')))
