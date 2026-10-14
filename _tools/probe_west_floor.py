import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
AT  = 'editor_toolset.toolsets.actor.ActorTools'
SCN = 'editor_toolset.toolsets.scene.SceneTools'
if 'true' not in M.app('IsPIERunning', {}):
    M.app('StartPIE', {'options': {'bSimulate': False}})
    time.sleep(6)
r = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'find_actors',
    'arguments': {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': '/Script/Engine.Character'}}})
pawn = json.loads(r)['returnValue'][0]
def pos():
    t = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': pawn}}))['returnValue']['location']
    return (round(t['x']), round(t['y']), round(t['z']))
print('scanning floor at y=700 from x=-12000 to -25000, step 500:')
solid = []
gaps = []
for x in range(-12000, -25001, -500):
    M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
        'arguments': {'actor': pawn, 'xform': {'location': {'x': float(x), 'y': 700.0, 'z': 400.0}}}})
    time.sleep(0.8)
    p = pos()
    ok = p[0] > x - 600 and p[0] < x + 600  # stayed in this 1000cm slab (or holding position near it)
    floor_here = ok and p[2] > -300
    if floor_here:
        solid.append(x)
    else:
        gaps.append((x, p))
    print('x=%7d -> pawn %-24s %s' % (x, p, 'FLOOR' if floor_here else 'GAP/FALL'))
print()
print('solid slab starts:', solid[:3], '...', solid[-3:] if solid else 'none')
print('gap/fall positions:', gaps[:6])
json.dump({'solid': solid, 'gaps': gaps}, open('_tools/shots/west_floor_scan.json', 'w'))
