import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
SCN = 'editor_toolset.toolsets.scene.SceneTools'
AT  = 'editor_toolset.toolsets.actor.ActorTools'
r = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'find_actors',
    'arguments': {'name': '', 'tag': '', 'collision_channels': []}})
d = json.loads(r)['returnValue']
far = []
for a in d:
    ref = a['refPath']
    n = ref.split('.')[-1]
    if not n.startswith('StaticMeshActor'):
        continue
    t = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': a}}))['returnValue']
    x = t['location']['x']
    if x < -24000:
        far.append((round(x), round(t['location']['y']), round(t['location']['z']), n))
far.sort()
print('far-west static meshes:', len(far))
for row in far[:16]:
    print(row)
