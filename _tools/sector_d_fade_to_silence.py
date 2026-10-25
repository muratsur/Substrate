"""Sector D ambience: keep the existing deep rumble (Amb_SectorD_Rumble: sewer room tone at pitch 0.35, vol 0.45) but
centre it on the arrival point (-660, -8500) and shorten its falloff, so it is full where the player arrives, fades along
the walk and is fully silent for the last ~170 units before C-06 (Fix_D06 at Y -6230). DESIGN.md: 'the scariest
anomaly type is a room tone that stops.' Previous values printed first so they can be restored."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
A = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.AmbientSound_4'
C = A + '.AudioComponent0'
INNER, FALLOFF = 600.0, 1500.0   # silent beyond 2100 from (-660,-8500) -> Y > -6400
t = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': A}}}))['returnValue']
ao = json.loads(json.loads(M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': C}, 'properties': ['AttenuationOverrides']}}))['returnValue'])['AttenuationOverrides']
print('before: location', t['location'], 'extents', ao['attenuationShapeExtents'], 'falloff', ao['falloffDistance'])
t['location'] = {'x': -660.0, 'y': -8500.0, 'z': 500.0}
M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'set_actor_transform', 'arguments': {'actor': {'refPath': A}, 'xform': t}})
ao['attenuationShapeExtents'] = {'x': INNER, 'y': 0, 'z': 0}
ao['falloffDistance'] = FALLOFF
M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': C}, 'values': json.dumps({'AttenuationOverrides': ao})}})
t2 = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': A}}}))['returnValue']['location']
ao2 = json.loads(json.loads(M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': C}, 'properties': ['AttenuationOverrides', 'VolumeMultiplier', 'PitchMultiplier']}}))['returnValue'])
print('after:  location', t2, 'extents', ao2['AttenuationOverrides']['attenuationShapeExtents'], 'falloff', ao2['AttenuationOverrides']['falloffDistance'], 'vol', ao2['VolumeMultiplier'], 'pitch', ao2['PitchMultiplier'])
assert ao2['AttenuationOverrides']['falloffDistance'] == FALLOFF and round(t2['y']) == -8500
