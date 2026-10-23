"""Launch any game command line (uncooked -game or packaged), screenshot spawn and a short walk. Kills only its own process."""
import subprocess, time, ctypes, sys
from ctypes import wintypes
from pathlib import Path
from PIL import ImageGrab
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
WAIT = float(sys.argv[2]); CMD = sys.argv[3:]
u = ctypes.windll.user32
proc = subprocess.Popen(CMD)
time.sleep(WAIT)
hw = []
def cb(h, _):
    if u.IsWindowVisible(h):
        pid = wintypes.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(pid))
        n = u.GetWindowTextLengthW(h); b = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(h, b, n + 1)
        if 'Substrate' in b.value and 'Unreal Editor' not in b.value: hw.append((h, b.value))
    return True
u.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(cb), 0)
print('windows', hw)
h = hw[-1][0]; u.SetForegroundWindow(h); time.sleep(1)
def shot(name):
    r = wintypes.RECT(); u.GetWindowRect(h, ctypes.byref(r)); ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom)).save(OUT / f'{name}.png')
def hold(vk, s):
    u.keybd_event(vk, 0, 0, 0); time.sleep(s); u.keybd_event(vk, 0, 2, 0); time.sleep(0.7)
shot('00_spawn')
for name, vk, s in (('01_W', 0x57, 1.2), ('02_D', 0x44, 1.5), ('03_A', 0x41, 2.5)):
    hold(vk, s); shot(name)
proc.kill()
