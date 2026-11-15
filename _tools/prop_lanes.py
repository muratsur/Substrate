"""Does a solid fixture prop cut its walkway? For each sewer/transit fixture (rows 0-8) this samples floor height on a
20 cm grid in a 5 m window around it, erodes the walkable cells by the player's capsule radius (42), and counts the
walkable regions that reach the window's edge - once as built, once with the prop's own cells treated as floor. A prop
that raises the count (or strands cells) blocks the path. Read-only. Usage: python _tools/prop_lanes.py  (PIE stopped)
shortcut: downward line traces, so overhangs above 1.8 m and gaps under railings are not modelled; walk it if in doubt."""
import sys, json, collections
sys.path.insert(0, '_tools')
import mcpx as M
STEP, HALF, R, STEPH = 20, 250, 42, 45
SCRIPT = """
import json
def run():
    out = []
    for x, y in %PTS%:
        h = execute_tool('editor_toolset.toolsets.scene.SceneTools.trace_world', json.dumps({'start': {'x': x, 'y': y, 'z': %Z%}, 'end': {'x': x, 'y': y, 'z': %Z% - 400.0}}))['returnValue']
        out.append(None if h is None else round(%Z% - h))
    return {'z': out}
"""
def c(ts, t, a): return json.loads(M.call('call_tool', {'toolset_name': ts, 'tool_name': t, 'arguments': a})).get('returnValue')

def heights(cx, cy, ztop):
    n = range(-HALF, HALF + 1, STEP)
    pts = [(float(cx + dx), float(cy + dy)) for dy in n for dx in n]
    z = []
    for i in range(0, len(pts), 150):   # ~4 traces/s in-editor; a whole window in one request times out
        r = M.call('call_tool', {'toolset_name': 'editor_toolset.toolsets.programmatic.ProgrammaticToolset', 'tool_name': 'execute_tool_script',
                                 'arguments': {'script': SCRIPT.replace('%PTS%', repr(pts[i:i + 150])).replace('%Z%', str(ztop))}})
        z += json.loads(json.loads(r)['returnValue'])['z']
    return {(i % len(n), i // len(n)): v for i, v in enumerate(z)}, len(n)

def regions(free, n):
    k = R // STEP
    ok = {p for p in free if all((p[0] + i, p[1] + j) in free or not (0 <= p[0] + i < n and 0 <= p[1] + j < n)
                                 for i in range(-k, k + 1) for j in range(-k, k + 1) if i * i + j * j <= k * k)}
    seen, out = set(), []
    for s in ok:
        if s in seen: continue
        comp, q = set(), collections.deque([s]); seen.add(s)
        while q:
            p = q.popleft(); comp.add(p)
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                t = (p[0] + d[0], p[1] + d[1])
                if t in ok and t not in seen: seen.add(t); q.append(t)
        out.append(comp)
    edge = [r for r in out if any(0 in p or n - 1 in p for p in r)]
    return len(edge), sum(len(r) for r in out) - sum(len(r) for r in edge)   # regions reaching the edge, stranded cells

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    fx = c(M.SCN, 'find_actors', {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': '/Game/Substrate/Core/BP_Fixture.BP_Fixture_C'}})
    assert fx and 'L_SectorC' in fx[0]['refPath'], 'not Substrate'
    bad = 0
    for a in fx:
        ref = {'refPath': a['refPath']}
        p = json.loads(c(M.OBJ, 'get_properties', {'instance': ref, 'properties': ['FixtureID', 'RowOrder']}))
        if p['RowOrder'] > 8 or (sys.argv[1:] and p['FixtureID'][:4] not in sys.argv[1:]): continue   # optional: only these IDs, e.g. C-02
        t = c(M.ACT, 'get_actor_transform', {'actor': ref})['location']
        h, n = heights(t['x'], t['y'], t['z'] + 150)
        mid = n // 2
        # the deck the prop stands on: commonest height within 1.6 m of it, from 1.5 m below the actor up to it (the whole window's
        # commonest height was the canal bed for C-03 and the lower floor for C-02, which hid a blocking C-02)
        floor = collections.Counter(round(v / 5) * 5 for q, v in h.items() if v is not None and t['z'] - 150 <= v <= t['z'] + 10 and (q[0] - mid) ** 2 + (q[1] - mid) ** 2 <= (160 // STEP) ** 2).most_common(1)[0][0]
        walk = lambda v: v is not None and abs(v - floor) <= STEPH
        prop = {q for q, v in h.items() if not walk(v) and v is not None and v > floor and (q[0] - mid) ** 2 + (q[1] - mid) ** 2 <= (100 // STEP) ** 2}
        free = {q for q, v in h.items() if walk(v)}
        withp, without = regions(free, n), regions(free | prop, n)
        blocks = withp[0] > without[0] or withp[1] > without[1] + len(prop)
        bad += blocks
        print(f"{p['FixtureID']:22} floor {floor:5} prop cells {len(prop):3}  regions/stranded with prop {withp}  without {without}  {'BLOCKS' if blocks else 'ok'}")
    print('blocking props:', bad)
