import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M

EA = 'EditorToolset.EditorAppToolset'

def ray(orig, yaw, pitch=0.0):
    M.app('SetCameraTransform', {'transform': {'location': {'x': orig[0], 'y': orig[1], 'z': orig[2]},
        'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': 0.0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
    r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'ScreenCoordsToWorld',
                             'arguments': {'coords': {'x': 0.5, 'y': 0.5}}})
    try: return json.loads(r)['returnValue']
    except Exception: return None

M.init()
time.sleep(1)
print('--- west rays after collision disable (expect NO low hits before -2500) ---')
for z in (170.0, 200.0, 240.0, 280.0, 310.0, 360.0, 430.0, 650.0):
    h = ray((-1480.0, 8449.0, z), 180.0)
    print('  z=%4.0f -> %s' % (z, ('hit x=%.0f (dist %.0f)' % (h['x'], abs(h['x']+1480))) if h else 'no hit'))
