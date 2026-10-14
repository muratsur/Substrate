import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
BP=M.BP
def bp(n,a=None): return M.call('call_tool', {'toolset_name':BP,'tool_name':n,'arguments':a or {}})
BPC='/Game/Substrate/Core/BP_Airlock.BP_Airlock'
# list graphs of the asset
r = bp('graph_list', {'blueprint': {'refPath': BPC}}) if True else None
print('graph_list:', (r or '')[:400])
for g in ('EventGraph','GateOpen'):
    r = bp('read_graph_dsl', {'graph': {'refPath': BPC + ':' + g}})
    print('=== %s ===' % g)
    print(r[:3000])
