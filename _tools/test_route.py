"""Probe the whole inspection route with the real pawn: every fixture stop plus the spawn.

Classifies each stop as
  STAYED   - solid floor, no teleport  (what every stop should be)
  RESCUED  - ended up back at the spawn, i.e. a rescue trigger fired (fell through a hole)
  NO FLOOR - still falling when read (z well below the expected deck)

Run:  python _tools/test_route.py
"""
import sys
import json
import time
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
SPAWN = (0, 1400)

STOPS = [
    ('spawn (PlayerStart)', -200, 1500, 500),
    ('terminal approach', -200, 1800, 500),
    ('C-01 (1469, 4342)', 1469, 4200, 600),
    ('C-02 (3060, 6170)', 3060, 6000, 600),
    ('C-03 (-2480, 7212)', -2480, 7100, 600),
    ('C-04 (-1516, 8349)', -1516, 8250, 600),
    ('C-05 (-2543, 10200)', -2543, 10100, 600),
    ('C-06 (8560, 3250)', 8560, 3150, 600),
    ('C-07 (8560, 4100)', 8560, 4000, 600),
    ('C-08 (-660, -6230)', -660, -6100, 600),
]


def find(cls):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                             'arguments': {'name': '', 'tag': '', 'collision_channels': [],
                                           'actor_type': {'refPath': cls}}})
    try:
        return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception:
        return []


def loc(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
                             'arguments': {'actor': {'refPath': ref}}})
    try:
        v = json.loads(r)['returnValue']['location']
        return (round(v['x']), round(v['y']), round(v['z']))
    except Exception:
        return None


def put(ref, x, y, z):
    M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
                         'arguments': {'actor': {'refPath': ref},
                                       'xform': {'location': {'x': x, 'y': y, 'z': z}}}})


M.init()
if 'true' not in M.app('IsPIERunning', {}):
    M.app('StartPIE', {'options': {'bSimulate': False}})
    time.sleep(12)
pawn = (find('/Script/Engine.Character') or [None])[0]
if not pawn:
    sys.exit('no pawn in PIE')

verdicts = {}
for label, x, y, z in STOPS:
    put(pawn, x, y, z)
    time.sleep(2.0)
    p = loc(pawn)
    if p is None:
        v, detail = 'NO PAWN', str(p)
    elif abs(p[0] - SPAWN[0]) < 150 and abs(p[1] - SPAWN[1]) < 150 and (x, y) != (-200, 1500):
        v, detail = 'RESCUED', 'teleported to spawn'
    elif p[2] < z - 400:
        v, detail = 'NO FLOOR', 'fell to z=%d' % p[2]
    else:
        v, detail = 'STAYED', 'rests at z=%d' % p[2]
    verdicts[label] = v
    print('%-24s -> %-24s %-9s %s' % (label, p, v, detail))

print()
bad = [k for k, v in verdicts.items() if v != 'STAYED']
print('route stops: %d/%d solid' % (len(verdicts) - len(bad), len(verdicts)))
print('problems  : %s' % (', '.join('%s (%s)' % (k, verdicts[k]) for k in bad) or 'none'))
