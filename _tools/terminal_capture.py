"""T1.4 terminal: capture the viewport around the placed terminal and save the PNG.

Run:  python _tools/terminal_capture.py <side>   side=-1 (view from -X) or 1 (from +X)
"""
import sys, json, base64, os
sys.path.insert(0, '_tools')
import mcpx as M

LOC = (-200.0, 1500.0, 430.0)
OUT = '_tools/capture'


def main():
    M.init()
    side = float(sys.argv[1]) if len(sys.argv) > 1 else -1.0
    dist = float(sys.argv[2]) if len(sys.argv) > 2 else 260.0
    cam = {'location': {'x': LOC[0] + side * dist, 'y': LOC[1], 'z': LOC[2] + 5.0},
           'rotation': {'pitch': 0.0, 'yaw': 0.0 if side < 0 else 180.0, 'roll': 0.0}}
    M.call('call_tool', {'toolset_name': M.APP, 'tool_name': 'SetCameraTransform',
                         'arguments': {'transform': cam}})
    r = M.call('call_tool', {'toolset_name': M.APP, 'tool_name': 'CaptureViewport',
                             'arguments': {'captureTransform': cam, 'annotations': None,
                                           'bShowUI': False}})
    if not r.strip().startswith('{'):
        print('ERR', r[:300]); return
    d = json.loads(r)['returnValue']
    img = d.get('image') or {}
    data = img.get('data') or ''
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'view_%s.png' % ('negx' if side < 0 else 'posx'))
    if data:
        with open(path, 'wb') as f:
            f.write(base64.b64decode(data))
        print('wrote', path, os.path.getsize(path), 'bytes')
    else:
        print('no image data; keys:', list(d.keys()))
    print('meta:', {k: v for k, v in d.items() if k != 'image'})


if __name__ == '__main__':
    main()
