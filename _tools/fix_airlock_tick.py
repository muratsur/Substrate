import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
BP=M.BP
def bp(n,a=None): return M.call('call_tool', {'toolset_name':BP,'tool_name':n,'arguments':a or {}})
BPC='/Game/Substrate/Core/BP_Airlock.BP_Airlock:'

dsl = '''(event EventBeginPlay)

(event Collision|EventActorBeginOverlap (OtherActor)
  (bind _ascharacter (Utilities|Casting|CastToCharacter OtherActor))
  (Variables|Default|SetInsideChar _ascharacter)
  (Variables|Default|SetInsideOK true))

(event EventTick (DeltaSeconds)
  (CallFunction|TryTransit))

(event Collision|EventActorEndOverlap (OtherActor)
  (Variables|Default|SetDisarmed false)
  (Variables|Default|SetInsideOK false))
'''
r = bp('write_graph_dsl', {'graph': {'refPath': BPC + 'EventGraph'}, 'dsl': dsl})
print('write:', r[:200])
print('read-back:')
r = json.loads(bp('read_graph_dsl', {'graph': {'refPath': BPC + 'EventGraph'}}))['returnValue']
print(r)
