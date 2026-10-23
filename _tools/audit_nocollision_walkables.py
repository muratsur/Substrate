"""Whole-map audit: StaticMeshActors whose component collision is not QueryAndPhysics, grouped by mesh (sizes = actor bounds)."""
import sys, json, collections
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
r = json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': '', 'tag': '', 'collision_channels': []}}))['returnValue']
by_mesh = collections.defaultdict(list)
for a in r:
    ref = a['refPath']; n = ref.split('.')[-1]
    if not n.startswith('StaticMeshActor'): continue
    res = json.loads(M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': ref + '.StaticMeshComponent0'}, 'properties': ['BodyInstance', 'StaticMesh']}}))['returnValue']
    d = json.loads(res) if isinstance(res, str) else res
    bi = d.get('BodyInstance', {})
    if bi.get('collisionEnabled') == 'QueryAndPhysics' and bi.get('collisionProfileName') in ('BlockAll', 'BlockAllDynamic'): continue
    mesh = d.get('StaticMesh', {}).get('refPath', '').split('.')[-1]
    by_mesh[mesh].append((n, bi.get('collisionProfileName'), bi.get('collisionEnabled')))
for mesh, lst in sorted(by_mesh.items(), key=lambda kv: -len(kv[1])):
    print(f'{mesh:30s} {len(lst):4d}  e.g. {lst[0]}')
    if not mesh.startswith('SM_detail'):
        for x in lst: print('    ', *x)
