import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
BP=M.BP
def bp(n,a=None): return M.call('call_tool', {'toolset_name':BP,'tool_name':n,'arguments':a or {}})

BPC='/Game/Substrate/Core/BP_CanalRescue.BP_CanalRescue'
# blueprint asset ref style used earlier: '/Game/Substrate/Core/BP_Airlock.BP_Airlock'
# try asset properties first via object tools
def obj(n,a=None): return M.call('call_tool', {'toolset_name':M.OBJ,'tool_name':n,'arguments':a or {}})
r = obj('get_properties', {'instance': {'refPath': BPC}, 'properties': ['graph', 'functions', 'variables']})
print('AV:', r[:400])
# graphs
r = bp('find_nodes', {'graph': {'refPath': BPC + ':EventGraph'}, 'title': ''})
try:
    refs = json.loads(r)['returnValue']
    print('EVENTGRAPH NODES:', len(refs))
    infos = []
    for i in range(0, len(refs), 40):
        infos += json.loads(bp('get_node_infos', {'nodes': refs[i:i+40]}))['returnValue']
    for n in infos:
        p = n.get('refPath') or n.get('node', {}).get('refPath')
        print('  ', (n.get('type_id') or '?')[:60], '->', (p or '?').split('.')[-1][:50])
except Exception as e:
    print('ERR', e, r[:300])
