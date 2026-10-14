"""Add dim shadowless fill lights along the Sector D corridor (editor level).

Run:  python -u _tools/add_corridor_fill.py
Reads each light back after setting it so the result is checked.
"""
import sys
import json
import time
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
SCN = M.SCN
OBJ = M.OBJ
LEVEL = '/Game/Substrate/Maps/L_SectorC.L_SectorC'
FILL_Y = 7050.0
FILL_Z = 600.0
FILL_X = [-700.0, -1100.0, -1500.0, -1900.0]
INTENSITY = 120.0
RADIUS = 1500.0


def light_component(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_components',
                             'arguments': {'actor': {'refPath': ref}}})
    for c in json.loads(r).get('returnValue', []):
        if 'LightComponent' in c['refPath']:
            return c['refPath']
    return None


def set_props(comp, values):
    return M.call('call_tool', {'toolset_name': OBJ, 'tool_name': 'set_properties',
                                'arguments': {'instance': {'refPath': comp},
                                              'values': json.dumps(values)}})


def get_props(comp, keys):
    r = M.call('call_tool', {'toolset_name': OBJ, 'tool_name': 'get_properties',
                             'arguments': {'instance': {'refPath': comp}, 'properties': keys}})
    v = json.loads(r)['returnValue']
    return json.loads(v) if isinstance(v, str) else v


M.init()
for i, x in enumerate(FILL_X):
    name = 'CorridorFill_%02d' % i
    r = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'add_to_scene_from_class',
                             'arguments': {'actor_type': {'refPath': '/Script/Engine.PointLight'},
                                           'name': name,
                                           'xform': {'location': {'x': x, 'y': FILL_Y, 'z': FILL_Z}}}})
    print(name, 'spawn:', r[:120])
    # the engine assigns its own name; use the refPath it returns
    actor = json.loads(r)['returnValue']['refPath']
    time.sleep(0.5)
    comp = light_component(actor)
    if not comp:
        print('  NO LIGHT COMPONENT for', name)
        continue
    set_props(comp, {'Intensity': INTENSITY, 'AttenuationRadius': RADIUS, 'CastShadows': False})
    back = get_props(comp, ['Intensity', 'AttenuationRadius', 'CastShadows'])
    print('  read back:', back)
