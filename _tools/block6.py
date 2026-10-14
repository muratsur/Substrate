import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
P='/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:PersistentLevel.BP_FirstPersonCharacter_C_0'
ACT=M.ACT; SCN=M.SCN

def act(name, args=None):
    return M.call('call_tool', {'toolset_name': ACT, 'tool_name': name, 'arguments': args or {}})
def scn(name, args=None):
    return M.call('call_tool', {'toolset_name': SCN, 'tool_name': name, 'arguments': args or {}})

def put(x, y, z):
    act('set_actor_transform', {'actor': {'refPath': P},
        'xform': {'location': {'x': float(x), 'y': float(y), 'z': float(z)}}})

def loc():
    v = json.loads(act('get_actor_transform', {'actor': {'refPath': P}}))['returnValue']['location']
    return (round(v['x']), round(v['y']), round(v['z']))

put(-5, 1398, 362); time.sleep(1.0)
print('start:', loc())
last_ok = None
for y in range(1400, 3200, 25):
    put(-5, y, 362)
    time.sleep(0.25)
    p = loc()
    if abs(p[1] - y) > 60:
        print('BLOCKED trying y=%d -> sat at %s' % (y, p))
        last_ok = y - 25
        break
    last_ok = y
    lastsat = p
print('last clear y:', last_ok)
