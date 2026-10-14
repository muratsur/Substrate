import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
BP=M.BP
def bp(n,a=None): return M.call('call_tool', {'toolset_name':BP,'tool_name':n,'arguments':a or {}})
BPC='/Game/Substrate/Core/BP_Airlock.BP_Airlock'
r = json.loads(bp('list_variables', {'blueprint': {'refPath': BPC}}))['returnValue']
if isinstance(r, str): r = json.loads(r)
print('VARIABLES:')
for v in r:
    print('  ', v if isinstance(v, str) else json.dumps(v))
