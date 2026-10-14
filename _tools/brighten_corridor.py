"""Brighten the Sector D corridor lights in the editor level (not PIE).

Run:  python -u _tools/brighten_corridor.py
Reads each value back after writing so the result is checked, not assumed.
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
LEVEL = '/Game/Substrate/Maps/L_SectorC.L_SectorC'
# light actor -> new intensity
TARGETS = {
    'PointLight_16': 900,
    'PointLight_15': 900,
    'RectLight_23': 40,
}


def light_component(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_components',
                             'arguments': {'actor': {'refPath': ref}}})
    for c in json.loads(r).get('returnValue', []):
        if 'LightComponent' in c['refPath']:
            return c['refPath']
    return None


def get_intensity(comp):
    r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties',
                             'arguments': {'instance': {'refPath': comp}, 'properties': ['Intensity']}})
    v = json.loads(r)['returnValue']
    d = json.loads(v) if isinstance(v, str) else v
    return d.get('Intensity')


def set_intensity(comp, value):
    return M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties',
                                'arguments': {'instance': {'refPath': comp},
                                              'values': json.dumps({'Intensity': value})}})


M.init()
for name, value in TARGETS.items():
    actor = '%s:PersistentLevel.%s' % (LEVEL, name)
    comp = light_component(actor)
    if not comp:
        print('NO COMPONENT for', name)
        continue
    before = get_intensity(comp)
    print(name, 'before', before, '-> setting', value)
    print('  set:', set_intensity(comp, value)[:120])
    print('  after', get_intensity(comp))
