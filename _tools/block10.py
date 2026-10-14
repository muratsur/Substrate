import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
SCN=M.SCN; ACT=M.ACT; OBJ=M.OBJ; BP=M.BP

def scn(n,a=None): return M.call('call_tool', {'toolset_name':SCN,'tool_name':n,'arguments':a or {}})
def obj(n,a=None): return M.call('call_tool', {'toolset_name':OBJ,'tool_name':n,'arguments':a or {}})
def act(n,a=None): return M.call('call_tool', {'toolset_name':ACT,'tool_name':n,'arguments':a or {}})

R='/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:PersistentLevel.BP_CanalRescue_C_1'
r = obj('get_properties', {'instance': {'refPath': R}, 'properties': ['TriggerCondition','TriggerActor','RespawnLocation','CheckInterval','FallingThreshold','bEnabled','TriggerState','bAutoEnable'] })
print('PROPS:', r[:800])
r = obj('list_properties', {'instance': {'refPath': R}})
print('ALL KEYS:', r[:1500])
