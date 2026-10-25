"""Close the dead-end stub south of the arch end (X -2560..-600, Y 5780..6450): two dry canal pits at Z 100 and a floor strip
that end in empty space at Y~5780, so walking past the arch dropped the player into BP_CanalRescue_C_1 and teleported them
to spawn. Places visible SM_module_wall_01 segments (540 x 100 x 500) along Y 6355..6455, plus a shortened one plugging the drain tunnel at X -2295..-1970 (its floor also ends in empty space near Y 4800)."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
MESH = '/Game/Modular_Sewer_Kit/Meshes/Modules/Walls/SM_module_wall_01.SM_module_wall_01'
Y, Z = 6355.0, 90.0
for i, (x, sx) in enumerate(((-2835.0, 1.0), (-1970.0, 1.0), (-1430.0, 1.0), (-890.0, 1.0), (-2295.0, 325.0 / 540.0))):
    label = f'SouthStub_Wall_{i}'
    if json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': label, 'tag': '', 'collision_channels': []}})).get('returnValue'):
        print(label, 'already exists'); continue
    res = json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'add_to_scene_from_asset', 'arguments': {
        'asset_path': MESH, 'name': label,
        'xform': {'location': {'x': x, 'y': Y, 'z': Z}, 'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0}, 'scale': {'x': sx, 'y': 1.0, 'z': 1.0}}}}))
    ref = res['returnValue']['refPath']
    M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': ref + '.StaticMeshComponent0'},
        'values': json.dumps({'BodyInstance': {'collisionEnabled': 'QueryAndPhysics', 'collisionProfileName': 'BlockAll'}})}})
    b = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']
    print(label, ref.split('.')[-1], f"X[{b['min']['x']:.0f}..{b['max']['x']:.0f}] Y[{b['min']['y']:.0f}..{b['max']['y']:.0f}] Z[{b['min']['z']:.0f}..{b['max']['z']:.0f}]")
