import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
ACT=M.ACT; SCN=M.SCN
def act(n,a=None): return M.call('call_tool', {'toolset_name':ACT,'tool_name':n,'arguments':a or {}})

# find pawn
r = json.loads(scn_r(M) if False else '') if False else None
def scn(n,a=None): return M.call('call_tool', {'toolset_name':SCN,'tool_name':n,'arguments':a or {}})
chars = json.loads(scn('find_actors', {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': '/Script/Engine.Character'}}))['returnValue']
P = chars[0]['refPath']
def put(x,y,z):
    act('set_actor_transform', {'actor': {'refPath': P}, 'xform': {'location': {'x':float(x),'y':float(y),'z':float(z)}}})
def loc():
    v = json.loads(act('get_actor_transform', {'actor': {'refPath': P}}))['returnValue']['location']
    return (round(v['x']),round(v['y']),round(v['z']))

put(-1534, 8409, 362); time.sleep(1.0)
print('start:', loc())
blocked_at = None
for x in range(-1550, -2000, -25):
    put(x, 8409, 362); time.sleep(0.25)
    p = loc()
    if abs(p[0] - x) > 60:
        print('BLOCKED at x=%d -> sat %s' % (x, p)); blocked_at = x; break
if not blocked_at:
    print('west seam clear all the way to x=-1975')
