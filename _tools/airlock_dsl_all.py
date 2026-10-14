import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
BP=M.BP
def bp(n,a=None): return M.call('call_tool', {'toolset_name':BP,'tool_name':n,'arguments':a or {}})
BPC='/Game/Substrate/Core/BP_Airlock.BP_Airlock'
for g in ('Transit','TryTransit','Disarm','FaceNearestFixture','UserConstructionScript'):
    r = bp('read_graph_dsl', {'graph': {'refPath': BPC + ':' + g}})
    print('=== %s ===' % g)
    v = ''
    try: v = json.loads(r)['returnValue']
    except Exception: v = r[:200]
    print(v[:2500])
    print()
