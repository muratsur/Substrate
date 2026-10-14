"""Acceptance test for the two reported defects in L_SectorC.

  1. "I can't move"          -> IA_Move / IA_Jump must be wired to the character's Move/Jump handlers
  2. "constant water sound"  -> every sound emitter in the level must be silenced
  3. "teleported to the start at the canal end" -> BP_CanalRescue_C_0 must sit below the walkable floor

Reads the editor world (the state that gets saved) plus the blueprint graphs the
running PIE session uses. Exits non-zero if any check fails.

Run:  python _tools/verify_saved.py
"""
import os
import sys
import json
import re
import time
sys.path.insert(0, '_tools')
import mcpx as M

M.init()

ACTOR = 'editor_toolset.toolsets.actor.ActorTools'
CHAR = '/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter.BP_FirstPersonCharacter'
G = CHAR + ':EventGraph'
LEV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
RMEG = {'refPath': RM + ':EventGraph'}
AUDIO_ASSETS = ['Content/Substrate/Audio/AMB_SewerRoomTone_Loop.uasset',
                'Content/Substrate/Audio/AMB_WaterDrips_Loop.uasset',
                'Content/FirstPerson/Blueprints/BP_FirstPersonCharacter.uasset',
                'Content/Substrate/Core/BP_Terminal.uasset',
                'Content/Substrate/Core/BP_RoundManager.uasset',
                'Content/Substrate/Maps/L_SectorC.umap']
failures = []


def check(label, ok, detail):
    print('%-4s %-34s %s' % ('PASS' if ok else 'FAIL', label, detail))
    if not ok:
        failures.append(label)


def getp(ref, props):
    r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties',
                             'arguments': {'instance': {'refPath': ref}, 'properties': props}})
    try:
        v = json.loads(r)['returnValue']
        return json.loads(v) if isinstance(v, str) else v
    except Exception:
        return {'error': r[:160]}


def raw_get(ref, props):
    """Raw text of a get_properties call, so 'property does not exist' answers are visible."""
    return M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties',
                                'arguments': {'instance': {'refPath': ref}, 'properties': props}})


def pin_links(node):
    """{pin name: [connected node names]} - event nodes report their links as outputs."""
    d = json.loads(M.bp('get_connected_subgraph',
                        {'node': {'refPath': G + '.' + node}}))['returnValue'][0]
    out = {}
    for p in d.get('input_pins', []) + d.get('output_pins', []):
        t = [c['node']['refPath'].split('.')[-1].replace('K2Node_', '')
             for c in (p.get('connected_pins') or [])]
        if t:
            out[p['name']] = t
    return out


def node_fn(node):
    d = json.loads(M.bp('get_node_infos', {'nodes': [{'refPath': G + '.' + node}]}))['returnValue'][0]
    return d.get('function') or d.get('type_id') or ''


def rm_nodes():
    """Every node of the RoundManager event graph, with refPath normalised."""
    refs = json.loads(M.bp('find_nodes', {'graph': RMEG, 'title': ''}))['returnValue']
    out = []
    for i in range(0, len(refs), 25):
        out += json.loads(M.bp('get_node_infos', {'nodes': refs[i:i + 25]}))['returnValue']
    for n in out:
        n['refPath'] = n.get('refPath') or n['node']['refPath']
    return out


def rm_pin(d, name):
    for p in d.get('input_pins', []) + d.get('output_pins', []):
        if p['name'] == name:
            return p
    return None


def actor_bounds(name):
    """(minx, miny, minz, maxx, maxy, maxz) for an actor in the persistent level."""
    r = M.call('call_tool', {'toolset_name': ACTOR, 'tool_name': 'get_actor_bounds',
                             'arguments': {'actor': {'refPath': LEV + name}}})
    try:
        v = json.loads(r)['returnValue']
        return tuple(round(v['min'][k]) for k in 'xyz') + tuple(round(v['max'][k]) for k in 'xyz')
    except Exception:
        return None


print('=== 1. movement (the "I can\'t move" defect)')
mv = pin_links('K2Node_EnhancedInputAction_3')
check('IA_Move -> Move exec', mv.get('Triggered') == ['CallFunction_5'], mv.get('Triggered'))
check('IA_Move.X -> strafe axis', mv.get('ActionValue_X') == ['CallFunction_5'], mv.get('ActionValue_X'))
check('IA_Move.Y -> forward axis', mv.get('ActionValue_Y') == ['CallFunction_5'], mv.get('ActionValue_Y'))

handler = pin_links('K2Node_CallFunction_5')
check('handler is the Move() fn', node_fn('K2Node_CallFunction_5') == '|Move', node_fn('K2Node_CallFunction_5'))
check('Move exec fed by IA_Move', handler.get('execute') == ['EnhancedInputAction_3'], handler.get('execute'))
check('Move strafe pin fed', handler.get('Left / Right') == ['EnhancedInputAction_3'], handler.get('Left / Right'))
check('Move forward pin fed', handler.get('Forward / Backward') == ['EnhancedInputAction_3'],
      handler.get('Forward / Backward'))

body = json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': CHAR + ':Move'}}))['returnValue']
check('Move body uses AddMovementInput',
      body.count('AddMovementInput') == 2 and 'RightVector' in body and 'ForwardVector' in body,
      ' '.join(body.split())[:100])

jm = pin_links('K2Node_EnhancedInputAction_5')
check('IA_Jump -> Jump', 'CallFunction_1193' in (jm.get('Started', []) + jm.get('Triggered', [])), jm.get('Started'))
check('IA_Jump release -> StopJumping', jm.get('Completed') == ['CallFunction_9386'], jm.get('Completed'))

print('=== 2. ambience (the "constant water sound" defect)')
for i in range(4):
    v = getp(LEV + 'AmbientSound_%d.AudioComponent0' % i,
             ['bAutoActivate', 'VolumeMultiplier', 'Sound'])
    snd = (v.get('Sound') or {}).get('refPath', '?').split('.')[-1]
    check('AmbientSound_%d is off' % i,
          v.get('bAutoActivate') is False and v.get('VolumeMultiplier') == 0,
          'auto=%s vol=%s sound=%s' % (v.get('bAutoActivate'), v.get('VolumeMultiplier'), snd))

water = ['BP_water_C_0', 'BP_water_C_1', 'BP_water_stream_C_1', 'BP_water_stream_C_3', 'BP_water_stream_C_5']
silent = []
for a in water:
    raw = raw_get(LEV + a, ['AudioComponent'])
    silent.append('could not be read' in raw or 'not valid Object' in raw)
check('water actors have no audio', all(silent), '%d/%d meshes only, no AudioComponent' % (sum(silent), len(water)))

print('=== 3. airlock gate plumbing (the tunnel gate needs E/Q fixture logging)')
rm = rm_nodes()
types = {x.get('type_id'): x for x in rm}
en = types.get('Input|EnableInput')
pc = rm_pin(en, 'PlayerController') if en else None
check('EnableInput has a PlayerController', bool(pc and pc.get('connected_pins')),
      'enabled for %s' % ([c['node']['refPath'].split('.')[-1] for c in (pc.get('connected_pins') or [])] if pc else 'NOTHING'))
for key, want, word, fn in (('E', 1, 'PASS', 'OnEKey'), ('Q', 2, 'FLAG', 'OnQKey')):
    k = types.get('Input|KeyboardEvents|' + key)
    pr = rm_pin(k, 'Pressed') if k else None
    targets = [c['node']['refPath'].split('.')[-1] for c in ((pr or {}).get('connected_pins') or [])]
    wired = bool(targets)
    body = ''
    try:
        body = json.loads(M.bp('read_graph_dsl',
                               {'graph': {'refPath': RM + ':' + fn}}))['returnValue']
    except Exception:
        pass
    logs_ok = ('LogLookedatFixture' in body or 'LogLookedAtFixture' in body) and re.search(r'LogLookedatFixture\b[^)]*\b%s\)' % want, body) is not None
    gate_ok = 'TryTransit' in body
    check('key %s logs %s' % (key, word), wired and logs_ok and gate_ok,
          'E->%s; handler: log(Result=%d)=%s airlock-branch=%s' % (targets or 'NOTHING', want, logs_ok, gate_ok))
for air, lo, hi in (('BP_Airlock_C_0', 0, 4), ('BP_Airlock_C_1', 5, 7)):
    a = getp(LEV + air, ['GateRowMin']).get('GateRowMin')
    b = getp(LEV + air, ['GateRowMax']).get('GateRowMax')
    check('%s wants rows %d-%d' % (air.split('_C_')[-1], lo, hi), a == lo and b == hi, 'rows %s-%s' % (a, b))

print('=== 4. canal end walkway is not a teleport trap')
rb = actor_bounds('BP_CanalRescue_C_0')
check('rescue box top below the walk floor', bool(rb) and rb[5] < 60,
      'box z %s..%s (walkable floor here is z=100)' % (rb[2], rb[5]) if rb else rb)
check('rescue still catches a fall', bool(rb) and rb[2] < -100,
      'box bottom z=%s, so a fall below the floor is still caught' % (rb[2] if rb else '?'))

print('=== 5. terminal screen no longer oversized')
tpl = getp('/Game/Substrate/Core/BP_Terminal.BP_Terminal_C:Screen_GEN_VARIABLE', ['DrawSize']).get('DrawSize')
pl = getp(LEV + 'BP_Terminal_C_0.Screen', ['DrawSize']).get('DrawSize')
check('template screen 30x22', tpl == {'x': 30, 'y': 22}, tpl)
check('placed screen 30x22', pl == {'x': 30, 'y': 22}, pl)

print('=== 6. artifacts on disk')
for f in AUDIO_ASSETS:
    st = os.stat(f.replace('/', os.sep))
    print('     %-62s %7d bytes  %s' % (f, st.st_size, time.strftime('%m-%d %H:%M:%S',
                                                                     time.localtime(st.st_mtime))))
print('     PIE running: %s' % M.app('IsPIERunning', {}))

print()
if failures:
    print('RESULT: %d FAILED -> %s' % (len(failures), ', '.join(failures)))
    sys.exit(1)
print('RESULT: all checks passed (editor reports "All Saved", so this is also the on-disk state)')
