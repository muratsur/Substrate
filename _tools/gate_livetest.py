"""West-gate live test: pre-place green light, wire temporary fill hook, run PIE
verify, tear down.

Subcommands:
  prep      spawn+tag WestGate_GreenLight, set hidden, save level
  add       TempFill fn (logs every fixture) + SetTimer hook, compile
  test      PIE: verify GateOpen, block hide, pawn teleport past gate, screenshot
  teardown  StopPIE, remove hook + TempFill, compile, save, restore maps to saved
"""
import sys
import json
import time
import os
import base64
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B

SCN = 'editor_toolset.toolsets.scene.SceneTools'
ACT = 'editor_toolset.toolsets.actor.ActorTools'
APP = 'EditorToolset.EditorAppToolset'
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
RM_C = RM + '_C'
EG = RM + ':EventGraph'
LEV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'

GREEN_LIGHT = 'WestGate_GreenLight'

TEMPFILL = '''(fn TempFill ()
  (bind fxs (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for f fxs
    (bind fx (Utilities|Casting|CastToBP_Fixture f))
    (Class|BPFixture|LogFixture fx :Result 1))
  (CallFunction|RefreshTerminal :self self)
  (CallFunction|OpenWestGate :self self))
'''


def pie():
    return 'true' in M.app('IsPIERunning', {})


def stop():
    if pie():
        M.app('StopPIE', {})
        time.sleep(6)
    print('PIE running:', pie())


def find_actors(cls, name_filter=''):
    args = {'name': name_filter, 'tag': '', 'collision_channels': [],
            'actor_type': {'refPath': cls}}
    r = json.loads(M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'find_actors',
                                        'arguments': args}))['returnValue']
    return [a['refPath'] for a in r]


def prop(ref, names):
    r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties',
                             'arguments': {'instance': {'refPath': ref},
                                           'properties': names}})
    try:
        return json.loads(r)['returnValue']
    except Exception:
        return r[:120]


def prep():
    stop()
    # spawn green light at the end cap
    r = M.call('call_tool', {'toolset_name': SCN, 'tool_name': 'add_to_scene_from_class',
                             'arguments': {'actor_type': {'refPath': '/Script/Engine.PointLight'},
                                           'name': GREEN_LIGHT,
                                           'xform': {'location': {'x': -25300.0, 'y': 700.0, 'z': 700.0}}}})
    print('spawn green:', r[:120])
    got = find_actors('/Script/Engine.PointLight', GREEN_LIGHT)
    print('found:', got)
    if not got:
        sys.exit('green light not found after spawn')
    ref = {'refPath': got[0]}
    print('tag:', M.call('call_tool', {'toolset_name': ACT, 'tool_name': 'add_tag',
                                       'arguments': {'actor': ref, 'tag': 'WestGateLightGreen'}})[:90])
    print('save:', M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                                        'arguments': {'asset_paths': ['/Game/Substrate/Maps/L_SectorC']}})[:80])


def info(refs):
    return json.loads(M.bp('get_node_infos', {'nodes': refs}))['returnValue']


def find_node(title):
    r = json.loads(M.bp('find_nodes', {'graph': {'refPath': EG}, 'title': title}))['returnValue']
    if r:
        return r
    print('  NOT FOUND:', title)
    return []


def pins(node, direction, type_id=None, name=None):
    infos = info([{'refPath': node}])[0]
    out = infos['input_pins' if direction == 'in' else 'output_pins']
    if type_id:
        out = [p for p in out if p['type_id'] == type_id]
    if name:
        out = [p for p in out if p['name'] == name]
    return out


def add_hook():
    stop()
    print('add fn:', M.bp('add_function_graph', {'blueprint': {'refPath': RM},
                                                 'graph_name': 'TempFill'})[:150])
    print('write:', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':TempFill'},
                                             'code': TEMPFILL})[:240])
    begin = find_node('Event BeginPlay')[0]['refPath']
    start = find_node('StartShift')[0]['refPath']
    timer = json.loads(M.bp('create_node', {'graph': {'refPath': EG},
                                            'type_id': 'Utilities|Time|SetTimerbyFunctionName',
                                            'pos': {'x': 200, 'y': 900}}))['returnValue']['refPath']
    b_then = pins(begin, 'out', 'Exec')[0]
    s_exec = pins(start, 'in', 'Exec')[0]
    t_exec = pins(timer, 'in', 'Exec')[0]
    t_then = pins(timer, 'out', 'Exec')[0]
    print('break:', M.bp('break_pins', {'output_pin': b_then['pin_id'],
                                        'input_pin': s_exec['pin_id']})[:80])
    print('bp->timer:', M.bp('connect_pins', {'output_pin': b_then['pin_id'],
                                              'input_pin': t_exec['pin_id']})[:80])
    print('timer->start:', M.bp('connect_pins', {'output_pin': t_then['pin_id'],
                                                 'input_pin': s_exec['pin_id']})[:80])
    for pname, val in (('FunctionName', 'TempFill'), ('Time', '2.0'), ('bLooping', 'true')):
        p = pins(timer, 'in', name=pname)
        if p:
            print('  pin', pname, M.bp('set_pin_value', {'pin': p[0]['pin_id'],
                                                         'value': val})[:70])
    print('compile:', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:150])
    print('save BP:', M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                                           'arguments': {'asset_paths': [RM]}})[:80])


def capture(pose, out):
    r = M.call('call_tool', {'toolset_name': APP, 'tool_name': 'CaptureViewport',
                             'arguments': {'captureTransform': pose, 'annotations': {}}})
    d = json.loads(r)['returnValue']
    img = d.get('image') or d
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'wb') as f:
        f.write(base64.b64decode(img['data']))
    print('captured', out, os.path.getsize(out), 'bytes')


def test():
    assert pie(), 'PIE must be running (call with the add step left live)'
    rms = find_actors(RM_C)
    print('RM instances:', rms)
    for ref in rms:
        print('  GateOpen:', prop(ref, ['GateOpen']), 'Remaining:',
              prop(ref, ['TerminalRemaining']))
    pawn = find_actors('/Script/Engine.Character')
    print('pawn:', pawn)
    if pawn:
        p = pawn[0]
        xf = json.loads(M.call('call_tool', {'toolset_name': ACT, 'tool_name': 'get_actor_transform',
                                             'arguments': {'actor': {'refPath': p}}}))['returnValue']
        print('pawn at:', xf.get('location'))
    gb = find_actors('/Script/Engine.PointLight', GREEN_LIGHT)
    print('green in PIE:', gb)
    if gb:
        print('  bHidden:', prop(gb[0], ['bHidden']), 'bVisible:', prop(gb[0], ['bVisible']),
              'intensity:', str(prop(gb[0], ['Intensity']))[:60])
    # screenshot from near the old blockade looking at the cap
    capture({'location': {'x': -24600.0, 'y': 700.0, 'z': 420.0},
             'rotation': {'pitch': -10.0, 'yaw': 180.0, 'roll': 0.0}},
            '_tools/shots/gate_open_view.png')


def teardown():
    stop()
    timer = find_node('Set Timer by Function Name')
    for n in timer:
        M.bp('delete_node', {'node': {'refPath': n['refPath']}})
    print('timer nodes removed:', len(timer))
    begin = find_node('Event BeginPlay')[0]['refPath']
    start = find_node('StartShift')[0]['refPath']
    b_then = pins(begin, 'out', 'Exec')[0]
    s_exec = pins(start, 'in', 'Exec')[0]
    print('reconnect:', M.bp('connect_pins', {'output_pin': b_then['pin_id'],
                                              'input_pin': s_exec['pin_id']})[:80])
    print('rm fn:', M.bp('remove_function_graph', {'blueprint': {'refPath': RM},
                                                  'graph_name': 'TempFill'})[:120])
    print('compile:', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:150])
    print('save:', M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                                        'arguments': {'asset_paths': [RM, '/Game/Substrate/Maps/L_SectorC']}})[:80])


if __name__ == '__main__':
    M.init()
    step = sys.argv[1] if len(sys.argv) > 1 else 'add'
    {'prep': prep, 'add': add_hook, 'test': test, 'teardown': teardown}[step]()
