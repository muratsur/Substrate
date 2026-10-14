"""Add a point light just above the PIE player (PIE world only, not saved).

Run:  python -u _tools/light_at_player.py [height_offset]
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
OFFSET = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0

M.init()
r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                         'arguments': {'name': '', 'tag': '', 'collision_channels': [],
                                       'actor_type': {'refPath': '/Script/Engine.Character'}}})
pawn = json.loads(r)['returnValue'][0]['refPath']
t = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
                                    'arguments': {'actor': {'refPath': pawn}}}))['returnValue']
loc = t['location']
x, y, z = loc['x'], loc['y'], loc['z'] + OFFSET
print('player at (%.0f, %.0f, %.0f); placing light at (%.0f, %.0f, %.0f)' % (loc['x'], loc['y'], loc['z'], x, y, z))
r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'add_to_scene_from_class',
                         'arguments': {'actor_type': {'refPath': '/Script/Engine.PointLight'},
                                       'name': 'PlayerFill_Light',
                                       'xform': {'location': {'x': x, 'y': y, 'z': z}}}})
print('add:', r[:200])
