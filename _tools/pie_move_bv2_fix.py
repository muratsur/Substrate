"""PIE-only: set BlockingVolume_2's root component to Movable, move it away, read back. Not saved.

Run:  python -u _tools/pie_move_bv2_fix.py
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
OBJ = M.OBJ
M.init()
r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                         'arguments': {'name': '', 'tag': '', 'collision_channels': [],
                                       'actor_type': {'refPath': '/Script/Engine.BlockingVolume'}}})
ref = [a['refPath'] for a in json.loads(r).get('returnValue', []) if a['refPath'].endswith('BlockingVolume_2')][0]
print('ref:', ref)
comps = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_components',
                             'arguments': {'actor': {'refPath': ref}}})
print('components:', comps[:300])
root = None
for c in json.loads(comps).get('returnValue', []):
    if 'BrushComponent' in c['refPath'] or 'RootComponent' in c['refPath']:
        root = c['refPath']
        break
print('root component:', root)
print('set mobility:', M.call('call_tool', {'toolset_name': OBJ, 'tool_name': 'set_properties',
      'arguments': {'instance': {'refPath': root}, 'values': json.dumps({'Mobility': 'Movable'})}})[:200])
print('move:', M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
      'arguments': {'actor': {'refPath': ref}, 'xform': {'location': {'x': -1272.0, 'y': 30000.0, 'z': 0.0}}}})[:120])
print('after:', M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
      'arguments': {'actor': {'refPath': ref}}})[:200])
