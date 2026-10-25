"""Green tint at spawn: DockMarkerLight (PointLight_0, colour 0.2/1.0/0.35, intensity 800, radius 650) sits 141 units from
the spawn point and floods the dock wall green-white. Keep it as a faint marker: intensity 150, radius 450.
Previous values: Intensity 800, AttenuationRadius 650."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
C = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.PointLight_0.LightComponent0'
for v in ({'Intensity': 150.0}, {'AttenuationRadius': 450.0}):
    M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': C}, 'values': json.dumps(v)}})
print(M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': C}, 'properties': ['Intensity', 'AttenuationRadius', 'LightColor']}}))
