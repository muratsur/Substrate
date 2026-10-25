"""While PIE runs, sample the player position ~5x/s; when it jumps to the spawn point, print the last positions before the jump.
Usage: python _tools/watch_teleports.py [seconds]"""
import sys, json, time, collections, math
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 600
hist = collections.deque(maxlen=25)
pawn = None
end = time.time() + DURATION
while time.time() < end:
    try:
        if pawn is None:
            r = json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': '/Script/Engine.Character'}}}))['returnValue']
            pawn = r[0]['refPath'] if r else None
            if pawn is None: time.sleep(1); continue
        l = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': pawn}}}))['returnValue']['location']
    except Exception:
        pawn = None; time.sleep(1); continue
    p = (round(l['x']), round(l['y']), round(l['z']), time.strftime('%H:%M:%S'))
    if hist and math.dist(hist[-1][:2], (0, 1400)) > 300 and math.dist(p[:2], (0, 1400)) < 5:
        print('TELEPORT at', p[3], 'last positions (x, y, z; feet = z-96):', flush=True)
        for h in list(hist)[-12:]: print('   ', h, flush=True)
    hist.append(p)
    time.sleep(0.2)
print('watch ended', flush=True)
