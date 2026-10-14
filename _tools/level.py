"""Inspect L_SectorC actors: fixtures, lights, growth nodes."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

SCN = M.SCN
MAP = 'L_SectorC'


def find(name='', tag='', actor_type=None):
    args = {'name': name, 'tag': tag, 'collision_channels': []}
    if actor_type:
        args['actor_type'] = {'refPath': actor_type}
    r = json.loads(M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'find_actors',
                                        'arguments': args}))['returnValue']
    return [a['refPath'] for a in r]


def props(ref, keys):
    r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties',
                             'arguments': {'instance': {'refPath': ref}, 'properties': keys}})
    try:
        return json.loads(json.loads(r)['returnValue'])
    except Exception:
        return r[:200]


def dump(label, refs, keys):
    print('==', label, len(refs))
    for r in refs:
        short = r.replace('/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.', '')
        print('  ', short, props(r, keys))


if __name__ == '__main__':
    M.init()
    dump('fixtures', find('Fixture'), ['fixtureID', 'rowOrder'])
    dump('growth', find('Growth'), ['stageIndex'])
    dump('lights-named', find('Light'), ['intensity', 'relativeLocation'])
    dump('pointlights', find(actor_type='/Script/Engine.PointLight'), ['intensity'])
    dump('spotlights', find(actor_type='/Script/Engine.SpotLight'), ['intensity'])
