"""Legibility audit (DESIGN.md 'dark but legible'): for every BP_Fixture and BP_AnomalySocket, find the strongest point/spot
light reaching it and rank sites by an approximate inverse-square illuminance. Read-only."""
import sys, json, math
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
L = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
def find(cls):
    return [a['refPath'].split('.')[-1] for a in json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': cls}}}))['returnValue']]
def loc(n):
    return json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': L + n}}}))['returnValue']['location']
def label(n):
    return json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_label', 'arguments': {'actor': {'refPath': L + n}}}))['returnValue']
lights = []
for cls, comp in (('/Script/Engine.PointLight', 'LightComponent0'), ('/Script/Engine.SpotLight', 'LightComponent0')):
    for n in find(cls):
        try:
            p = json.loads(json.loads(M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': L + n + '.' + comp}, 'properties': ['Intensity', 'AttenuationRadius', 'bVisible']}}))['returnValue'])
        except Exception:
            continue
        if p.get('bVisible') is False: continue
        lights.append((n, loc(n), p.get('Intensity', 0), p.get('AttenuationRadius', 1000)))
# BP lights (BP_Light_C etc.) carry their own components; include their world location with a typical intensity flag
bp_lights = [n for n in (a['refPath'].split('.')[-1] for a in json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': '', 'tag': '', 'collision_channels': []}}))['returnValue']) if n.startswith('BP_Light')]
bp = [(n, loc(n)) for n in bp_lights]
for n in bp_lights:  # BP_Light lamps hold a SpotLight component; count them as real lights
    try:
        p = json.loads(json.loads(M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': L + n + '.SpotLight'}, 'properties': ['Intensity', 'AttenuationRadius', 'bVisible']}}))['returnValue'])
    except Exception:
        continue
    if p.get('bVisible') is not False: lights.append((n, loc(n), p.get('Intensity', 0), p.get('AttenuationRadius', 1000)))
print(f'{len(lights)} point/spot lights, {len(bp)} BP_Light actors')
sites = [(n, 'fixture') for n in find('/Game/Substrate/Core/BP_Fixture.BP_Fixture_C')] + [(n, 'anomaly') for n in find('/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C')]
rows = []
for n, kind in sites:
    s = loc(n)
    best, bestn, bestd = 0.0, '-', 1e9
    for ln, l, inten, rad in lights:
        d = math.dist((s['x'], s['y'], s['z']), (l['x'], l['y'], l['z']))
        if d < rad:
            e = inten / max(d / 100.0, 0.5) ** 2   # rough: candela-ish / m^2
            if e > best: best, bestn, bestd = e, ln, d
    nearest_bp = min((math.dist((s['x'], s['y'], s['z']), (l['x'], l['y'], l['z'])) for _, l in bp), default=1e9)
    rows.append((best, kind, label(n), round(s['x']), round(s['y']), round(s['z']), bestn, round(bestd), round(nearest_bp)))
rows.sort()
print('illum  kind     label                          x      y      z   best_light             dist  nearestBP_Light')
for r in rows:
    print(f'{r[0]:6.1f} {r[1]:8s} {r[2][:30]:30s} {r[3]:6d} {r[4]:6d} {r[5]:5d}  {r[6][:20]:20s} {r[7]:6d} {r[8]:6d}')
