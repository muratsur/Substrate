import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
def scn(n,a=None): return M.call('call_tool', {'toolset_name':M.SCN,'tool_name':n,'arguments':a or {}})
def trace(x1,y1,z1, x2,y2,z2):
    r = json.loads(scn('trace_world', {'start': {'x':x1,'y':y1,'z':z1}, 'end': {'x':x2,'y':y2,'z':z2}}))['returnValue']
    return r
print('--- floor grid (z from 900 down to -400): F=floor at z shown, .=NO FLOOR ---')
xs = [-1500, -1000, -500, -5, 300, 700, 1000, 1400, 1800]
ys = list(range(1000, 12001, 500))
print('%9s' % 'x\y', ''.join('%5d' % y for y in ys))
for x in xs:
    row = '%9d' % x
    for y in ys:
        d = trace(x, y, 900, x, y, -400)
        if d is None:
            row += '    .'
        else:
            z = 900 - d
            row += ('%5.0f' % z) if z > 20 else '    ~'    # ~ = water/very low
    print(row)
print()
print('--- exact north edge of ground at x=-5 (25u steps, y 1700..1850):')

for x in (-5, 300, 700, 1000):
    edge = None
    for y in range(1500, 2100, 25):
        d = trace(x, y, 900, x, y, -400)
        if d is None:
            edge = y; break
    print('x=%5d ground edge at y=%s' % (x, edge))
