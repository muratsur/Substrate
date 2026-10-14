"""Height-map the level: trace straight down on a grid and print the first hit.

Also prints the route markers (fixtures) and the actors that can move the player.

Run:  python _tools/survey_floor.py [z_top] [z_bottom]
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
L = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
TOP = int(sys.argv[1]) if len(sys.argv) > 1 else 600
BOT = int(sys.argv[2]) if len(sys.argv) > 2 else -600
XS = [-3000, -2500, -2000, -1500, -1000, -500, 0, 500, 1000, 2000]
YS = [1400, 2500, 4000, 5500, 7000, 8000, 9000, 10000, 10500, 11000]


def floor(x, y):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'trace_world',
                             'arguments': {'start': {'x': x, 'y': y, 'z': TOP},
                                           'end': {'x': x, 'y': y, 'z': BOT}}})
    try:
        v = json.loads(r)['returnValue']
        return None if v is None else round(TOP - v)
    except Exception:
        return 'ERR'


def bounds(a):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds',
                             'arguments': {'actor': {'refPath': L + a}}})
    try:
        v = json.loads(r)['returnValue']
        return tuple(round(v['min'][k]) for k in 'xyz') + tuple(round(v['max'][k]) for k in 'xyz')
    except Exception:
        return None


M.init()
print('=== floor height (first hit from z=%d down to z=%d); "-" = nothing hit' % (TOP, BOT))
print('%7s %s' % ('y / x', ''.join('%7d' % x for x in XS)))
for y in YS:
    print('%7d %s' % (y, ''.join('%7s' % ('-' if (f := floor(x, y)) is None else f) for x in XS)))

print('=== route markers ===')
for name in ['BP_Fixture_C_%d' % i for i in range(9)] + ['BP_Terminal_C_0', 'BP_Airlock_C_0', 'BP_Airlock_C_1']:
    print('  %-22s %s' % (name, bounds(name)))
