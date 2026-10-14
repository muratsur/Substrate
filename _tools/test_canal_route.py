"""Walk-test the canal route without input: teleport the pawn, let it settle, read where it ends up.

BP_CanalRescue teleports the player to (0, 1400, 400) - the spawn - so "was I rescued?"
is simply "did I end up back at spawn?".

Run:  python _tools/test_canal_route.py
"""
import sys
import json
import time
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
SPAWN = (0, 1400)


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
        return r[:110]


def put(ref, x, y, z):
    M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
                         'arguments': {'actor': {'refPath': ref},
                                       'xform': {'location': {'x': x, 'y': y, 'z': z}}}})


M.init()
print('PIE:', M.app('IsPIERunning', {})[:40])
if 'true' not in M.app('IsPIERunning', {}):
    print('start:', M.app('StartPIE', {'options': {'bSimulate': False}})[:80])
    time.sleep(12)

chars = find('/Script/Engine.Character')
print('pawn refs:', chars[:2])
if not chars:
    sys.exit('no pawn found')
pawn = chars[0]

CASES = [
    ('catwalk start   (-2500, 8500)', -2500, 8500, 450),
    ('catwalk end     (-2500, 10100)', -2500, 10100, 450),
    ('catwalk past C05(-2500, 10600)', -2500, 10600, 450),
    ('channel north   (-2100, 8000)', -2100, 8000, 250),
    ('channel in box  (-2100, 9500)', -2100, 9500, 250),
    ('channel near end(-2100, 10300)', -2100, 10300, 250),
    ('east ledge      (-1800, 9500)', -1800, 9500, 450),
    ('below the floor (-2100, 9500, -100)', -2100, 9500, -100),
    ('deep canal trench x=-1300', -1300, 10000, 500),
]
for y in range(8500, 11500, 550):
    CASES.append(('route: catwalk  y=%d' % y, -2500, y, 450))
for y in range(8500, 11500, 550):
    CASES.append(('route: channel  y=%d' % y, -2100, y, 250))
for y in range(8500, 11500, 550):
    CASES.append(('route: east walk y=%d' % y, -1000, y, 650))

results = {}
for label, x, y, z in CASES:
    put(pawn, x, y, z)
    time.sleep(2.2)
    p = loc(pawn)
    rescued = isinstance(p, tuple) and abs(p[0] - SPAWN[0]) < 150 and abs(p[1] - SPAWN[1]) < 150
    results[label] = rescued
    print('%-32s -> %-24s %s' % (label, p, 'RESCUED (teleported to spawn)' if rescued else 'stayed'))
print()
for line in ('catwalk', 'channel', 'east walk'):
    bad = [k for k, r in results.items() if k.startswith('route: ' + line) and r]
    print('%-10s %s' % (line, 'CLEAR end to end' if not bad else 'blocked at ' + ', '.join(bad)))

print('PIE still:', M.app('IsPIERunning', {})[:40])
