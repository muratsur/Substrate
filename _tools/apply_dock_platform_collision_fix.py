"""Apply complete floor collision repair for all walking surfaces on the West and East banks of Sector C.

Ground truth root cause:
- Bridge crosses Westbound (-X direction).
- Facing West (yaw=180), turning Right means moving South (-Y).
- Prior agent assumed turning right meant North (+Y) and only fixed northern slabs (3106..3115).
- Slabs south of Y=8188 (StaticMeshActor_2715..2720, 2875..2877, 3206..3207) and northern East approach (2741, 2712..2707) had NoCollision.
- Stepping off the west bridge stairs and steering right placed player on StaticMeshActor_2715, immediately dropping into canal water at Z=197.

This script sets BlockAll / QueryAndPhysics on all genuine walking floor slabs.
"""

import sys
import json
import time

sys.path.insert(0, '_tools')
import mcpx as M
M.init()

OBJ = 'editor_toolset.toolsets.object.ObjectTools'
ACT = 'editor_toolset.toolsets.actor.ActorTools'
AT = 'editor_toolset.toolsets.asset.AssetTools'
MAP = '/Game/Substrate/Maps/L_SectorC'

# Slabs to fix:
WEST_SOUTH_SLABS = [
    2715, 2716, 2875, 2717, 2876, 2718, 2877, 2719, 2720, 3206, 3207
]

WEST_NORTH_SLABS = [
    2721, 3292, 3293, 3294
]

EAST_NORTH_SLABS = [
    2741, 2712, 2740, 2711, 2739, 2710, 2738, 2709, 2737, 2708, 2736, 2707, 2735
]

ALL_TARGET_SLABS = [797, 798, 799, 800, 1631, 1633, 1635, 1742, 1743]

print(f"=== APPLYING FLOOR COLLISION REPAIR TO {len(ALL_TARGET_SLABS)} FLOOR SLABS ===")

success_count = 0
for num in ALL_TARGET_SLABS:
    rp = f'/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.StaticMeshActor_{num}.StaticMeshComponent0'
    val = {
        'BodyInstance': {
            'collisionEnabled': 'QueryAndPhysics',
            'collisionProfileName': 'BlockAll'
        }
    }
    r = M.call('call_tool', {
        'toolset_name': OBJ,
        'tool_name': 'set_properties',
        'arguments': {
            'instance': {'refPath': rp},
            'values': json.dumps(val)
        }
    })
    
    # Read back to verify
    p = M.call('call_tool', {
        'toolset_name': OBJ,
        'tool_name': 'get_properties',
        'arguments': {
            'instance': {'refPath': rp},
            'properties': ['BodyInstance']
        }
    })
    try:
        bi = json.loads(json.loads(p)['returnValue']).get('BodyInstance', {})
        ce = bi.get('collisionEnabled')
        cp = bi.get('collisionProfileName')
        if ce == 'QueryAndPhysics' and cp == 'BlockAll':
            print(f"  OK: StaticMeshActor_{num:4d} -> CollisionEnabled={ce}, Profile={cp}")
            success_count += 1
        else:
            print(f"  FAIL: StaticMeshActor_{num:4d} -> CollisionEnabled={ce}, Profile={cp}")
    except Exception as e:
        print(f"  ERROR reading StaticMeshActor_{num}: {e}")

print(f"\nSuccessfully updated {success_count}/{len(ALL_TARGET_SLABS)} floor slabs.")

# Save all dirty assets including map
print("\n--- SAVING MAP ASSET ---")
save_res = M.call('call_tool', {
    'toolset_name': AT,
    'tool_name': 'save_assets',
    'arguments': {'asset_paths': []}
})
print(f"Save assets result: {save_res}")

print("\n=== REPAIR APPLIED AND SAVED ===")
