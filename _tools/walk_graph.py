"""Walkability map of Sector C for route-closure planning. Samples floor height on a 100-unit grid (in-editor batched
traces), links 4-neighbours whose height differs by <= 65 (MaxStepHeight), drops canal-rescue cells (floor < 248 inside a
BP_CanalRescue box), and answers: which cells are reachable from spawn, and does removing a bridge disconnect anything.
Writes _evidence/walk_grid.json (cached; delete to resample). Usage: python _tools/walk_graph.py"""
import sys, json, os, collections
sys.path.insert(0, '_tools')
import mcpx as M
X0, X1, Y0, Y1, STEP, ZTOP = -3600, 4400, 0, 11600, 100, 650.0
CACHE = '_evidence/walk_grid.json'
RESCUE = [(-2315, 2485, 5000, 8800), (-2315, 2485, 0, 5050), (-3100, 2500, 8980, 10820)]  # X/Y of BP_CanalRescue boxes (top Z 248 / 40)
BRIDGES = {'stone_crossing': (-2064, 8335), 'west_canal_W': (-3253, 765), 'west_canal_E': (-756, 765), 'east': (3051, 6311), 'north': (553, 10355)}
SPAWN = (0, 1400)
SCRIPT = """
import json
def run():
    out = []
    for x, y in %PTS%:
        h = execute_tool('editor_toolset.toolsets.scene.SceneTools.trace_world', json.dumps({'start': {'x': x, 'y': y, 'z': %Z%}, 'end': {'x': x, 'y': y, 'z': -600.0}}))['returnValue']
        out.append(None if h is None else round(%Z% - h))
    return {'z': out}
"""
def sample():
    # resumable: the partial grid is saved after every batch (~4 traces/s in-editor, ~40 min for the full grid)
    M.init()
    pts = [(int(x), int(y)) for y in range(Y0, Y1 + 1, STEP) for x in range(X0, X1 + 1, STEP)]
    part = CACHE + '.partial'
    grid = json.load(open(part)) if os.path.exists(part) else {}
    todo = [p for p in pts if f'{p[0]},{p[1]}' not in grid]
    for i in range(0, len(todo), 200):
        batch = todo[i:i + 200]
        r = M.call('call_tool', {'toolset_name': 'editor_toolset.toolsets.programmatic.ProgrammaticToolset', 'tool_name': 'execute_tool_script',
                                 'arguments': {'script': SCRIPT.replace('%PTS%', repr([(float(x), float(y)) for x, y in batch])).replace('%Z%', str(ZTOP))}})
        for (x, y), z in zip(batch, json.loads(json.loads(r)['returnValue'])['z']): grid[f'{x},{y}'] = z
        json.dump(grid, open(part, 'w'))
        print(f'  sampled {len(grid)}/{len(pts)}', flush=True)
    os.replace(part, CACHE)
    return grid
grid = json.load(open(CACHE)) if os.path.exists(CACHE) else sample()
REF = '_evidence/walk_grid_refined.json'
HEADROOM = 190   # player capsule is 192 tall
REFINE = '''
import json
def run():
    out = []
    for x, y, top in %PTS%:
        # nothing lies between z and ZTOP (the first downward trace came from there), so the real ceiling is the first
        # hit going UP from ZTOP; only if that leaves < HEADROOM is z an overhead surface to look below
        up = execute_tool('editor_toolset.toolsets.scene.SceneTools.trace_world', json.dumps({'start': {'x': x, 'y': y, 'z': %Z%}, 'end': {'x': x, 'y': y, 'z': %Z% + 600.0}}))['returnValue']
        z, ceiling = top, (%Z% + 600.0 if up is None else %Z% + up)
        for _ in range(4):                        # a hit with < HEADROOM of space above it is overhead: look below it
            if ceiling - z >= %HR%: break
            h = execute_tool('editor_toolset.toolsets.scene.SceneTools.trace_world', json.dumps({'start': {'x': x, 'y': y, 'z': z - 5.0}, 'end': {'x': x, 'y': y, 'z': -600.0}}))['returnValue']
            if h is None: z = None; break
            ceiling, z = z, round(z - 5.0 - h)
        out.append(z)
    return {'z': out}
'''
def refine():
    M.init()
    done = json.load(open(REF)) if os.path.exists(REF) else {}
    todo = [(k, z) for k, z in grid.items() if z is not None and ZTOP - z < HEADROOM and k not in done]
    for i in range(0, len(todo), 100):
        batch = todo[i:i + 100]
        pts = [(float(k.split(',')[0]), float(k.split(',')[1]), float(z)) for k, z in batch]
        r = M.call('call_tool', {'toolset_name': 'editor_toolset.toolsets.programmatic.ProgrammaticToolset', 'tool_name': 'execute_tool_script',
                                 'arguments': {'script': REFINE.replace('%PTS%', repr(pts)).replace('%Z%', str(ZTOP)).replace('%HR%', str(HEADROOM))}})
        for (k, _), z in zip(batch, json.loads(json.loads(r)['returnValue'])['z']): done[k] = z
        json.dump(done, open(REF, 'w'))
        print(f'  refined {len(done)}/{len(done) + len(todo) - i - len(batch)}', flush=True)
    return done
grid.update(refine() if ('--refine' in sys.argv or not os.path.exists(REF)) else json.load(open(REF)))
# trace_world uses the Visibility channel; blocks that collide with the player but ignore Visibility (the 230 blocks fixed
# on 2026-10-23) are invisible to it. Overlay their tops (collect_trace_invisible_blockers.py); taller than ZTOP = wall.
BLK = '_evidence/trace_invisible_blockers.json'
if os.path.exists(BLK):
    for b in json.load(open(BLK)):
        for x in range(X0, X1 + 1, STEP):
            if not b['xmin'] <= x <= b['xmax']: continue
            for y in range(Y0, Y1 + 1, STEP):
                if not b['ymin'] <= y <= b['ymax']: continue
                k = f'{x},{y}'
                grid[k] = None if b['zmax'] > ZTOP else max(grid.get(k) or -1e9, round(b['zmax']))
def walkable(x, y):
    z = grid.get(f'{x},{y}')
    if z is None: return None
    if z < 248 and any(a <= x <= b and c <= y <= d for a, b, c, d in RESCUE): return None   # canal water -> rescue teleport
    return z
# the grid only sees floors: walls taller than ZTOP and thin walls between samples are missed, so edges in a region can be
# checked with a horizontal trace 70 above the higher floor (shortcut: a line trace, not the 42-radius capsule, so gaps
# narrower than the player still count as open). Blocked edges are cached in WALLS.
WALLS = '_evidence/walk_walls.json'
EDGE = """
import json
def run():
    out = []
    for x, y, nx, ny, z in %E%:
        h = execute_tool('editor_toolset.toolsets.scene.SceneTools.trace_world', json.dumps({'start': {'x': x, 'y': y, 'z': z}, 'end': {'x': nx, 'y': ny, 'z': z}}))['returnValue']
        out.append(h is not None)
    return {'hit': out}
"""
walls = json.load(open(WALLS)) if os.path.exists(WALLS) else {}
def check_walls(x0, x1, y0, y1):
    M.init()
    todo = []
    for x in range(x0, x1 + 1, STEP):
        for y in range(y0, y1 + 1, STEP):
            z = walkable(x, y)
            for nx, ny in ((x + STEP, y), (x, y + STEP)):
                nz = walkable(nx, ny)
                k = f'{x},{y},{nx},{ny}'
                if z is not None and nz is not None and abs(nz - z) <= 65 and k not in walls:
                    todo.append((k, (float(x), float(y), float(nx), float(ny), float(max(z, nz) + 70))))
    for i in range(0, len(todo), 300):
        batch = todo[i:i + 300]
        r = M.call('call_tool', {'toolset_name': 'editor_toolset.toolsets.programmatic.ProgrammaticToolset', 'tool_name': 'execute_tool_script',
                                 'arguments': {'script': EDGE.replace('%E%', repr([e for _, e in batch]))}})
        for (k, _), hit in zip(batch, json.loads(json.loads(r)['returnValue'])['hit']): walls[k] = hit
        json.dump(walls, open(WALLS, 'w'))
        print(f'  edges {i + len(batch)}/{len(todo)}', flush=True)
def blocked(a, b):
    a, b = min(a, b), max(a, b)
    return walls.get(f'{a[0]},{a[1]},{b[0]},{b[1]}', False)
def reach(start, removed=frozenset()):
    seen, q = {start}, collections.deque([start])
    while q:
        x, y = q.popleft(); z = walkable(x, y)
        for nx, ny in ((x + STEP, y), (x - STEP, y), (x, y + STEP), (x, y - STEP)):
            if (nx, ny) in seen or (nx, ny) in removed: continue
            nz = walkable(nx, ny)
            if nz is not None and abs(nz - z) <= 65 and not blocked((x, y), (nx, ny)): seen.add((nx, ny)); q.append((nx, ny))
    return seen
def cells_near(c, r=250):
    return frozenset((x, y) for x in range(X0, X1 + 1, STEP) for y in range(Y0, Y1 + 1, STEP) if abs(x - c[0]) <= r and abs(y - c[1]) <= r)
if __name__ == '__main__':
    if '--walls' in sys.argv:
        check_walls(*map(int, sys.argv[sys.argv.index('--walls') + 1:][:4])); sys.exit()
    base = reach(SPAWN)
    print('reachable from spawn:', len(base), 'cells')
    fixtures = {'C1': (1469, 4342), 'C2': (3060, 6170), 'C3': (-2480, 7212), 'C4': (-1516, 8349), 'C5': (-2543, 10200)}
    snap = lambda p: (round(p[0] / STEP) * STEP, round(p[1] / STEP) * STEP)
    near = lambda s, p: any(abs(x - snap(p)[0]) <= 300 and abs(y - snap(p)[1]) <= 300 for x, y in s)
    print('fixtures reachable:', {k: near(base, v) for k, v in fixtures.items()})
    for b, c in BRIDGES.items():
        cut = cells_near(c)
        r = reach(SPAWN, cut)
        lost = {k for k, v in fixtures.items() if near(base, v) and not near(r, v)}
        print(f'remove {b:15s}: reachable {len(r):5d} (was {len(base)}), fixtures cut off: {sorted(lost) or "none"}')
