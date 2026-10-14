"""T1.4 terminal: place BP_Terminal in L_SectorC and capture the editor viewport.

Run:  python _tools/terminal_place.py place
      python _tools/terminal_place.py capture [from_x]   # -1 (behind) or 1 (in front)
"""
import sys, json, os
sys.path.insert(0, '_tools')
import mcpx as M

CLS = '/Game/Substrate/Core/BP_Terminal.BP_Terminal_C'
LOC = (-200.0, 1500.0, 430.0)  # near the route start; it re-parents to the camera at play
OUT = '_tools/capture'


def s(name, args):
    return M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': name, 'arguments': args})


def app(name, args):
    return M.call('call_tool', {'toolset_name': M.APP, 'tool_name': name, 'arguments': args})


def obj_props(ref, values):
    return M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties',
                                'arguments': {'instance': {'refPath': ref},
                                              'values': json.dumps(values)}})


def place():
    r = s('add_to_scene_from_class', {'actor_type': {'refPath': CLS}, 'name': 'Terminal_01',
                                      'xform': {'location': {'x': LOC[0], 'y': LOC[1], 'z': LOC[2]},
                                                'rotation': {'pitch': 0.0, 'yaw': 180.0, 'roll': 0.0}}})
    print('spawn:', r[:300])
    ref = json.loads(r)['returnValue']['refPath']
    s('set_actor_folder', {'actor': {'refPath': ref}, 'folder_path': 'Substrate/Terminal'})
    s('set_actor_label', {'actor': {'refPath': ref}, 'label': 'Terminal_01'})
    print('props:', obj_props(ref, {
        'UpOffset': {'x': 48.0, 'y': 10.0, 'z': -12.0},
        'StowOffset': {'x': 30.0, 'y': 4.0, 'z': -34.0}})[:200])
    r2 = M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform',
                              'arguments': {'actor': {'refPath': ref}}})
    print('xform:', r2[:300])
    print('saved:', s('save_actor', {'actor': {'refPath': ref}})[:200])
    return ref


def capture(kind='viewport', side=-1):
    """Capture the level viewport looking at the terminal."""
    # camera 260 uu to the side of the terminal, at its height, looking at it
    dist = 8.0 if os.environ.get('TERM_FAR') else 2.6
    cam = (LOC[0] + side * 260.0, LOC[1], LOC[2] + 5.0)
    yaw = 0.0 if side < 0 else 180.0
    if kind == 'viewport':
        print('cam:', app('SetCameraTransform', {
            'transform': {'location': {'x': cam[0], 'y': cam[1], 'z': cam[2]},
                          'rotation': {'pitch': 0.0, 'yaw': yaw, 'roll': 0.0}}})[:200])
        r = app('CaptureViewport', {})
    else:
        r = app('CaptureEditorImage', {})
    print('capture:', r[:500])
    os.makedirs(OUT, exist_ok=True)
    if r.strip().startswith('{'):
        d = json.loads(r).get('returnValue')
        if isinstance(d, dict):
            for k in ('image', 'path', 'filePath', 'data'):
                if k in d:
                    print('key', k, len(str(d[k])))
        else:
            print('plain:', str(d)[:200])


def main():
    M.init()
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'place'
    if cmd == 'place':
        place()
    elif cmd == 'capture':
        capture(sys.argv[2] if len(sys.argv) > 2 else 'viewport',
                float(sys.argv[3]) if len(sys.argv) > 3 else -1)


if __name__ == '__main__':
    main()
