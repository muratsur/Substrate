"""Re-apply the keyboard movement wiring (+ terminal screen size), compile, save, and prove it landed on disk."""
import os
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

M.init()

CHAR = '/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter.BP_FirstPersonCharacter'
G = CHAR + ':EventGraph'
BPTOOL = M.BP
EYE = '/Game/Substrate/Core/BP_Terminal.BP_Terminal_C:Screen_GEN_VARIABLE'
TERM_SCREEN = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.BP_Terminal_C_0.Screen'
FILES = {
    'char BP': 'Content/FirstPerson/Blueprints/BP_FirstPersonCharacter.uasset',
    'terminal BP': 'Content/Substrate/Core/BP_Terminal.uasset',
    'level': 'Content/Substrate/Maps/L_SectorC.umap',
}


def pin(node, direction, index):
    return {'direction': direction, 'index_id': index, 'node': {'refPath': G + '.' + node}}


def links(node):
    r = M.bp('get_connected_subgraph', {'node': {'refPath': G + '.' + node}})
    try:
        d = json.loads(r)['returnValue'][0]
    except Exception:
        return 'ERR ' + r[:90]
    out = []
    for p in d.get('input_pins', []) + d.get('output_pins', []):
        tgt = [c['node']['refPath'].split('.')[-1].replace('K2Node_', '') for c in (p.get('connected_pins') or [])]
        if tgt:
            out.append(p['name'] + '->' + ','.join(tgt))
    return out


def connect(onode, oidx, inode, iidx):
    return M.bp('connect_pins', {'output_pin': pin(onode, 'EGPD_Output', oidx),
                                 'input_pin': pin(inode, 'EGPD_Input', iidx)})[:60]


print('=== before')
print('  IA_Move :', links('K2Node_EnhancedInputAction_3'))
print('  Move    :', links('K2Node_CallFunction_5'))

print('=== wiring')
print('  exec   :', connect('K2Node_EnhancedInputAction_3', 0, 'K2Node_CallFunction_5', 0))
print('  x axis :', connect('K2Node_EnhancedInputAction_3', 5, 'K2Node_CallFunction_5', 2))
print('  y axis :', connect('K2Node_EnhancedInputAction_3', 6, 'K2Node_CallFunction_5', 3))
print('  jump   :', connect('K2Node_EnhancedInputAction_5', 0, 'K2Node_CallFunction_1193', 0))
print('  stopjmp:', connect('K2Node_EnhancedInputAction_5', 4, 'K2Node_CallFunction_9386', 0))

print('=== after')
print('  IA_Move :', links('K2Node_EnhancedInputAction_3'))
print('  Move    :', links('K2Node_CallFunction_5'))
print('  compile :', M.bp('compile_blueprint', {'blueprint': {'refPath': CHAR}})[:150])

print('=== terminal screen sizes')
def setp(ref, vals):
    return M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties',
                                'arguments': {'instance': {'refPath': ref},
                                              'values': json.dumps(vals)}})[:60]
def getp(ref):
    return M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties',
                                'arguments': {'instance': {'refPath': ref},
                                              'properties': ['DrawSize']}})[:120]
print('  template set x/y:', setp(EYE, {'DrawSize': {'x': 30}}), setp(EYE, {'DrawSize': {'y': 22}}))
print('  template now   :', getp(EYE))
print('  placed now     :', getp(TERM_SCREEN))

print('=== saving')
for p in ('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter',
          '/Game/Substrate/Core/BP_Terminal',
          '/Game/Substrate/Maps/L_SectorC'):
    print('  ', p, M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                                        'arguments': {'asset_paths': [p]}})[:80])

print('=== disk mtimes')
for k, f in FILES.items():
    print('  %-12s %s' % (k, __import__('time').strftime('%m-%d %H:%M:%S', __import__('time').localtime(os.path.getmtime(f)))))
