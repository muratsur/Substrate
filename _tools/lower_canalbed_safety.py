"""CanalBed_Safety (StaticMeshActor_3691) sat at Z 290..330: 140 above the water (Z 190), forming an invisible wall at the
canal edges and an invisible floor above the blocks. Lower it to match CanalBed_Safety_North (StaticMeshActor_3780, top Z 185)."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
XF = {'location': {'x': 1335.0, 'y': 6900.0, 'z': 165.0}, 'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0}, 'scale': {'x': 26.7, 'y': 38.0, 'z': 0.4}}
for w in ('L_SectorC', 'UEDPIE_0_L_SectorC'):
    ref = f'/Game/Substrate/Maps/{w}.L_SectorC:PersistentLevel.StaticMeshActor_3691'
    M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'set_actor_transform', 'arguments': {'actor': {'refPath': ref}, 'xform': XF}})
    b = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}})).get('returnValue')
    print(w, b and (round(b['min']['z']), round(b['max']['z'])))
print(M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}}))
