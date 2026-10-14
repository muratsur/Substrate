import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
OBJ=M.OBJ; ACT=M.ACT
def obj(n,a=None): return M.call('call_tool', {'toolset_name':OBJ,'tool_name':n,'arguments':a or {}})
def act(n,a=None): return M.call('call_tool', {'toolset_name':ACT,'tool_name':n,'arguments':a or {}})

L='/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:PersistentLevel.'
for i in (0,1):
    A = L+'BP_Airlock_C_%d'%i
    r = obj('get_properties', {'instance': {'refPath': A}, 'properties': ['GateOK','TransitTarget','RowsLow','RowsHigh','IsTransiting','LockReason']})
    print('BP_Airlock_C_%d:' % i, r[:500])
    xf = json.loads(act('get_actor_transform', {'actor': {'refPath': A}}))['returnValue']
    print('  xf:', xf['location'])
    comps = json.loads(act('get_components', {'actor': {'refPath': A}}))['returnValue']
    print('  comps:', [c['refPath'].split('.')[-1] for c in comps])
