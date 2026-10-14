import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
def scn(n,a=None): return M.call('call_tool', {'toolset_name':M.SCN,'tool_name':n,'arguments':a or {}})

def trace(x1,y1,z1, x2,y2,z2):
    r = json.loads(scn('trace_world', {'start': {'x':x1,'y':y1,'z':z1}, 'end': {'x':x2,'y':y2,'z':z2}}))['returnValue']
    return r   # distance or None

print('--- downward trace from z=900 at x=-5, various y ---')
for y in range(1200, 3200, 100):
    d = trace(-5, y, 900, -5, y, -400)
    if d is None:
        print('y=%5d  NO FLOOR (gap in ground)' % y)
    else:
        z = 900 - d
        print('y=%5d  floor z=%.0f' % (y, z))
