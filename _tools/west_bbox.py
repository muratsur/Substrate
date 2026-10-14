import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
SCN = 'editor_toolset.toolsets.scene.SceneTools'
def bbox(minb, maxb, label):
    r = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'find_actors',
        'arguments': {'name': '', 'tag': '', 'collision_channels': [],
                      'bounds': {'min': {'x': minb[0], 'y': minb[1], 'z': minb[2]},
                                  'max': {'x': maxb[0], 'y': maxb[1], 'z': maxb[2]}}}})
    d = json.loads(r)['returnValue']
    print('%s: %d actors' % (label, len(d)))
    for a in d[:40]:
        print('  ', a['refPath'].split('.')[-1])
    return d
bbox((-19000, -2000, -1000), (-17000, 2000, 1000), 'x -19000..-17000')
bbox((-24000, -2000, -1000), (-23000, 2000, 1000), 'x -24000..-23000')
bbox((-25600, -2000, -1000), (-24800, 2000, 1000), 'x -25600..-24800')
bbox((-12500, -2000, -1000), (-11500, 2000, 1000), 'x -12500..-11500')
