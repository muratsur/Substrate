import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
ACT=M.ACT; SCN=M.SCN; OBJ=M.OBJ
def act(n,a=None): return M.call('call_tool', {'toolset_name':ACT,'tool_name':n,'arguments':a or {}})
def obj(n,a=None): return M.call('call_tool', {'toolset_name':OBJ,'tool_name':n,'arguments':a or {}})
def scn(n,a=None): return M.call('call_tool', {'toolset_name':SCN,'tool_name':n,'arguments':a or {}})

R='/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:PersistentLevel.BP_CanalRescue_C_1'
print('xf:', act('get_actor_transform', {'actor': {'refPath': R}})[:300])
r = act('get_components', {'actor': {'refPath': R}})
comps = json.loads(r)['returnValue']
print('comps:', comps)
for c in comps:
    if 'collision' in c['refPath'].lower() or 'shape' in c['refPath'].lower() or 'box' in c['refPath'].lower():
        r = obj('get_properties', {'instance': c, 'properties': ['BoxExtent','AreaClassX1','CollisionEnabled','CollisionProfileName','X,Y,Z']})
        print('SHAPE', c['refPath'].split('.')[-1], r[:500])
        r = obj('get_properties', {'instance': c, 'properties': ['BoxExtent']})
        print('BoxExtent:', r[:300])
# also check the other instance
r = scn('find_actors', {'name': 'CanalRescue', 'tag': '', 'collision_channels': []})
allresses = [h['refPath'] for h in json.loads(r)['returnValue']]
print('instances:', allresses)
