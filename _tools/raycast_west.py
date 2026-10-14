import sys, json, math
sys.path.insert(0, '_tools')
import mcpx as M

EA = 'EditorToolset.EditorAppToolset'

M.init()
orig = (-1500.0, 8449.0, 430.0)
M.app('SetCameraTransform', {'transform': {'location': {'x': orig[0], 'y': orig[1], 'z': orig[2]},
    'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
for yaw in (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0):
    M.app('SetCameraTransform', {'transform': {'location': {'x': orig[0], 'y': orig[1], 'z': orig[2]},
        'rotation': {'pitch': 0.0, 'yaw': yaw, 'roll': 0.0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
    r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'ScreenCoordsToWorld',
                             'arguments': {'coords': {'x': 0.5, 'y': 0.5}}})
    try:
        h = json.loads(r)['returnValue']
        dx, dy = h['x'] - orig[0], h['y'] - orig[1]
        dist = math.hypot(dx, dy)
        print('yaw %5.0f -> hit (%.0f, %.0f, %.0f)  delta=(%.0f, %.0f) dist=%.0f' % (yaw, h['x'], h['y'], h['z'], dx, dy, dist))
    except Exception:
        print('yaw %5.0f -> %s' % (yaw, r[:200]))
