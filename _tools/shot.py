"""Capture the level viewport from a given pose to a PNG.

Run:  python _tools/shot.py out.png X Y Z pitch yaw
      python _tools/shot.py shots/canal_end.png -1700 8300 1500 -35 90
"""
import sys
import json
import base64
import os
sys.path.insert(0, '_tools')
import mcpx as M

EA = 'EditorToolset.EditorAppToolset'


def shot(path, x, y, z, pitch, yaw):
    pose = {'location': {'x': x, 'y': y, 'z': z},
            'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': 0}}
    r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'CaptureViewport',
                             'arguments': {'captureTransform': pose, 'annotations': {}}})
    d = json.loads(r)['returnValue']
    img = d.get('image') or d
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'wb') as f:
        f.write(base64.b64decode(img['data']))
    print('wrote', path, os.path.getsize(path), 'bytes')


if __name__ == '__main__':
    M.init()
    a = sys.argv[1:]
    shot(a[0], *[float(v) for v in a[1:6]])
