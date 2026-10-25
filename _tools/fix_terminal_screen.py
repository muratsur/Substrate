"""Terminal screen rendered as a checkerboard: an earlier fix set the WidgetComponent DrawSize to 30x22 to stop it being
oversized, but for a world-space widget DrawSize is also the render resolution (30x22 px). Keep the same 30x22-unit
footprint by rendering at 600x440 and scaling the component by 0.05. Applied to the blueprint template and the placed
instance (which carries its own copy)."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
REFS = ['/Game/Substrate/Core/BP_Terminal.BP_Terminal_C:Screen_GEN_VARIABLE',
        '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.BP_Terminal_C_0.Screen']
for r in REFS:
    # one axis per call: on the placed instance a multi-axis struct write only applied X
    for vals in ({'DrawSize': {'x': 600}}, {'DrawSize': {'y': 440}},
                 {'RelativeScale3D': {'x': 0.05}}, {'RelativeScale3D': {'y': 0.05}}, {'RelativeScale3D': {'z': 0.05}}):
        M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': r}, 'values': json.dumps(vals)}})
    print(r.split('/')[-1], M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': r}, 'properties': ['DrawSize', 'RelativeScale3D']}}))
print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': '/Game/Substrate/Core/BP_Terminal.BP_Terminal'}})[:200])
