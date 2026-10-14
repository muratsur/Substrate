"""List lights near the PIE player with their current intensity.

Run:  python -u _tools/list_lights.py [radius]
"""
import sys
import json
import math
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
RADIUS = float(sys.argv[1]) if len(sys.argv) > 1 else 2500
LIGHT_CLASSES = ['/Script/Engine.PointLight', '/Script/Engine.SpotLight', '/Script/Engine.RectLight']


def find(cls):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                             'arguments': {'name': '', 'tag': '', 'collision_channels': [],
                                           'actor_type': {'refPath': cls}}})
    try:
        return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception:
        return []


def loc_of(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
                             'arguments': {'actor': {'refPath': ref}}})
    return json.loads(r)['returnValue']['location']


def light_component(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_components',
                             'arguments': {'actor': {'refPath': ref}}})
    for c in json.loads(r).get('returnValue', []):
        if 'LightComponent' in c['refPath']:
            return c['refPath']
    return None


def intensity(ref):
    comp = light_component(ref)
    if not comp:
        return None
    r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties',
                             'arguments': {'instance': {'refPath': comp},
                                           'properties': ['Intensity']}})
    try:
        v = json.loads(r)['returnValue']
        d = json.loads(v) if isinstance(v, str) else v
        return d.get('Intensity')
    except Exception:
        return None


M.init()
pawn = (find('/Script/Engine.Character') or [None])[0]
if not pawn:
    sys.exit('no pawn found - is PIE running?')
p = loc_of(pawn)
print('player at (%.0f, %.0f, %.0f)' % (p['x'], p['y'], p['z']))

hits = []
for cls in LIGHT_CLASSES:
    for ref in find(cls):
        l = loc_of(ref)
        d = math.dist((l['x'], l['y'], l['z']), (p['x'], p['y'], p['z']))
        if d <= RADIUS:
            hits.append((d, ref, l))
hits.sort()
print('lights within %d (%d):' % (RADIUS, len(hits)))
for d, ref, l in hits:
    print('  %-70s dist=%-6.0f at (%.0f, %.0f, %.0f) intensity=%s' %
          (ref.split(':')[-1], d, l['x'], l['y'], l['z'], intensity(ref)))
