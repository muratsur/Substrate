import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
AT  = 'editor_toolset.toolsets.actor.ActorTools'
SCN = 'editor_toolset.toolsets.scene.SceneTools'
# start PIE if not running
if 'true' not in M.app('IsPIERunning', {}):
    M.app('StartPIE', {'options': {'bSimulate': False}})
    time.sleep(6)
r = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'find_actors',
    'arguments': {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': '/Script/Engine.Character'}}})
pawn = json.loads(r)['returnValue'][0]
def pos():
    t = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': pawn}}))['returnValue']['location']
    return (round(t['x']), round(t['y']), round(t['z']))
def teleport(x, y, z, label):
    M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
        'arguments': {'actor': pawn, 'xform': {'location': {'x': float(x), 'y': float(y), 'z': float(z)}}}})
    time.sleep(1.2)
    p = pos()
    held = abs(p[0] - x) < 300 and abs(p[1] - y) < 300 and abs(p[2] - z) < 500
    print('%-28s placed at %s -> holds %s' % (label, p, 'OK' if held else 'FELL'))
    return held
r0 = teleport(-18000, 700, 400, 'mid-extension floor')
r1 = teleport(-23000, 700, 400, 'deep extension floor')
r2 = teleport(-24900, 700, 400, 'just before blockade')
print('RESULT:', 'ALL THREE HOLD - west extension is walkable' if (r0 and r1 and r2) else 'SOME POSITION DID NOT HOLD - investigate')
