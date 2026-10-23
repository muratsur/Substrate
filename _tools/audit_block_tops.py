"""For every walkable static mesh actor, trace down at its centre and compare the hit with its visual bounds top."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
WALK = ('SM_concrete', 'SM_stair', 'SM_double_bridge', 'SM_floor', 'SM_platform', 'SM_path')
r = json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': '', 'tag': '', 'collision_channels': []}}))['returnValue']
for a in r:
    ref = a['refPath']; n = ref.split('.')[-1]
    if not n.startswith('StaticMeshActor'): continue
    res = json.loads(M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': ref + '.StaticMeshComponent0'}, 'properties': ['StaticMesh']}}))['returnValue']
    d = json.loads(res) if isinstance(res, str) else res
    mesh = d.get('StaticMesh', {}).get('refPath', '').split('.')[-1]
    if not mesh.startswith(WALK): continue
    b = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']
    mn, mx = b['min'], b['max']
    x, y = (mn['x'] + mx['x']) / 2, (mn['y'] + mx['y']) / 2
    top = mx['z'] + 400
    h = json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'trace_world', 'arguments': {'start': {'x': x, 'y': y, 'z': top}, 'end': {'x': x, 'y': y, 'z': mn['z'] - 50}}})).get('returnValue')
    hit = None if h is None else top - h
    gap = None if hit is None else mx['z'] - hit
    flag = '  <-- NO HIT ON MESH' if hit is None or hit < mn['z'] - 1 else ''
    print(f"{n:24s} {mesh:24s} c=({x:.0f},{y:.0f}) Z[{mn['z']:.0f}..{mx['z']:.0f}] hit={'-' if hit is None else f'{hit:.0f}'}{flag}")
