"""List every actor within RADIUS of the live PIE pawn, with class and scale.

Run:  python -u _tools/find_near.py [radius]
"""
import sys
import json
import math
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
RADIUS = float(sys.argv[1]) if len(sys.argv) > 1 else 600


def find(cls):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                             'arguments': {'name': '', 'tag': '', 'collision_channels': [],
                                           'actor_type': {'refPath': cls}}})
    try:
        return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception:
        return []


def xform(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
                             'arguments': {'actor': {'refPath': ref}}})
    return json.loads(r)['returnValue']


M.init()
pawn = find('/Script/Engine.Character')[0]
p = xform(pawn)['location']
print('player at (%.0f, %.0f, %.0f)' % (p['x'], p['y'], p['z']))
for cls in ['/Script/Engine.StaticMeshActor', '/Script/Engine.BlockingVolume', '/Script/Engine.Actor']:
    for ref in find(cls):
        t = xform(ref)
        l, s = t['location'], t['scale']
        d = math.dist((l['x'], l['y'], l['z']), (p['x'], p['y'], p['z']))
        if d <= RADIUS:
            print('%-40s dist=%-6.0f at (%.0f, %.0f, %.0f) scale=(%.1f, %.1f, %.1f)' %
                  (ref.split(':')[-1], d, l['x'], l['y'], l['z'], s['x'], s['y'], s['z']))
