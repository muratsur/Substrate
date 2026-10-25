"""Fill holes in the corridor's south wall row (SM_module_high_wall_01, 730 x 260 x 2500, at Y -90, Z 240):
  - X -9870..-9140: the upper piece is missing between _16 and _14 (lower row intact); the player walked off the
    walkway into empty space at X~-9500, Y<0 and was teleported to spawn.
  - X 1080..2540: the row simply stops at X 1080; the floor strip beyond it (and the floor east of the X~1700 cross wall,
    which is open below Y 100) ends in empty space to the south and east.
Idempotent: skips pieces whose label already exists."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
MESH = '/Game/Modular_Sewer_Kit/Meshes/Modules/Walls/SM_module_high_wall_01.SM_module_high_wall_01'
PIECES = {'SM_module_high_wall_restored_west': -9870.0, 'SM_module_high_wall_south_ext_0': 1080.0, 'SM_module_high_wall_south_ext_1': 1810.0}
for label, x in PIECES.items():
    if json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': label, 'tag': '', 'collision_channels': []}})).get('returnValue'):
        print(label, 'already exists'); continue
    raw = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'add_to_scene_from_asset', 'arguments': {'asset_path': MESH, 'name': label,
        'xform': {'location': {'x': x, 'y': -90.0, 'z': 240.0}, 'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0}, 'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}}})
    if not raw.startswith('{'): sys.exit(raw)   # e.g. "Cannot create actors while PIE is active."
    ref = json.loads(raw)['returnValue']['refPath']
    M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': ref + '.StaticMeshComponent0'},
        'values': json.dumps({'BodyInstance': {'collisionEnabled': 'QueryAndPhysics', 'collisionProfileName': 'BlockAll'}})}})
    b = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']
    print(label, ref.split('.')[-1], f"X[{b['min']['x']:.0f}..{b['max']['x']:.0f}] Y[{b['min']['y']:.0f}..{b['max']['y']:.0f}] Z[{b['min']['z']:.0f}..{b['max']['z']:.0f}]")
