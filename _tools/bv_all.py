"""Read-only: transform of every BlockingVolume in the live PIE world.

Run:  python -u _tools/bv_all.py
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
for a in json.loads(r).get('returnValue', []):
    ref = a['refPath']
    t = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
                                        'arguments': {'actor': {'refPath': ref}}}))['returnValue']
    print(ref.split(':')[-1], t['location'], 'scale', t['scale'])
