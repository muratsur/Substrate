"""The placed terminal's Body (BlockAllDynamic) rides on the player camera when raised and blocks the player's own capsule.
Keep it blocking everything else, ignore Pawn."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
rp = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.BP_Terminal_C_0.Body'
M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': rp}, 'values': json.dumps({'BodyInstance': {
    'collisionProfileName': 'Custom', 'collisionEnabled': 'QueryAndPhysics', 'objectType': 'ECC_WorldDynamic'}})}})
# responses must be set in a separate call: switching the profile resets them
M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': rp}, 'values': json.dumps({'BodyInstance': {
    'collisionResponses': {'responseArray': [{'channel': 'Pawn', 'response': 'ECR_Ignore'}]}}})}})
bi = json.loads(json.loads(M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': rp}, 'properties': ['BodyInstance']}}))['returnValue'])['BodyInstance']
print(bi['collisionProfileName'], bi['collisionEnabled'], bi['objectType'], bi['collisionResponses'])
assert bi['collisionProfileName'] == 'Custom' and {'channel': 'Pawn', 'response': 'ECR_Ignore'} in bi['collisionResponses']['responseArray']
print(M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}}))
