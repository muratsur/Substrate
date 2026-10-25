"""Light the dark checklist/anomaly sites found by audit_fixture_lighting.py (DESIGN.md: every fixture sits in its own
pool of light). For each site: find the nearest wall at lamp height, mount a BP_Light_02 (the red wall lamp used across
Sector C) on it ~330 above the site, facing out of the wall. Same blueprint and light settings as the existing lamps.
Usage: python _tools/add_fixture_lamps.py [--dry-run]"""
import sys, json, math
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
LAMP = '/Game/Modular_Sewer_Kit/Blueprint/Light/BP_Light_02.BP_Light_02'
SITES = {  # label: (x, y, z) from _evidence/fixture_lighting.txt
    'Fixture_C5': (-2543, 10200, 430), 'Fixture_C1': (1469, 4342, 430), 'Fixture_C2': (3060, 6170, 430),
    'Fixture_C4': (-1516, 8349, 420), 'Anomaly_Growth_C': (2200, 5200, 430)}
LIFT, REACH = 330.0, 700.0
def trace(a, b):
    h = json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'trace_world', 'arguments': {'start': dict(zip('xyz', a)), 'end': dict(zip('xyz', b))}})).get('returnValue')
    return h
for site, (x, y, z) in SITES.items():
    zl = z + LIFT
    best = None
    for k in range(16):
        a = math.radians(k * 22.5); d = (math.cos(a), math.sin(a))
        h = trace((x, y, zl), (x + d[0] * REACH, y + d[1] * REACH, zl))
        if h is not None and h > 30 and (best is None or h < best[0]): best = (h, d)   # <30: trace started inside geometry
    if best is None: print(site, 'no wall within', REACH, '- skipped'); continue
    h, d = best
    px, py = x + d[0] * (h - 20), y + d[1] * (h - 20)        # 20 off the wall surface
    out = (-d[0], -d[1])                                       # lamp front faces back toward the site
    yaw = math.degrees(math.atan2(-out[0], out[1]))            # BP_Light_02 front is its local +Y
    label = 'FixtureLamp_' + site
    print(f'{label}: wall {h:.0f} away, lamp at ({px:.0f}, {py:.0f}, {zl:.0f}) yaw {yaw:.0f}')
    if '--dry-run' in sys.argv: continue
    if json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': label, 'tag': '', 'collision_channels': []}})).get('returnValue'):
        print('   already exists'); continue
    raw = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'add_to_scene_from_asset', 'arguments': {'asset_path': LAMP, 'name': label,
        'xform': {'location': {'x': px, 'y': py, 'z': zl}, 'rotation': {'pitch': 0.0, 'yaw': yaw, 'roll': 0.0}, 'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}}})
    if not raw.startswith('{'): sys.exit(raw)
    print('   placed', json.loads(raw)['returnValue']['refPath'].split('.')[-1])
