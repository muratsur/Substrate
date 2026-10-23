"""Enable BlockAll collision on every concrete block / wall / pillar that the map left at NoCollision.
Source list: _evidence/nocollision_whole_map.txt (from audit_nocollision_walkables.py). SM_detail_* rubble stays NoCollision."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
LVL = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
names = [l.split()[0] for l in open('_evidence/nocollision_whole_map.txt') if l.startswith('     ')]
SPAWNS = [(0, 1400, 360)]  # PlayerStart and BP_CanalRescue target; capsule r=42 hh=96
for n in names:
    b = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': LVL + n}}}))['returnValue']
    mn, mx = b['min'], b['max']
    for x, y, z in SPAWNS:
        assert not (mn['x'] - 42 < x < mx['x'] + 42 and mn['y'] - 42 < y < mx['y'] + 42 and mn['z'] < z + 96 and mx['z'] > z - 90), f'{n} overlaps spawn'
ok = 0
for n in names:
    rp = LVL + n + '.StaticMeshComponent0'
    M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': rp}, 'values': json.dumps({'BodyInstance': {'collisionEnabled': 'QueryAndPhysics', 'collisionProfileName': 'BlockAll'}})}})
    bi = json.loads(json.loads(M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties', 'arguments': {'instance': {'refPath': rp}, 'properties': ['BodyInstance']}}))['returnValue'])['BodyInstance']
    if (bi['collisionEnabled'], bi['collisionProfileName']) == ('QueryAndPhysics', 'BlockAll'): ok += 1
    else: print('FAIL', n, bi['collisionEnabled'], bi['collisionProfileName'])
print(f'fixed {ok}/{len(names)}')
