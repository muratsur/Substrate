"""Make the airlock gate usable: the fixture logging keys E (PASS) / Q (FLAG) must fire.

BP_RoundManager's BeginPlay calls EnableInput with an EMPTY PlayerController pin, so player
input never reaches the actor and the E/Q key events can never fire.  BP_Airlock only transits
when GateOK is true, and GateOpen() sets GateOK true only when every fixture in the gate's row
range is logged correctly - so a dead E/Q means the gate can never open.

Fixes:
  1. EnableInput.PlayerController  <-  GetPlayerController(0)
  2. E -> LogLookedAtFixture(Result = 1 = PASS), Q -> LogLookedAtFixture(Result = 2 = FLAG)

Run:  python _tools/fix_airlock_gate.py
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
EG = {'refPath': RM + ':EventGraph'}


def all_nodes():
    refs = json.loads(M.bp('find_nodes', {'graph': EG, 'title': ''}))['returnValue']
    out = []
    for i in range(0, len(refs), 25):
        out += json.loads(M.bp('get_node_infos', {'nodes': refs[i:i + 25]}))['returnValue']
    for n in out:                       # get_node_infos nests the ref under 'node'
        n['refPath'] = n.get('refPath') or n['node']['refPath']
    return out


def pin(d, name, direction=None):
    for p in d.get('input_pins', []) + d.get('output_pins', []):
        if p['name'] == name and (direction is None or p.get('direction') == direction):
            return p
    return None


def conn_names(p):
    return [c['node']['refPath'].split('.')[-1] for c in (p.get('connected_pins') or [])]


M.init()
print('PIE:', M.app('IsPIERunning', {})[:40])
nodes = all_nodes()
by_type = {}
for n in nodes:
    by_type.setdefault(n.get('type_id'), []).append(n)

enable = by_type.get('Input|EnableInput', [None])[0]
if enable is None:
    sys.exit('EnableInput node not found; types present: %s' % sorted(by_type))
pc = pin(enable, 'PlayerController')
print('EnableInput (%s).PlayerController <- %s' % (enable['refPath'].split('.')[-1], conn_names(pc) or 'NOTHING'))

if not (pc.get('connected_pins') or []):
    created = json.loads(M.bp('create_node', {'graph': EG, 'type_id': 'Game|GetPlayerController',
                                              'pos': {'x': -600, 'y': 620}}))['returnValue']['refPath']
    gd = json.loads(M.bp('get_node_infos', {'nodes': [{'refPath': created}]}))['returnValue'][0]
    outs = gd.get('output_pins', [])
    print('  new node %s outputs=%s' % (created.split('.')[-1], [p['name'] for p in outs]))
    print('  connect ->', M.bp('connect_pins', {'output_pin': outs[0]['pin_id'],
                                                'input_pin': pc['pin_id']})[:70])

for key, want in (('E', 1), ('Q', 2)):
    kn = by_type.get('Input|KeyboardEvents|' + key, [None])[0]
    if kn is None:
        print('key %s: no node found' % key)
        continue
    callers = conn_names(pin(kn, 'Pressed'))
    print('key %s (%s) Pressed -> %s   [want Result=%d]' % (key, kn['refPath'].split('.')[-1], callers, want))
    for c in (pin(kn, 'Pressed').get('connected_pins') or []):
        ref = c['node']['refPath']
        cd = json.loads(M.bp('get_node_infos', {'nodes': [{'refPath': ref}]}))['returnValue'][0]
        rp = pin(cd, 'Result')
        if rp is None:
            print('   %s (%s) has no Result pin' % (ref.split('.')[-1], cd.get('type_id')))
            continue
        print('   %s Result before: %s' % (ref.split('.')[-1], str(M.bp('get_pin_value', {'pin': rp['pin_id']}))[:50]))
        M.bp('set_pin_value', {'pin': rp['pin_id'], 'value': str(want)})
        print('   %s Result after : %s' % (ref.split('.')[-1], str(M.bp('get_pin_value', {'pin': rp['pin_id']}))[:50]))

print('compile:', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:200])
print('save   :', M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                                       'arguments': {'asset_paths': [RM]}})[:80])

print('=== after ===')
nodes = all_nodes()
enable = next(n for n in nodes if n.get('type_id') == 'Input|EnableInput')
print('EnableInput.PlayerController <-', conn_names(pin(enable, 'PlayerController')) or 'NOTHING')
for key, want in (('E', 1), ('Q', 2)):
    kn = next(n for n in nodes if n.get('type_id') == 'Input|KeyboardEvents|' + key)
    for c in (pin(kn, 'Pressed').get('connected_pins') or []):
        cd = json.loads(M.bp('get_node_infos', {'nodes': [{'refPath': c['node']['refPath']}]}))['returnValue'][0]
        rp = pin(cd, 'Result')
        if rp:
            print('%s -> %s Result=%s' % (key, c['node']['refPath'].split('.')[-1],
                                          str(M.bp('get_pin_value', {'pin': rp['pin_id']}))[:40]))
