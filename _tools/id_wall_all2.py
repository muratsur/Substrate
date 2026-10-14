import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

EA = 'EditorToolset.EditorAppToolset'
AT = 'editor_toolset.toolsets.actor.ActorTools'

def bounds(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}})
    return json.loads(r)['returnValue']

M.init()
LEV = '/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:'
# camera right at the player eye, facing west
M.app('SetCameraTransform', {'transform': {'location': {'x': -1534.0, 'y': 8409.0, 'z': 430.0},
    'rotation': {'pitch': -10.0, 'yaw': 180.0, 'roll': 0.0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'GetVisibleActors', 'arguments': {}})
refs = [a['refPath'] for a in json.loads(r)['returnValue']]
print('%d visible actors from player pose' % len(refs))
hits = []
for ref in refs:
    try:
        b = bounds(ref)
    except Exception:
        continue
    mn, mx = b.get('min'), b.get('max')
    if not (isinstance(mn, dict) and isinstance(mx, dict)):
        continue
    # anything crossing the x wall plane within reach of the walk lane, up to chest height
    if mn['x'] - 80 <= -1604 <= mx['x'] + 80 and mn['y'] - 80 <= 8409 <= mx['y'] + 80 and mn['z'] < 400 and mx['z'] > 200:
        hits.append((ref.split(':')[-1], mn, mx))
print(' actors crossing the x~-1604 plane at your lane:')
for name, mn, mx in hits:
    print('   %-56s x[%7.0f..%7.0f] y[%7.0f..%7.0f] z[%7.0f..%7.0f]' % (name, mn['x'], mx['x'], mn['y'], mx['y'], mn['z'], mx['z']))
if not hits:
    print('   (none)')
