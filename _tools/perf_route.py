"""Frame-time survey of the route in a Development build: for each spot, launch the game teleported there (BugItGo) with
the CSV profiler capturing FRAMES frames, keep the last 300 (post-load steady state) and summarize. Captures only the game
window (PrintWindow) when --shot is given. Kills only its own process.
Usage: python _tools/perf_route.py <DevPerf build dir> [spot ...] [--shot]"""
import sys, os, time, glob, csv, json, subprocess, ctypes, statistics
from ctypes import wintypes
BUILD = sys.argv[1]
EXE = os.path.join(BUILD, 'Substrate', 'Binaries', 'Win64', 'Substrate.exe')
CSVDIR = os.path.join(BUILD, 'Substrate', 'Saved', 'Profiling', 'CSV')
OUT = os.path.join('_evidence', 'perf' + ('_1440' if '--1440' in sys.argv else ''))
os.makedirs(OUT, exist_ok=True)
SPOTS = {  # name: (x, y, z, yaw) - z = floor + 100
    'dock_spawn': (0, 1400, 360, 90), 'west_corridor': (-6000, 100, 360, 180), 'canal_arch': (-1848, 6802, 387, 90),
    'east_bank': (2704, 7797, 293, 180), 'transit_B': (8560, 3250, 402, 90), 'sector_D': (-660, -8500, 390, 90)}
RES = (2560, 1440) if '--1440' in sys.argv else (1920, 1080)
FRAMES = 1800   # ~15 s at 110 fps; the last 300 are kept
want = [a for a in sys.argv[2:] if not a.startswith('--')] or list(SPOTS)
u = ctypes.windll.user32; g = ctypes.windll.gdi32
def window_of(pid):
    found = []
    def cb(h, _):
        p = wintypes.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid and u.IsWindowVisible(h): found.append(h)
        return True
    u.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(cb), 0)
    return found[0] if found else None
def shot(h, path):
    from PIL import Image
    r = wintypes.RECT(); u.GetClientRect(h, ctypes.byref(r)); w, hh = r.right, r.bottom
    dc = u.GetDC(h); mdc = g.CreateCompatibleDC(dc); bmp = g.CreateCompatibleBitmap(dc, w, hh); g.SelectObject(mdc, bmp)
    u.PrintWindow(h, mdc, 3)  # PW_CLIENTONLY | PW_RENDERFULLCONTENT: this window only
    buf = ctypes.create_string_buffer(w * hh * 4)
    class BIH(ctypes.Structure):
        _fields_ = [('biSize', wintypes.DWORD), ('biWidth', ctypes.c_long), ('biHeight', ctypes.c_long), ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD),
                    ('biCompression', wintypes.DWORD), ('biSizeImage', wintypes.DWORD), ('a', ctypes.c_long), ('b', ctypes.c_long), ('c', wintypes.DWORD), ('d', wintypes.DWORD)]
    bi = BIH(ctypes.sizeof(BIH), w, -hh, 1, 32, 0, 0, 0, 0, 0, 0)
    g.GetDIBits(mdc, bmp, 0, hh, buf, ctypes.byref(bi), 0)
    Image.frombuffer('RGBA', (w, hh), buf, 'raw', 'BGRA', 0, 1).convert('RGB').save(path)
    g.DeleteObject(bmp); g.DeleteDC(mdc); u.ReleaseDC(h, dc)
csv.field_size_limit(1 << 30)   # the CSV profiler appends one huge metadata row
results = {}
def analyse(path, keep=300):
    """Rows grow as the profiler adds stats, and the CSV ends with a repeated header plus a metadata row: use the last
    header's column positions and the last `keep` numeric rows."""
    with open(path, newline='') as fh:
        rows = list(csv.reader(fh))
    heads = [i for i, r in enumerate(rows) if 'FrameTime' in r]
    head = rows[heads[-1]]
    def num(r, key):
        i = head.index(key)
        try: return float(r[i])
        except (IndexError, ValueError): return None
    data = [r for r in rows[1:heads[-1]] if num(r, 'FrameTime') is not None][-keep:]
    col = lambda key: [v for v in (num(r, key) for r in data) if v is not None] if key in head else []
    ft, gt, rt, gpu, rhi = col('FrameTime'), col('GameThreadTime'), col('RenderThreadTime'), col('GPUTime'), col('RHIThreadTime')
    q = lambda v, pc: round(sorted(v)[max(0, int(len(v) * pc) - 1)], 2)
    m = lambda v: round(statistics.mean(v), 2) if v else None
    return {'avg_ms': m(ft), 'p95_ms': q(ft, .95), 'max_ms': round(max(ft), 2), 'fps': round(1000 / statistics.mean(ft), 1),
            'game_ms': m(gt), 'render_ms': m(rt), 'rhi_ms': m(rhi), 'gpu_ms': m(gpu), 'frames': len(ft), 'csv': os.path.basename(path)}
def done(f):
    try:
        with open(f, 'rb') as fh: tail = fh.read()[-400000:].lower()
    except PermissionError:   # still being written
        return False
    return any(k in tail for k in (b'[commandline]', b'[platform]'))
for name in want:
    x, y, z, yaw = SPOTS[name]
    before = set(glob.glob(os.path.join(CSVDIR, '*.csv')))
    cmds = f'EnableCheats, r.VSync 0, t.MaxFPS 0, BugItGo {x} {y} {z} 0 {yaw} 0' + (', showdebug' if '--shot' in sys.argv else '')
    p = subprocess.Popen([EXE, '-windowed', f'-ResX={RES[0]}', f'-ResY={RES[1]}', f'-csvCaptureFrames={FRAMES}', f'-ExecCmds={cmds}'])
    new, t0 = [], time.time()
    try:
        while time.time() - t0 < 150 and not new:
            time.sleep(2)
            if '--shot' in sys.argv and time.time() - t0 > 12 and not os.path.exists(os.path.join(OUT, name + '.png')):
                h = window_of(p.pid)
                if h: shot(h, os.path.join(OUT, name + '.png'))
            # the profiler streams rows while recording; the capture is complete once its metadata row ('[...]') is written
            new = [f for f in set(glob.glob(os.path.join(CSVDIR, '*.csv'))) - before if done(f)]
    finally:
        p.kill(); p.wait()   # only our own process, even if something above fails
    if not new: print(name, 'no CSV written'); continue
    results[name] = analyse(new[0])
    print(name, results[name], flush=True)
json.dump(results, open(os.path.join(OUT, 'route_perf.json'), 'w'), indent=1)
