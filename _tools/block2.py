import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
if 'true' not in M.app('IsPIERunning', {}):
    M.app('StartPIE', {'options': {'bSimulate': False}})
    time.sleep(14)
r = M.actor('find_actors', {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': '/Script/Engine.Character'}})
print(json.loads(r)['returnValue'])
