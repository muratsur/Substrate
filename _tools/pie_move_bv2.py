"""PIE-only test: move BlockingVolume_2 far away so the player can walk past it. Not saved.

Run:  python -u _tools/pie_move_bv2.py
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
M.init()
r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                         'arguments': {'name': '', 'tag': '', 'collision_channels': [],
                                       'actor_type': {'refPath': '/Script/Engine.BlockingVolume'}}})
refs = [a['refPath'] for a in json.loads(r).get('returnValue', []) if a['refPath'].endswith('BlockingVolume_2')]
print('found:', refs)
ref = refs[0]
print('before:', M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
                                       'arguments': {'actor': {'refPath': ref}}})[:200])
print('move:', M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
                                    'arguments': {'actor': {'refPath': ref},
                                                  'xform': {'location': {'x': -1272.0, 'y': 30000.0, 'z': 0.0}}}})[:120])
