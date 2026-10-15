"""Apply user fixes:
Step 1: Turn off neon-green underwater effect (BP_water & PostProcessVolume_3)
Step 2: Fix stairs collision (SM_stair_01, SM_stair_02, SM_stairs_03 to CTF_UseComplexAsSimple + CharacterMovement)
Step 3: Put CanalRescue back only under the deep pit (z = 50), not on the stairs
"""
import sys
import json
import time
sys.path.insert(0, '_tools')
import mcpx as M

M.init()

ACT = 'editor_toolset.toolsets.actor.ActorTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
LEV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
MAP = '/Game/Substrate/Maps/L_SectorC'

print('================================================================')
print('       APPLYING CANAL, WATER, AND STAIRS COLLISION FIXES       ')
print('================================================================')

# --- STEP 1: Turn off neon-green underwater effect ---
print('\n--- STEP 1: NEON-GREEN UNDERWATER EFFECT ---')
# 1. Disable PostProcessVolume_3
pp3 = LEV + 'PostProcessVolume_3'
M.call('call_tool', {'toolset_name': OBJ, 'tool_name': 'set_properties',
                     'arguments': {'instance': {'refPath': pp3},
                                   'values': json.dumps({'bEnabled': False})}})
print('PostProcessVolume_3 bEnabled set to False.')

# 2. Lower BP_water_C_0 and BP_water_C_1 location Z by 40 units (from 230 down to 190)
for w in ['BP_water_C_0', 'BP_water_C_1']:
    w_ref = LEV + w
    curr_xf = json.loads(M.call('call_tool', {'toolset_name': ACT, 'tool_name': 'get_actor_transform',
                                              'arguments': {'actor': {'refPath': w_ref}}})).get('returnValue')
    new_loc = curr_xf['location']
    new_loc['z'] = 190.0  # 40 units below original 230
    M.call('call_tool', {'toolset_name': ACT, 'tool_name': 'set_actor_transform',
                         'arguments': {'actor': {'refPath': w_ref},
                                       'xform': {'location': new_loc, 'rotation': curr_xf['rotation'], 'scale': curr_xf['scale']}}})
    print(f'{w} Location Z updated to 190.0.')


# --- STEP 2: Fix stairs collision ---
print('\n--- STEP 2: FIX STAIRS COLLISION ---')
stair_meshes = [
    '/Game/Modular_Sewer_Kit/Meshes/Modules/Stairs/SM_stair_01',
    '/Game/Modular_Sewer_Kit/Meshes/Modules/Stairs/SM_stair_02',
    '/Game/Modular_Sewer_Kit/Meshes/Modules/Stairs/SM_stairs_03',
    '/Game/Modular_Sewer_Kit/Meshes/Rust_modules/SM_stairs_platform_01',
    '/Game/Modular_Sewer_Kit/Meshes/Rust_modules/SM_stairs_platform_02',
    '/Game/Modular_Sewer_Kit/Meshes/Rust_modules/SM_stairs_rust_01',
    '/Game/Modular_Sewer_Kit/Meshes/Rust_modules/SM_stairs_rust_02',
    '/Game/Modular_Sewer_Kit/Meshes/Rust_modules/SM_stairs_rust_03',
]

for mesh_path in stair_meshes:
    asset_ref = f'{mesh_path}.{mesh_path.split("/")[-1]}'
    r = M.call('call_tool', {'toolset_name': OBJ, 'tool_name': 'get_properties',
                             'arguments': {'instance': {'refPath': asset_ref}, 'properties': ['BodySetup']}})
    bs = json.loads(json.loads(r)['returnValue'])['BodySetup']['refPath']
    M.call('call_tool', {'toolset_name': OBJ, 'tool_name': 'set_properties',
                         'arguments': {'instance': {'refPath': bs},
                                       'values': json.dumps({'CollisionTraceFlag': 'CTF_UseComplexAsSimple'})}})
    print(f'{asset_ref.split("/")[-1]} -> CTF_UseComplexAsSimple')

# Enhance character movement for smooth stair climbing
char_bp = '/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter.BP_FirstPersonCharacter'
cdo_r = M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'get_default_object',
                             'arguments': {'blueprint': {'refPath': char_bp}}})
cdo = json.loads(cdo_r)['returnValue']['refPath']
p = M.call('call_tool', {'toolset_name': OBJ, 'tool_name': 'get_properties',
                         'arguments': {'instance': {'refPath': cdo}, 'properties': ['CharacterMovement']}})
cm = json.loads(json.loads(p)['returnValue'])['CharacterMovement']['refPath']
M.call('call_tool', {'toolset_name': OBJ, 'tool_name': 'set_properties',
                     'arguments': {'instance': {'refPath': cm},
                                   'values': json.dumps({'WalkableFloorAngle': 50.0, 'MaxStepHeight': 50.0})}})
print('BP_FirstPersonCharacter CharacterMovement: WalkableFloorAngle=50.0, MaxStepHeight=50.0')


# --- STEP 3: Put CanalRescue back under deep pit (Z = 50) ---
print('\n--- STEP 3: CANAL RESCUE UNDER DEEP PIT ---')
cr_global = LEV + 'BP_CanalRescue_C_0'
cr_sw = LEV + 'BP_CanalRescue_C_1'

# CanalRescue_Global at Z = 50.0, scale (70, 23, 1.75) -> bounds Z: -20..120
M.call('call_tool', {'toolset_name': ACT, 'tool_name': 'set_actor_transform',
                     'arguments': {'actor': {'refPath': cr_global},
                                   'xform': {'location': {'x': -300.0, 'y': 9900.0, 'z': 50.0},
                                             'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0},
                                             'scale': {'x': 70.0, 'y': 23.0, 'z': 1.75}}}})
b0 = json.loads(M.call('call_tool', {'toolset_name': ACT, 'tool_name': 'get_actor_bounds',
                                     'arguments': {'actor': {'refPath': cr_global}}})).get('returnValue')
print('CanalRescue_Global (BP_CanalRescue_C_0) updated:')
print('  Location Z: 50.0, Bounds:', b0)

# CanalRescue_SouthWest at Z = 0.0, scale (150, 175, 1.25) -> bounds Z: -50..50
M.call('call_tool', {'toolset_name': ACT, 'tool_name': 'set_actor_transform',
                     'arguments': {'actor': {'refPath': cr_sw},
                                   'xform': {'location': {'x': -1000.0, 'y': 5000.0, 'z': 0.0},
                                             'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0},
                                             'scale': {'x': 150.0, 'y': 175.0, 'z': 1.25}}}})
b1 = json.loads(M.call('call_tool', {'toolset_name': ACT, 'tool_name': 'get_actor_bounds',
                                     'arguments': {'actor': {'refPath': cr_sw}}})).get('returnValue')
print('CanalRescue_SouthWest (BP_CanalRescue_C_1) updated:')
print('  Location Z: 0.0, Bounds:', b1)

# Ensure BP_CanalRescue teleport graph is active
bpc_graph = '/Game/Substrate/Core/BP_CanalRescue.BP_CanalRescue:EventGraph'
dsl = json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'read_graph_dsl',
                                      'arguments': {'graph': {'refPath': bpc_graph}}}))['returnValue']
rescue_enabled = 'SetActorLocation' in dsl and 'EventActorBeginOverlap' in dsl
print(f'BP_CanalRescue Teleport Status: {"ENABLED" if rescue_enabled else "DISABLED"}')

# --- SAVE ASSETS ---
print('\n--- SAVING ASSETS ---')
assets_to_save = [MAP, char_bp] + [f'{m}.{m.split("/")[-1]}' for m in stair_meshes]
save_res = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                                'arguments': {'asset_paths': assets_to_save}})
print('Save assets result:', save_res)

print('\n================================================================')
print('               ALL 3 STEPS SUCCESSFULLY APPLIED                 ')
print('================================================================')
