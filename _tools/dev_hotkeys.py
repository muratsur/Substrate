"""Dev hotkeys so a playtest doesn't need the whole A-C-B-A walk (2026-11-08).
  1  jump to the next checklist fixture, facing it (cycles rows 0..RequiredRowMax)
  2  skip the shift: log every required row correctly, then run the normal close (audit + debrief)
  3  print this shift's anomalies on screen for 10 s
(Not F5-F7: during Play the editor uses the F keys for view modes - F5 switched to Shader Complexity.)
Only active outside Shipping AND either with no Content/Paks folder (the editor; packaged builds load from paks) or
when launched with -devhotkeys, so packaged tester builds don't get them by default. (The editor's command line is
empty, so it can't be detected from that.)
Each placed BP_Fixture gets a DevSpot (where key 1 puts you): 1.2 m out from the prop on its most open side, the same
rule fixture_plates.py uses for plates.
Usage: python _tools/dev_hotkeys.py   (PIE stopped), then save L_SectorC (DevSpot values live on placed fixtures)."""
import sys, json, math
sys.path.insert(0, '_tools')
import mcpx as M
import build_sector_a as A
from aim_and_airlock_feedback import RM, FIX, add_var, write, ok
from fixture_plates import LV, prop_box, open_yaw, trace
FBP = '/Game/Substrate/Core/BP_Fixture.BP_Fixture'
G = {'refPath': RM + ':EventGraph'}
ALLOWED = ('(and (not (Development|IsPackagedforDistribution)) (or (not (Utilities|Paths|DirectoryExists (Utilities|String|Append (Utilities|Paths|ProjectContentDir) "Paks"))) '
           '(Utilities|String|Contains (Utilities|GetCommandLine) "-devhotkeys")))')

NEXT = '''(fn DevNextFixture ()
  (if %(ok)s
    (Variables|Default|SetDevFound false)
    (bind _outactors (Actor|GetAllActorsOfClass "%(fix)s"))
    (for _index (range (+ (Variables|Default|GetRequiredRowMax) 1))
      (for _array_element _outactors
        (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
        (if (and (not (Variables|Default|GetDevFound)) (and (>= _index (Variables|Default|GetDevNextRow)) (== (Class|BPFixture|GetRowOrder _asbp_fixture) _index)))
          (Variables|Default|SetDevFound true)
          (Variables|Default|SetDevNextRow (+ _index 1))
          (bind _pawn (Game|GetPlayerPawn 0))
          (bind _rot (Math|Rotator|FindLookatRotation (Class|BPFixture|GetDevSpot _asbp_fixture) (Transformation|GetActorLocation _asbp_fixture)))
          (Transformation|SetActorLocationAndRotation :self _pawn :NewLocation (Class|BPFixture|GetDevSpot _asbp_fixture) :NewRotation _rot :bSweep false)
          (Pawn|SetControlRotation :self (Pawn|GetController :self _pawn) :NewRotation _rot)
          (CallFunction|ShowHint self (Utilities|String|Append "DEV: AT " (Utilities|String|ToString(Name) (Class|BPFixture|GetFixtureID _asbp_fixture)))))))
    (if (not (Variables|Default|GetDevFound))
      (Variables|Default|SetDevNextRow 0)
      (CallFunction|ShowHint "DEV: END OF CHECKLIST - F5 AGAIN STARTS OVER"))))
''' % {'ok': ALLOWED, 'fix': FIX}

SKIP = '''(fn DevSkipShift ()
  (if (and %(ok)s (Variables|Default|GetShiftOpen))
    (bind _outactors (Actor|GetAllActorsOfClass "%(fix)s"))
    (for _array_element _outactors
      (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
      (if (Class|BPFixture|InRowRange _asbp_fixture 0 (Variables|Default|GetRequiredRowMax))
        (Class|BPFixture|LogFixture _asbp_fixture (select (== (Class|BPFixture|GetFixtureState _asbp_fixture) 0) 1 2))))
    (CallFunction|TryCloseShift)))
''' % {'ok': ALLOWED, 'fix': FIX}

LIST = '''(fn DevAnomalyList ()
  (if %(ok)s
    (CallFunction|CollectDebriefChanges)
    (Development|PrintString (Utilities|String|Append (Utilities|String|Append "DEV - ANOMALIES THIS SHIFT:" (Variables|Default|GetNL)) (Variables|Default|GetDebriefChanges)) true true "(R=1.000000,G=0.800000,B=0.200000,A=1.000000)" 10.0 "DevAnomalyList")))
''' % {'ok': ALLOWED}

def call(tool, args):
    return json.loads(ok(M.bp(tool, args), tool))['returnValue']

def key_bound(key):
    for k in call('find_nodes', {'graph': G, 'title': '', 'node_class': {'refPath': '/Script/BlueprintGraph.K2Node_InputKey'}}):
        if call('get_node_infos', {'nodes': [k]})[0].get('type_id') == 'Input|KeyboardEvents|' + key: return True

def unbind_f_keys():
    """First version bound F5-F7, which the editor also uses for view modes during Play; drop those nodes and their calls."""
    for k in call('find_nodes', {'graph': G, 'title': '', 'node_class': {'refPath': '/Script/BlueprintGraph.K2Node_InputKey'}}):
        if call('get_node_infos', {'nodes': [k]})[0].get('type_id') in ('Input|KeyboardEvents|F5', 'Input|KeyboardEvents|F6', 'Input|KeyboardEvents|F7'):
            ok(M.bp('delete_node', {'node': k}), 'delete F key'); print('removed', k['refPath'].split('.')[-1])
    if not key_bound('1'):   # only before the first 1/2/3 wiring: drop the orphaned Dev* call nodes
        for k in call('find_nodes', {'graph': G, 'title': '', 'node_class': {'refPath': '/Script/BlueprintGraph.K2Node_CallFunction'}}):
            if call('get_node_infos', {'nodes': [k]})[0].get('type_id', '').split('|')[-1].startswith('Dev'):
                ok(M.bp('delete_node', {'node': k}), 'delete call'); print('removed', k['refPath'].split('.')[-1])

def wire(key, fn, y):
    if key_bound(key): print(key, 'already bound'); return
    types = call('find_node_types', {'graph': G, 'type_id_filter': fn, 'context_pins': []})
    tid = next(t if isinstance(t, str) else t['type_id'] for t in types if (t if isinstance(t, str) else t['type_id']).endswith('|' + fn))
    def make(type_id, x):
        n = call('create_node', {'graph': G, 'type_id': type_id, 'pos': {'x': x, 'y': y}})
        return n if isinstance(n, dict) and 'refPath' in n else n['node']
    k, c = make('Input|KeyboardEvents|' + key, 0), make(tid, 300)
    pins = lambda n: {(p['pin_id']['direction'], p['name']): p['pin_id'] for p in (lambda i: i.get('input_pins', []) + i.get('output_pins', []))(call('get_node_infos', {'nodes': [n]})[0])}
    ok(M.bp('connect_pins', {'output_pin': pins(k)[('EGPD_Output', 'Pressed')], 'input_pin': pins(c)[('EGPD_Input', 'execute')]}), 'wire ' + key)
    print(key, '->', tid)

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    # 1. per-fixture stand spots
    add_var(FBP, 'DevSpot', 'Vector')
    ok(M.bp('set_variable_instance_editable', {'blueprint': {'refPath': FBP}, 'variable_name': 'DevSpot', 'instance_editable': True}), 'DevSpot editable')
    ok(M.bp('compile_blueprint', {'blueprint': {'refPath': FBP}}), 'compile fixture')
    for i in range(12):
        a = {'refPath': LV + 'BP_Fixture_C_%d' % i}
        xf = A.call(M.ACT, 'get_actor_transform', {'actor': a})
        loc = xf['location']
        top, half = prop_box(i, loc, xf['scale']['x'])
        d = trace({'x': loc['x'], 'y': loc['y'], 'z': loc['z'] + 50}, {'x': loc['x'], 'y': loc['y'], 'z': loc['z'] - 400})
        floor = loc['z'] + 50 - d if d is not None else loc['z']
        yaw = math.radians(open_yaw(loc, floor + 120))
        spot = {'x': loc['x'] + (half + 120) * math.cos(yaw), 'y': loc['y'] + (half + 120) * math.sin(yaw), 'z': floor + 100}
        A.call(M.OBJ, 'set_properties', {'instance': a, 'values': json.dumps({'devSpot': '(X=%.1f,Y=%.1f,Z=%.1f)' % (spot['x'], spot['y'], spot['z'])})})
        got = json.loads(A.call(M.OBJ, 'get_properties', {'instance': a, 'properties': ['devSpot']}))['devSpot']
        assert abs(got['x'] - spot['x']) < 1, (i, got)
        print('BP_Fixture_C_%d spot' % i, {k: round(v) for k, v in spot.items()})
    # 2. Round Manager functions + keys
    add_var(RM, 'DevNextRow', 'int')
    add_var(RM, 'DevFound', 'bool')
    graphs = [g['refPath'].split(':')[-1] for g in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': RM}}))['returnValue']]
    for name, code, must in (('DevNextFixture', NEXT, ('SetActorLocationAndRotation', 'GetDevSpot')),
                             ('DevSkipShift', SKIP, ('LogFixture', 'TryCloseShift')),
                             ('DevAnomalyList', LIST, ('CollectDebriefChanges', 'PrintString'))):
        if name not in graphs: ok(M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': name}), 'add ' + name)
        write(RM, name, code, must + ('GetCommandLine',))
    unbind_f_keys()
    for key, fn, y in (('1', 'DevNextFixture', 3000), ('2', 'DevSkipShift', 3150), ('3', 'DevAnomalyList', 3300)):
        wire(key, fn, y)
    print('compile', ok(M.bp('compile_blueprint', {'blueprint': {'refPath': RM}}), 'compile')[:100])
    print('save', M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM, FBP]}})[:80])
