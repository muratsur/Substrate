"""Pre-package collision check for L_SectorC. Exits 1 (and lists offenders) when it finds:
  1. a visible structural mesh (blocks, floors, stairs, walls...) without QueryAndPhysics collision -> player sinks/walks through
  2. a hidden mesh that blocks the player and pokes above the water line -> invisible wall
  3. a placed BP_Terminal whose Body blocks Pawn -> raised terminal blocks the player's own capsule
Usage: python _tools/preflight_collision.py [--selftest] [--full]  (--full ignores the rubble cache)   (editor must be running with the MCP server)"""
import sys, json
from pathlib import Path
sys.path.insert(0, '_tools')

LEVEL = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
WATER_Z = 190.0
STRUCTURAL = ('SM_concrete', 'SM_stair', 'SM_floor', 'SM_platform', 'SM_path', 'SM_double_bridge',
              'SM_module_wall', 'SM_module_high_wall', 'SM_pillar', 'SM_arch', 'SM_sewer', 'SM_entrance')
# Hidden blockers reviewed 2026-10-23 as flush with the visible floor (or a deliberate railing), pinned to their top Z.
# shortcut: pinned by actor name + top Z, re-review and update here when one is moved on purpose.
REVIEWED_HIDDEN = {'StaticMeshActor_229': 275,   # CanalDoorway_SafetyFloor, floor modules top 270
                   'StaticMeshActor_3689': 290,  # SectorB_FloorSafety, under SM_path
                   'StaticMeshActor_3690': 290,  # SectorD_FloorSafety, inside alien-organism ground
                   'StaticMeshActor_3797': 595}  # Bridge_Safety_Barrier_East, thin invisible railing

COLLECT = """
import json
def run():
    T = lambda tool, args: execute_tool(tool, json.dumps(args))['returnValue']
    rows = []
    for name in %NAMES%:
        rp = '%LEVEL%' + name   # editor world, even while PIE is running
        comp = rp + ('.StaticMeshComponent0' if name.startswith('StaticMeshActor') else '.Body')
        try:
            p = json.loads(T('editor_toolset.toolsets.object.ObjectTools.get_properties', {'instance': {'refPath': comp}, 'properties': ['StaticMesh', 'BodyInstance', 'bHiddenInGame', 'bVisible']}))
            hidden = bool(p.get('bHiddenInGame')) or p.get('bVisible') is False
            # bounds only matter for the hidden-blocker rule; skipping them halves the editor calls
            b = T('editor_toolset.toolsets.actor.ActorTools.get_actor_bounds', {'actor': {'refPath': rp}}) if hidden else {'min': {'x': 0, 'y': 0, 'z': 0}, 'max': {'x': 0, 'y': 0, 'z': 0}}
        except Exception:
            continue   # runtime-only actor (PIE) or no such component
        bi = p.get('BodyInstance', {})
        rows.append({'name': name, 'mesh': (p.get('StaticMesh') or {}).get('refPath', '').split('.')[-1],
                     'hidden': hidden,
                     'enabled': bi.get('collisionEnabled'), 'profile': bi.get('collisionProfileName'),
                     'responses': {r['channel']: r['response'] for r in bi.get('collisionResponses', {}).get('responseArray', [])},
                     'zmin': b['min']['z'], 'zmax': b['max']['z'],
                     'dx': b['max']['x'] - b['min']['x'], 'dy': b['max']['y'] - b['min']['y']})
    return {'rows': rows}
""".replace('%LEVEL%', LEVEL)
CHUNK = 150  # each call must finish inside ue_mcp's 120 s HTTP timeout


def blocks_pawn(r):
    if r['enabled'] in ('NoCollision', 'QueryOnly', None): return False
    if r['profile'] in ('NoCollision', 'OverlapAll', 'OverlapAllDynamic', 'UI', 'Trigger', 'Spectator'): return False
    return r['responses'].get('Pawn', 'ECR_Block') == 'ECR_Block'


def problems(rows):
    out = []
    for r in rows:
        if r['name'].startswith('BP_Terminal_C'):
            if blocks_pawn(r): out.append(f"{r['name']}: terminal Body blocks Pawn (raised terminal blocks the player)")
        elif r['mesh'].startswith(STRUCTURAL) and not r['hidden'] and r['enabled'] != 'QueryAndPhysics':
            out.append(f"{r['name']} ({r['mesh']}): visible structure has collision {r['enabled']} -> player walks/sinks through it")
        elif r['hidden'] and blocks_pawn(r) and r['zmax'] > WATER_Z + 5 and max(r['dx'], r['dy']) > 150 \
                and abs(r['zmax'] - REVIEWED_HIDDEN.get(r['name'], -1e9)) > 2:
            out.append(f"{r['name']} ({r['mesh']}): hidden blocker Z[{r['zmin']:.0f}..{r['zmax']:.0f}] above water -> invisible wall/floor")
    return out


def selftest():
    ok = dict(name='StaticMeshActor_1', mesh='SM_concrete_01', hidden=False, enabled='QueryAndPhysics', profile='BlockAll', responses={}, zmin=72, zmax=288, dx=200, dy=280)
    rows = [ok,
            dict(ok, name='StaticMeshActor_2', enabled='NoCollision', profile='NoCollision'),
            dict(ok, name='StaticMeshActor_3', mesh='Cube', hidden=True, zmin=290, zmax=330, dx=2670, dy=3800),
            dict(ok, name='StaticMeshActor_4', mesh='Cube', hidden=True, zmin=145, zmax=185, dx=2670, dy=3800),
            dict(ok, name='StaticMeshActor_229', mesh='Cube', hidden=True, zmin=255, zmax=275, dx=600, dy=200),
            dict(ok, name='StaticMeshActor_3689', mesh='Cube', hidden=True, zmin=350, zmax=390, dx=880, dy=2700),
            dict(ok, name='StaticMeshActor_5', mesh='SM_detail_01', enabled='NoCollision', profile='NoCollision'),
            dict(ok, name='BP_Terminal_C_0', mesh='Cube', profile='BlockAllDynamic', zmax=430),
            dict(ok, name='BP_Terminal_C_1', mesh='Cube', profile='Custom', responses={'Pawn': 'ECR_Ignore'}, zmax=430)]
    names = sorted(p.split(':')[0].split(' ')[0] for p in problems(rows))
    assert names == ['BP_Terminal_C_0', 'StaticMeshActor_2', 'StaticMeshActor_3', 'StaticMeshActor_3689'], names
    print('selftest ok')


if __name__ == '__main__':
    selftest()
    if '--selftest' in sys.argv: sys.exit(0)
    import mcpx as M
    M.init()
    actors = json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': '', 'tag': '', 'collision_channels': []}}))['returnValue']
    names = sorted({n for n in (a['refPath'].split('.')[-1] for a in actors) if n.startswith(('StaticMeshActor', 'BP_Terminal_C'))})
    assert len(names) > 1000, f'only {len(names)} actors found - is L_SectorC loaded in the editor?'
    # shortcut: actors once seen as SM_detail rubble are skipped by name; delete the cache after re-meshing rubble actors.
    cache = Path(__file__).with_name('preflight_rubble_cache.json')
    rubble = set(json.loads(cache.read_text())) if cache.exists() and '--full' not in sys.argv else set()
    todo = [n for n in names if n not in rubble]
    rows = []
    for i in range(0, len(todo), CHUNK):
        res = M.call('call_tool', {'toolset_name': 'editor_toolset.toolsets.programmatic.ProgrammaticToolset', 'tool_name': 'execute_tool_script',
                                   'arguments': {'script': COLLECT.replace('%NAMES%', repr(todo[i:i + CHUNK]))}})
        rows += json.loads(json.loads(res)['returnValue'])['rows']
    cache.write_text(json.dumps(sorted(rubble | {r['name'] for r in rows if r['mesh'].startswith('SM_detail')})))
    found = problems(rows)
    print(f'preflight_collision: {len(rows)} actors checked ({len(names) - len(todo)} cached rubble skipped), {len(found)} problem(s)')
    for p in found: print('  FAIL', p)
    sys.exit(1 if found else 0)
