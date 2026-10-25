"""The terminal Body is /Engine/BasicShapes/Cube with no material override, so it rendered WorldGridMaterial (the engine's
checkerboard placeholder) right behind the transparent screen. Give it the Sewer kit's dark pipe metal (MI_pipes, as used
by the wall lamps). Template + placed instance."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
MAT = '/Game/Modular_Sewer_Kit/Materials/MI_pipes.MI_pipes'
for r in ('/Game/Substrate/Core/BP_Terminal.BP_Terminal_C:Body_GEN_VARIABLE',
          '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.BP_Terminal_C_0.Body'):
    M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': r}, 'values': json.dumps({'OverrideMaterials': [{'refPath': MAT}]})}})
    print(r.split(':')[-1], M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': r}, 'properties': ['OverrideMaterials']}}))
print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': '/Game/Substrate/Core/BP_Terminal.BP_Terminal'}})[:200])
