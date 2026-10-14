import sys, json, time, math
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
EA = 'EditorToolset.EditorAppToolset'

def find(cls):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
        'arguments': {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': cls}}})
    try: return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception: return []

def put(ref, xyz, yaw=None):
    args = {'actor': {'refPath': ref},
            'xform': {'location': {'x': float(xyz[0]), 'y': float(xyz[1]), 'z': float(xyz[2])}}}
    if yaw is not None:
        args['xform']['rotation'] = {'pitch': 0.0, 'yaw': float(yaw), 'roll': 0.0}
    M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform', 'arguments': args})

def loc(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': ref}}})
    try:
        v = json.loads(r)['returnValue']['location']; return (v['x'], v['y'], v['z'])
    except Exception: return None

M.init()
M.app('StartPIE', {'options': {'bSimulate': False}})
time.sleep(12)
pawn = (find('/Script/Engine.Character') or [None])[0]
if not pawn: sys.exit('no pawn in PIE')
print('pawn:', pawn.split(':')[-1])

start = ( -1597.0, 8449.0, 385.0 )
put(pawn, start, yaw=270.0)  # face west (-X)
time.sleep(1.0)
print('placed at', loc(pawn))

# step west in 100-unit increments until position stops advancing
x = start[0]
prev = None
for i in range(40):
    x -= 100
    put(pawn, (x, start[1], start[2]), yaw=270.0)
    time.sleep(0.6)
    cur = loc(pawn)
    if cur is None: break
    moved = prev is None or abs(cur[0] - prev[0]) > 1
    print('step %02d  target x=%.0f  actual (%.0f, %.0f, %.0f) %s' % (i, x, cur[0], cur[1], cur[2], '' if moved else '  <-- STUCK'))
    if prev is not None and abs(cur[0] - prev[0]) < 1 and abs(cur[1] - prev[1]) < 1:
        print('BLOCKED at x=%.0f (last free x=%.0f)' % (x, prev[0]))
        break
    prev = cur

# capture the viewport from the player pose so we can see what blocks
p = loc(pawn)
pose = {'location': {'x': p[0], 'y': p[1], 'z': p[2] + 60},
        'rotation': {'pitch': 0, 'yaw': 270, 'roll': 0}}
r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'CaptureViewport',
                         'arguments': {'captureTransform': pose, 'annotations': {}}})
d = json.loads(r)['returnValue']
img = (d.get('image') or d)
import base64, os
os.makedirs('_tools/shots', exist_ok=True)
with open('_tools/shots/west_block.png', 'wb') as f:
    f.write(base64.b64decode(img['data']))
print('captured _tools/shots/west_block.png')

# list visible actors at that pose
r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'GetVisibleActors', 'arguments': {}})
try:
    vis = [a['refPath'].split(':')[-1] for a in json.loads(r)['returnValue']]
    print('in view (%d):' % len(vis), vis[:40])
except Exception:
    print('visible actors failed')
