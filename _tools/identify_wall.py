import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
SCN = 'editor_toolset.toolsets.scene.SceneTools'

def find(cls):
    r = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'find_actors',
        'arguments': {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': cls}}})
    try: return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception: return []

def bounds(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}})
    return json.loads(r)['returnValue']

def raw_bounds(ref):
    return M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}})

M.init()
target = (-1604.0, 8449.0)
TARGETS = [(-1604, 8449), (-2600, 8449)]
print('raw bounds sample:', raw_bounds(find('/Script/Engine.StaticMeshActor')[0])[:300], '\n')
for cls in ('/Script/Engine.StaticMeshActor', '/Script/Engine.BlockingVolume'):
    refs = find(cls)
    print('%s: %d actors' % (cls.split('.')[-1], len(refs)))
    cands = []
    for ref in refs:
        try:
            b = bounds(ref)
        except Exception:
            continue
        # handle either {origin,extent} or {min,max} style
        if 'origin' in b and isinstance(b['origin'], dict):
            o, ex = b['origin'], b.get('extent', {})
            lo = (o['x'] - ex['x'], o['y'] - ex['y'], o['z'] - ex['z'])
            hi = (o['x'] + ex['x'], o['y'] + ex['y'], o['z'] + ex['z'])
            ctr = (o['x'], o['y'], o['z'])
        elif 'Min' in b and isinstance(b['Min'], dict):
            lo = (b['Min']['x'], b['Min']['y'], b['Min']['z'])
            hi = (b['Max']['x'], b['Max']['y'], b['Max']['z'])
            ctr = ((lo[0]+hi[0])/2, (lo[1]+hi[1])/2, (lo[2]+hi[2])/2)
        else:
            continue
        for (tx, ty) in TARGETS:
            if lo[0] <= tx <= hi[0] and lo[1] - 80 <= ty <= hi[1] + 80:
                cands.append((ref, ctr, lo, hi))
    for ref, ctr, lo, hi in sorted(cands):
        print('  %-52s box x[%-.0f..%.0f] y[%-.0f..%.0f] z[%-.0f..%.0f]' %
              (ref.split(':')[-1], lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
