import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
P='/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:PersistentLevel.BP_FirstPersonCharacter_C_0'

def act(name, args=None):
    return M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': name, 'arguments': args or {}})

def scn(name, args=None):
    return M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': name, 'arguments': args or {}})

def obj(name, args=None):
    return M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': name, 'arguments': args or {}})

r = act('get_actor_transform', {'actor': {'refPath': P}})
print('PAWN:', json.dumps(json.loads(r)['returnValue']))

# capsule size
r = act('get_components', {'actor': {'refPath': P}})
comps = json.loads(r)['returnValue']
print('COMPS:'); [print('  ', c) for c in comps[:10]]
