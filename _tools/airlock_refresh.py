import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
BP=M.BP
def bp(n,a=None): return M.call('call_tool', {'toolset_name':BP,'tool_name':n,'arguments':a or {}})

G = {'refPath': '/Game/Substrate/Core/BP_Airlock.BP_Airlock:GateOpen'}
dsl = json.loads(bp('read_graph_dsl', {'graph': G}))['returnValue']
print('--- GateOpen DSL ---')
print(dsl[:2000])
print('compile:', bp('compile_blueprint', {'blueprint': {'refPath': '/Game/Substrate/Core/BP_Airlock.BP_Airlock'}})[:150])
print('save:', M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
      'arguments': {'asset_paths': ['/Game/Substrate/Core/BP_Airlock.BP_Airlock']}})[:120])
