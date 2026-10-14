import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
print('PIE:', M.app('IsPIERunning', {})[:80])
r = M.actor('find_actors', {'name': '', 'tag': '', 'collision_channels': [], 'class_name': ''})
try:
    actors = json.loads(r)['returnValue']
except Exception:
    actors = []
pawn = [a['refPath'] for a in actors if 'Character' in a.get('refPath','')]
print('pawns:', pawn)
