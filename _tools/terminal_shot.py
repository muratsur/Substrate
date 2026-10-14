"""T1.4 terminal: capture the whole editor (PIE window included) to a PNG.

Run:  python _tools/terminal_shot.py <name>
"""
import sys, json, base64, os
sys.path.insert(0, '_tools')
import mcpx as M

OUT = '_tools/capture'


def main():
    M.init()
    name = sys.argv[1] if len(sys.argv) > 1 else 'pie'
    r = M.call('call_tool', {'toolset_name': M.APP, 'tool_name': 'CaptureEditorImage',
                             'arguments': {}})
    if not r.strip().startswith('{'):
        print('ERR', r[:400]); return
    d = json.loads(r)['returnValue']
    data = d.get('data') or ''
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + '.png')
    if data:
        with open(path, 'wb') as f:
            f.write(base64.b64decode(data))
        print('wrote', path, os.path.getsize(path), 'bytes', d.get('mimeType'),
              d.get('width'), d.get('height'))
    else:
        print('no data; keys:', list(d.keys()))


if __name__ == '__main__':
    main()
