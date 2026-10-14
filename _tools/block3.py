import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
print('PIE:', M.app('IsPIERunning', {})[:80])
r = M.actor('find_actors', {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': '/Script/Engine.Character'}})
print('RAW:', r[:600])
