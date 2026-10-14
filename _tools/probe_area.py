"""Map trap zones with the real pawn: drop it on a grid, see where it ends up.

  S = stayed (solid floor)      R = teleported back to the spawn      ? = unreadable

Run:  python _tools/probe_area.py X0 X1 Y0 Y1 [step]
      python _tools/probe_area.py -1500 2000 1400 3400 500
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
        return None


M.init()
a = [int(v) for v in sys.argv[1:5]]
step = int(sys.argv[5]) if len(sys.argv) > 5 else 500
x0, x1, y0, y1 = a
if 'true' not in M.app('IsPIERunning', {}):
    M.app('StartPIE', {'options': {'bSimulate': False}})
    time.sleep(12)
pawn = (find('/Script/Engine.Character') or [None])[0]
if not pawn:
    sys.exit('no pawn in PIE')

print('%7s %s' % ('y / x', ''.join('%7d' % x for x in range(x0, x1 + 1, step))))
for y in range(y0, y1 + 1, step):
    row = []
    for x in range(x0, x1 + 1, step):
        M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
                             'arguments': {'actor': {'refPath': pawn},
                                           'xform': {'location': {'x': float(x), 'y': float(y), 'z': 500.0}}}})
        time.sleep(1.8)
        p = loc(pawn)
        if p is None:
            row.append('?')
        elif abs(p[0] - SPAWN[0]) < 150 and abs(p[1] - SPAWN[1]) < 150 and (x, y) != SPAWN:
            row.append('R')
        else:
            row.append('S')
    print('%7d %s' % (y, ''.join('%7s' % c for c in row)))
