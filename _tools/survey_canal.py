"""Zoom in on the canal end (where BP_CanalRescue_C_0 sits) and list stair-ish actors.

Run:  python _tools/survey_canal.py
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
L = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
XS = [-3200, -3000, -2800, -2600, -2400, -2200, -2000, -1800, -1600, -1400, -1200]
YS = [8500, 8750, 9000, 9250, 9500, 9750, 10000, 10250, 10500, 10750, 11000, 11250]


def floor(x, y, top=600, bot=-400):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'trace_world',
                             'arguments': {'start': {'x': x, 'y': y, 'z': top},
                                           'end': {'x': x, 'y': y, 'z': bot}}})
    try:
        v = json.loads(r)['returnValue']
        return None if v is None else round(top - v)
    except Exception:
        return 'E'


M.init()
print('=== canal end floor map (first hit from z=600 down to z=-400)')
print('%7s %s' % ('y / x', ''.join('%6d' % x for x in XS)))
for y in YS:
    print('%7d %s' % (y, ''.join('%6s' % ('-' if (f := floor(x, y)) is None else f) for x in XS)))

print('=== actors whose label suggests a way down / across ===')
for term in ('Stair', 'Step', 'Ramp', 'Ladder', 'Catwalk', 'Walkway', 'Bridge', 'Canal', 'Water', 'Grate', 'Outfall', 'Tunnel'):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                             'arguments': {'name': term, 'tag': '', 'collision_channels': [],
                                           'actor_type': {'refPath': '/Script/Engine.Actor'}}})
    try:
        got = [a['refPath'].split(':')[-1] for a in json.loads(r).get('returnValue', [])]
    except Exception:
        got = ['ERR']
    print('  %-9s %s' % (term, got[:12]))
