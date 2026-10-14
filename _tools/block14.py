import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
ACT=M.ACT; OBJ=M.OBJ
def act(n,a=None): return M.call('call_tool', {'toolset_name':ACT,'tool_name':n,'arguments':a or {}})
def obj(n,a=None): return M.call('call_tool', {'toolset_name':OBJ,'tool_name':n,'arguments':a or {}})

L='/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:PersistentLevel.'
for i in (0,1):
    R=L+'BP_CanalRescue_C_%d'%i
    xf = json.loads(act('get_actor_transform', {'actor': {'refPath': R}}))['returnValue']
    l,s = xf['location'], xf['scale']
    ex,ey,ez = 40*s['x'], 40*s['y'], 40*s['z']
    print('BP_CanalRescue_C_%d center=(%.0f,%.0f,%.0f) half=(%.0f,%.0f,%.0f) box x[%.0f..%.0f] y[%.0f..%.0f] z[%.0f..%.0f]' % (
        i, l['x'],l['y'],l['z'], ex,ey,ez, l['x']-ex,l['x']+ex, l['y']-ey,l['y']+ey, l['z']-ez,l['z']+ez))
# capsule dims
P=L+'BP_FirstPersonCharacter_C_0'
r = obj('get_properties', {'instance': {'refPath': P+'.CollisionCylinder'}, 'properties': ['CapsuleHalfHeight','CapsuleRadius']})
print('CAPSULE:', r[:200])
