"""Ways out of the west canal. Since the canal rescue was switched off for water exploration (2026-10-23), a player who
falls into the west canal (bed z 100, banks z 288, sealed at y 6355 in the south) cannot get out: a tester was stranded
there on 2026-11-14. This places kit stairs (SM_stair_01, as CanalExploration_DockStairs does at the dock) across the
canal, rising to the west bank, one south and one north of the stone crossing, then prints the height profile up each.
Usage: python _tools/canal_exit_stairs.py   (PIE stopped), then save L_SectorC."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
MESH = '/Game/Modular_Sewer_Kit/Meshes/Modules/Stairs/SM_stair_01.SM_stair_01'   # 1000 wide x 660 run x 200 rise
BED, BANK = 100.0, 288.0
# label: (y centre, x of the west bank edge = stair top, x of the stair foot)
STAIRS = {'CanalExit_Stairs_South': (7650.0, -2450.0, -1990.0), 'CanalExit_Stairs_North': (9300.0, -2350.0, -1990.0)}
WIDTH = 300.0

def c(ts, t, a):
    r = M.call('call_tool', {'toolset_name': ts, 'tool_name': t, 'arguments': a})
    try: return json.loads(r).get('returnValue')
    except Exception: return r[:300]
def bounds(ref): return c(M.ACT, 'get_actor_bounds', {'actor': {'refPath': ref}})
def top(x, y):
    d = c(M.SCN, 'trace_world', {'start': {'x': x, 'y': y, 'z': 500.0}, 'end': {'x': x, 'y': y, 'z': 0.0}})
    return None if d is None else round(500 - d)

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    probe = c(M.SCN, 'find_actors', {'name': 'CanalExploration_DockStairs', 'tag': '', 'collision_channels': []})
    assert probe and 'Maps/L_SectorC' in probe[0]['refPath'], 'not Substrate'
    body = c(M.OBJ, 'get_properties', {'instance': {'refPath': probe[0]['refPath'] + '.StaticMeshComponent0'}, 'properties': ['BodyInstance']})
    for label, (yc, xtop, xfoot) in STAIRS.items():
        print('==', label, 'profile before', [top(x, yc) for x in range(int(xtop) - 60, int(xfoot) + 61, 60)])
        found = c(M.SCN, 'find_actors', {'name': label, 'tag': '', 'collision_channels': []})
        if found: ref = found[0]['refPath']; print('exists')
        else:
            # yaw 270 turns the mesh's ascent (+y at the dock's yaw 180) to -x, toward the west bank
            xf = {'location': {'x': xtop, 'y': yc, 'z': BED}, 'rotation': {'pitch': 0.0, 'yaw': 270.0, 'roll': 0.0},
                  'scale': {'x': -WIDTH / 1000.0, 'y': (xfoot - xtop) / 660.0, 'z': (BANK - BED) / 200.0}}
            ref = c(M.SCN, 'add_to_scene_from_asset', {'asset_path': MESH, 'name': label, 'xform': xf})['refPath']
            b = bounds(ref)   # slide it so the footprint is exactly xtop..xfoot, centred on yc, standing on the bed
            xf['location'] = {'x': xtop + (xtop - b['min']['x']), 'y': yc + (yc - (b['min']['y'] + b['max']['y']) / 2), 'z': BED + (BED - b['min']['z'])}
            c(M.ACT, 'set_actor_transform', {'actor': {'refPath': ref}, 'xform': xf})
            # same collision as the dock stairs (complex-as-simple lives on the mesh asset)
            c(M.OBJ, 'set_properties', {'instance': {'refPath': ref + '.StaticMeshComponent0'}, 'values': json.dumps({'BodyInstance': {'collisionEnabled': 'QueryAndPhysics', 'collisionProfileName': 'BlockAll'}})})
            c(M.SCN, 'set_actor_folder', {'actor': {'refPath': ref}, 'folder_path': 'Substrate/CanalExits'})
        b = bounds(ref)
        print(ref.split('.')[-1], {k: [round(b['min'][k]), round(b['max'][k])] for k in 'xyz'})
        print('profile after ', [top(x, yc) for x in range(int(xtop) - 60, int(xfoot) + 61, 60)], '(west bank ... canal bed)')
