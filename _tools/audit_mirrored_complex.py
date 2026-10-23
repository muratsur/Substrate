"""List StaticMeshActors whose transform mirrors/flips their mesh (negative scale or upside-down rotation)."""
import sys, json, collections
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
r = json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': '', 'tag': '', 'collision_channels': []}}))['returnValue']
cnt = collections.Counter()
for a in r:
    ref = a['refPath']; n = ref.split('.')[-1]
    if not n.startswith('StaticMeshActor'): continue
    t = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']
    s, rot = t['scale'], t['rotation']
    neg = sum(v < 0 for v in s.values())
    flip = abs(abs(rot['roll']) - 180) < 30 or abs(abs(rot['pitch']) - 180) < 30
    if not (neg or flip): continue
    res = json.loads(M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': ref + '.StaticMeshComponent0'}, 'properties': ['StaticMesh']}}))['returnValue']
    d = json.loads(res) if isinstance(res, str) else res
    mesh = d.get('StaticMesh', {}).get('refPath', '').split('.')[-1]
    cnt[mesh] += 1
    L = t['location']
    print(f"{n:24s} {mesh:28s} loc=({L['x']:.0f},{L['y']:.0f},{L['z']:.0f}) scale=({s['x']:.2f},{s['y']:.2f},{s['z']:.2f}) rot=(p{rot['pitch']:.0f},y{rot['yaw']:.0f},r{rot['roll']:.0f})")
print(cnt)
