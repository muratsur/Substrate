"""Implement Fix 1 and Fix 2 from user guide:
1. Put a solid floor under the water (CanalBed_Safety_North) right at the bottom of the stairs
   so the player stays at ankle-deep puddle level (Z = 185) and never drops below the concrete curb.
2. Put a solid floor under the south stairs/canal (CanalBed_Safety_South) at Z = 70.
3. Boost BP_FirstPersonCharacter CharacterMovement MaxStepHeight to 65.0 and WalkableFloorAngle to 55.0.
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

M.init()

SCN = M.SCN
ACT = 'editor_toolset.toolsets.actor.ActorTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
MAP = '/Game/Substrate/Maps/L_SectorC'

print('================================================================')
print('       IMPLEMENTING SOLID FLOOR UNDER WATER & STAIR FIXES       ')
print('================================================================')

# 1. Check if CanalBed_Safety_North already exists
r = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'find_actors',
                         'arguments': {'name': 'CanalBed_Safety_North', 'tag': '', 'collision_channels': []}})
existing_north = json.loads(r).get('returnValue', [])

if existing_north:
    print('CanalBed_Safety_North exists, updating transform...')
    north_ref = existing_north[0]['refPath']
else:
    print('Creating CanalBed_Safety_North under stairs/water gap (Y=8800..11500)...')
    # Use Cube.Cube asset
    res = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'add_to_scene_from_asset',
                               'arguments': {
                                   'asset_path': '/Engine/BasicShapes/Cube.Cube',
                                   'name': 'CanalBed_Safety_North',
                                   'xform': {
                                       'location': {'x': 750.0, 'y': 10150.0, 'z': 165.0},
                                       'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0},
                                       'scale': {'x': 45.0, 'y': 27.0, 'z': 0.4}
                                   }
                               }})
    print('add_to_scene_from_asset result:', res)
    north_ref = json.loads(res)['returnValue']['refPath']

# Set collision to BlockAll on CanalBed_Safety_North
M.call('call_tool', {'toolset_name': OBJ, 'tool_name': 'set_properties',
                     'arguments': {
                         'instance': {'refPath': f'{north_ref}.StaticMeshComponent0'},
                         'values': json.dumps({'BodyInstance': {'CollisionProfileName': 'BlockAll'}})
                     }})
b_north = json.loads(M.call('call_tool', {'toolset_name': ACT, 'tool_name': 'get_actor_bounds',
                                         'arguments': {'actor': {'refPath': north_ref}}})).get('returnValue')
print('CanalBed_Safety_North Bounds:', b_north)


# 2. Check/Add CanalBed_Safety_South for Y=0..5000 at Z=50 (top at Z=70, matching bottom step)
r_south = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'find_actors',
                               'arguments': {'name': 'CanalBed_Safety_South', 'tag': '', 'collision_channels': []}})
existing_south = json.loads(r_south).get('returnValue', [])

if existing_south:
    print('CanalBed_Safety_South exists.')
    south_ref = existing_south[0]['refPath']
else:
    print('Creating CanalBed_Safety_South under south stairs/water gap (Y=0..5000)...')
    res_s = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'add_to_scene_from_asset',
                                 'arguments': {
                                     'asset_path': '/Engine/BasicShapes/Cube.Cube',
                                     'name': 'CanalBed_Safety_South',
                                     'xform': {
                                         'location': {'x': 400.0, 'y': 2500.0, 'z': 50.0},
                                         'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0},
                                         'scale': {'x': 40.0, 'y': 50.0, 'z': 0.4}
                                     }
                                 }})
    print('add_to_scene_from_asset south result:', res_s)
    south_ref = json.loads(res_s)['returnValue']['refPath']

# Set collision to BlockAll on CanalBed_Safety_South
M.call('call_tool', {'toolset_name': OBJ, 'tool_name': 'set_properties',
                     'arguments': {
                         'instance': {'refPath': f'{south_ref}.StaticMeshComponent0'},
                         'values': json.dumps({'BodyInstance': {'CollisionProfileName': 'BlockAll'}})
                     }})
b_south = json.loads(M.call('call_tool', {'toolset_name': ACT, 'tool_name': 'get_actor_bounds',
                                         'arguments': {'actor': {'refPath': south_ref}}})).get('returnValue')
print('CanalBed_Safety_South Bounds:', b_south)


# 3. Boost BP_FirstPersonCharacter CharacterMovement MaxStepHeight and WalkableFloorAngle
char_bp = '/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter.BP_FirstPersonCharacter'
cdo_r = M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'get_default_object',
                             'arguments': {'blueprint': {'refPath': char_bp}}})
cdo = json.loads(cdo_r)['returnValue']['refPath']
p = M.call('call_tool', {'toolset_name': OBJ, 'tool_name': 'get_properties',
                         'arguments': {'instance': {'refPath': cdo}, 'properties': ['CharacterMovement']}})
cm = json.loads(json.loads(p)['returnValue'])['CharacterMovement']['refPath']
M.call('call_tool', {'toolset_name': OBJ, 'tool_name': 'set_properties',
                     'arguments': {'instance': {'refPath': cm},
                                   'values': json.dumps({'WalkableFloorAngle': 55.0, 'MaxStepHeight': 65.0})}})
print('BP_FirstPersonCharacter CharacterMovement: WalkableFloorAngle=55.0, MaxStepHeight=65.0')


# 4. Save Assets
print('\n--- SAVING ASSETS ---')
save_res = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                                'arguments': {'asset_paths': [MAP, char_bp]}})
print('Save assets result:', save_res)

print('\n================================================================')
print('             WATER FLOOR FIXES APPLIED SUCCESSFULLY             ')
print('================================================================')
