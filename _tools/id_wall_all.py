import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

EA = 'EditorToolset.EditorAppToolset'
AT = 'editor_toolset.toolsets.actor.ActorTools'

def bounds(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}})
    return json.loads(r)['returnValue']

M.init()
# camera at the blocked spot facing west, edit mode now
M.app('SetCameraTransform', {'transform': {'location': {'x': -1500.0, 'y': 8449.0, 'z': 300.0},
    'rotation': {'pitch': 0.0, 'yaw': 180.0, 'roll': 0.0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'GetVisibleActors', 'arguments': {}})
refs = [a['refPath'] for a in json.loads(r)['returnValue']]
print('%d visible actors' % len(refs))
for ref in refs:
    if 'StaticMesh' not in ref.split('.')[-1]:
        continue
    try:
        b = bounds(ref)
    except Exception:
        continue
    mn, mx = b.get('min'), b.get('max')
    if not isinstance(mn, dict):
        continue
    # anything crossing the x=-1604 plane near the walk lane y 8100..8800, z below 400
    if mn['x'] - 60 <= -1604 <= mx['x'] + 60 and mn['y'] <= 8449 <= mx['y'] and mn['z'] < 400 and mx['z'] > 150:
        print('%-52s x[%7.0f..%7.0f] y[%7.0f..%7.0f] z[%7.0f..%7.0f]' % (
            ref.split(':')[-1], mn['x'], mx['x'], mn['y'], mx['y'], mn['z'], mx['z']))
