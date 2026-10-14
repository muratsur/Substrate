import sys, json, math
sys.path.insert(0, '_tools')
import mcpx as M

EA = 'EditorToolset.EditorAppToolset'
AT = 'editor_toolset.toolsets.actor.ActorTools'
SCN = 'editor_toolset.toolsets.scene.SceneTools'

def ray(orig, yaw, pitch=0.0):
    M.app('SetCameraTransform', {'transform': {'location': {'x': orig[0], 'y': orig[1], 'z': orig[2]},
        'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': 0.0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}})
    r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'ScreenCoordsToWorld',
                             'arguments': {'coords': {'x': 0.5, 'y': 0.5}}})
    try: return json.loads(r)['returnValue']
    except Exception: return None

def find(cls):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
        'arguments': {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': cls}}})
    try: return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception: return []

def bounds(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds',
                             'arguments': {'actor': {'refPath': ref}}})
    return json.loads(r)['returnValue']

M.init()
Y = 8449.0
# 1) low-height west scans from just east of the player, below eye height
for z in (180.0, 260.0, 310.0, 360.0, 400.0, 430.0, 500.0, 650.0):
    h = ray((-1480.0, Y, z), 180.0)
    if h:
        print('west z=%5.0f -> hit x=%-8.0f (dist %.0f)' % (z, h['x'], abs(h['x'] + 1480)))
    else:
        print('west z=%5.0f -> no hit' % z)

# 2) identify actors whose bounds contain the x=-2600 plane near y=8449
print('\n=== actors near the x=-2600 hit ===')
target = (-2600.0, Y, 430.0)
cands = set()
for cls in ('/Script/Engine.StaticMeshActor', '/Script/Engine.BlockingVolume',
            '/Script/Engine.Brush', '/Script/Engine.LevelScriptActor'):
    for ref in find(cls):
        try: b = bounds(ref)
        except Exception: continue
        o = b.get('origin') or b.get('Origin') or b
        ex = b.get('extent') or b.get('Extent') or b
        if not isinstance(o, dict): continue
        lo = (o['x'] - ex['x'], o['y'] - ex['y'], o['z'] - ex['z'])
        hi = (o['x'] + ex['x'], o['y'] + ex['y'], o['z'] + ex['z'])
        if lo[0] <= target[0] <= hi[0] and lo[1] - 50 <= target[1] <= hi[1] + 50 and lo[2] <= target[2] <= hi[2] + 200:
            cands.add(ref)
for ref in sorted(cands):
    b = bounds(ref)
    o, ex = b['origin'] if 'origin' in b else b.get('Origin'), b.get('extent') or b.get('Extent')
    print('  %-50s center=(%.0f,%.0f,%.0f) extent=(%.0f,%.0f,%.0f)' % (
        ref.split(':')[-1], o['x'], o['y'], o['z'], ex['x'], ex['y'], ex['z']))
if not cands:
    print('  (none matched)')
