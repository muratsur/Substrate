"""List static mesh actors whose location sits in the corridor lane ahead of the PIE player.

Run:  python _tools/scan_lane.py
Output is printed; candidates are sorted by distance from the player.
"""
import sys
import json
import math
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
SMA = '/Script/Engine.StaticMeshActor'


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
    t = json.loads(r)['returnValue']
    return t['location'], t.get('scale') or {}


M.init()
pawn = (find('/Script/Engine.Character') or [None])[0]
if not pawn:
    sys.exit('no pawn found - is PIE running?')
p, _ = loc_of(pawn)
px, py, pz = p['x'], p['y'], p['z']
print('player at (%.0f, %.0f, %.0f)' % (px, py, pz))

# Lane: forward along +X (yaw ~0), 1800 units ahead, +/-260 wide, floor to +400 high.
hits = []
for ref in find(SMA):
    loc, _ = loc_of(ref)
    dx, dy, dz = loc['x'] - px, loc['y'] - py, loc['z'] - pz
    if -150 <= dx <= 1800 and abs(dy) <= 260 and -200 <= dz <= 400:
        hits.append((math.hypot(dx, dy), ref.split(':')[-1], round(dx), round(dy), round(dz)))

hits.sort()
print('lane candidates (%d):' % len(hits))
for h in hits[:60]:
    print('  %-40s dist=%-6.0f dx=%-6d dy=%-6d dz=%d' % (h[1], h[0], h[2], h[3], h[4]))
