"""Poll the PIE pawn every 0.5s; log position + detect the rescue teleport."""
import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
import gate_livetest as G

OUT = '_tools/shots/fall_trace.csv'
M.init()
pawn = G.find_actors('/Script/Engine.Character')[0]
last = None
t0 = time.time()
print('tracing', pawn, 'for 180s ->', OUT)
with open(OUT, 'w') as f:
    f.write('t,x,y,z,event\n')
    while time.time() - t0 < 180:
        try:
            tf = json.loads(M.call('call_tool', {'toolset_name': G.ACT, 'tool_name': 'get_actor_transform',
                'arguments': {'actor': {'refPath': pawn}}}))['returnValue']
            l = tf.get('location', {})
            x, y, z = l.get('x',0), l.get('y',0), l.get('z',0)
            evt = ''
            if last and (abs(x-last[0]) > 3000 or abs(y-last[1]) > 3000):
                evt = 'TELEPORT from %.0f,%.0f,%.0f' % last
                print('%.1fs TELEPORT -> %.0f,%.0f,%.0f (was %.0f,%.0f,%.0f)' % (
                    time.time()-t0, x, y, z, *last))
            f.write('%.1f,%.0f,%.0f,%.0f,%s\n' % (time.time()-t0, x, y, z, evt))
            f.flush()
            last = (x, y, z)
        except Exception as e:
            print('poll err', str(e)[:60])
        time.sleep(0.5)
print('trace complete')
