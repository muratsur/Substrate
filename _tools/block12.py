import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
BP=M.BP
def bp(n,a=None): return M.call('call_tool', {'toolset_name':BP,'tool_name':n,'arguments':a or {}})
BPC='/Game/Substrate/Core/BP_CanalRescue.BP_CanalRescue'
r = bp('read_graph_dsl', {'graph': {'refPath': BPC + ':EventGraph'}})
print(r[:4000])
