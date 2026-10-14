import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
M.init()
LEV = '/Game/Substrate/Maps/UEDPIE_0_L_SectorC.L_SectorC:'
args = {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': ''},
        'bound': {'center': {'x': -1550.0, 'y': 8409.0, 'z': 350.0},
                  'extent': {'x': 250.0, 'y': 600.0, 'z': 300.0}}}
r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': args})
refs = [a['refPath'].split(':')[-1] for a in json.loads(r).get('returnValue', [])]
print('%d actors in the seam box' % len(refs))
crossers = []
for short in refs:
    if short in ('WorldSettings',):
        continue
    ref = LEV + 'PersistentLevel.' + short
    try:
        b = json.loads(M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']
    except Exception:
        continue
    mn, mx = b.get('min'), b.get('max')
    if not (isinstance(mn, dict) and isinstance(mx, dict)):
        continue
    if mn['x'] - 40 <= -1604 <= mx['x'] + 40 and mn['z'] < 460 and mx['z'] > 250:
        crossers.append((short, mn, mx))
print('crossing x=-1604 at capsule heights:')
for short, mn, mx in crossers:
    print('  %-52s x[%7.0f..%7.0f] y[%7.0f..%7.0f] z[%7.0f..%7.0f]' % (
        short, mn['x'], mx['x'], mn['y'], mx['y'], mn['z'], mx['z']))
