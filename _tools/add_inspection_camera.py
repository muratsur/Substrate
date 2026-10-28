"""Inspection camera. C photographs the fixture you are looking at (same 4 m view test as E/Q), using one of FILM shots per
shift. A photographed fixture counts as reported at the audit whatever its state: it is the hedge for "I'm not sure",
and it reveals nothing (the terminal shows [PHOTO], the remaining count drops either way). Photographed IDs are kept as
"|ID|" in the PhotoIDs string (no array variables through this toolset); StartShift resets film and photos.
Usage: python _tools/add_inspection_camera.py   (PIE stopped), then save BP_RoundManager."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
M.init()
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
G = {'refPath': RM + ':EventGraph'}
FILM = 3
call = lambda tool, args: json.loads(M.bp(tool, args))['returnValue']
read = lambda g: json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': RM + ':' + g}})).get('returnValue', '')
PHOTO_KEY = lambda f: f'(Utilities|String|Append (Utilities|String|Append "|" (Utilities|String|ToString(Name) (Class|BPFixture|GetFixtureID {f}))) "|")'
PHOTOGRAPHED = lambda f: f'(Utilities|String|Contains (Variables|Default|GetPhotoIDs) {PHOTO_KEY(f)})'

def write(g, code):
    before = read(g)
    print(g, '->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':' + g}, 'code': code})[:300])
    print(''.join(difflib.unified_diff(before.splitlines(True), read(g).splitlines(True), 'before', 'after')))

def patch(g, pairs, done):
    s = read(g)
    if done in s: print(g, 'already patched'); return
    # read-back forms the writer rejects
    s = s.replace('(|GetbIsOvertime)', '(Variables|Default|GetIsOvertime)').replace('(Camera|GetTarget _asbp_anomaly_socket)', '(Class|BPAnomalySocket|GetTargetActor _asbp_anomaly_socket)').replace('(Utilities|Equal(Object) _target Fixture)', '(== _target Fixture)')
    for old, new in pairs:
        assert s.count(old) == 1, (g, old)
        s = s.replace(old, new)
    write(g, s)

TAKE = f'''(fn TakePhoto ()
  (if (<= (Variables|Default|GetFilmLeft) 0)
    (CallFunction|ShowHint :Text "NO FILM LEFT")
    (else
      (Variables|Default|SetBestDist 400.0)
      (for a (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C")
        (bind _f (Utilities|Casting|CastToBP_Fixture a))
        (bind _score (Class|BPFixture|ViewScore _f (Camera|GetCameraLocation (Game|GetPlayerCameraManager 0)) (Math|Vector|GetForwardVector (Camera|GetCameraRotation (Game|GetPlayerCameraManager 0)))))
        (if (< _score (Variables|Default|GetBestDist))
          (Variables|Default|SetBestDist _score)
          (Variables|Default|SetBestFixture _f)))
      (if (< (Variables|Default|GetBestDist) 400.0)
        (bind _best (Variables|Default|GetBestFixture))
        (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Camera_Shutter.Camera_Shutter" 0.8 1.0)
        (CameraFades|StartCameraFade (Game|GetPlayerCameraManager 0) 0.8 0.0 0.25 "(R=1.000000,G=1.000000,B=1.000000,A=1.000000)" false false)
        (if (not {PHOTOGRAPHED('_best')})
          (Variables|Default|SetFilmLeft (- (Variables|Default|GetFilmLeft) 1))
          (Variables|Default|SetPhotoIDs (Utilities|String|Append (Variables|Default|GetPhotoIDs) {PHOTO_KEY('_best')})))
        (CallFunction|ShowHint :Text (Utilities|String|Append (Utilities|String|Append "PHOTO " (Utilities|String|ToString(Name) (Class|BPFixture|GetFixtureID _best))) (Utilities|String|Append " - FILM " (Utilities|String|ToString(Integer) (Variables|Default|GetFilmLeft)))))
        (else
          (CallFunction|ShowHint :Text "NO FIXTURE IN FRAME WITHIN 4 M"))))))
'''

if __name__ == '__main__':
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    have = [v['name'] if isinstance(v, dict) else v for v in call('list_variables', {'blueprint': {'refPath': RM}})]
    if 'FilmLeft' not in have: B.add_var(RM, 'FilmLeft', 'int')
    if 'PhotoIDs' not in have: B.add_var(RM, 'PhotoIDs', 'string')
    try: M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': 'TakePhoto'})
    except Exception as e: print('TakePhoto exists:', str(e)[:80])
    B.compile_bp(RM)
    write('TakePhoto', TAKE)
    patch('StartShift', [('  (Variables|Default|SetLastLoggedAction "")\n',
          f'  (Variables|Default|SetLastLoggedAction "")\n  (Variables|Default|SetFilmLeft {FILM})\n  (Variables|Default|SetPhotoIDs "")\n')], 'SetFilmLeft')
    patch('TryCloseShift', [('(bind _correct (Class|BPFixture|IsLoggedCorrectly _asbp_fixture))',
             f'(bind _correct (or (Class|BPFixture|IsLoggedCorrectly _asbp_fixture) {PHOTOGRAPHED("_asbp_fixture")}))')], 'GetPhotoIDs')
    patch('AddRowIfMatch', [('(bind _correct (Class|BPFixture|IsLoggedCorrectly _asbp_fixture))',
             f'(bind _correct (or (Class|BPFixture|IsLoggedCorrectly _asbp_fixture) {PHOTOGRAPHED("_asbp_fixture")}))'),
            ('(select (== (Class|BPFixture|GetLogResult _asbp_fixture) 0) "[ ]" ',
             f'(select (== (Class|BPFixture|GetLogResult _asbp_fixture) 0) (select {PHOTOGRAPHED("_asbp_fixture")} "[PHOTO]" "[ ]") ')], 'GetPhotoIDs')
    B.compile_bp(RM)
    # C key -> TakePhoto
    for k in call('find_nodes', {'graph': G, 'title': '', 'node_class': {'refPath': '/Script/BlueprintGraph.K2Node_InputKey'}}):
        if call('get_node_infos', {'nodes': [k]})[0].get('type_id') == 'Input|KeyboardEvents|C':
            print('C key already wired'); break
    else:
        mk = lambda t, x, y: (lambda n: n if 'refPath' in n else n['node'])(call('create_node', {'graph': G, 'type_id': t, 'pos': {'x': x, 'y': y}}))
        key, fn = mk('Input|KeyboardEvents|C', 0, 3000), mk('CallFunction|TakePhoto', 300, 3000)
        pins = lambda n: {(p['pin_id']['direction'], p['name']): p['pin_id'] for i in [call('get_node_infos', {'nodes': [n]})[0]] for p in i.get('input_pins', []) + i.get('output_pins', [])}
        pk, pf = pins(key), pins(fn)
        print('C ->', M.bp('connect_pins', {'output_pin': pk[('EGPD_Output', 'Pressed')], 'input_pin': pf[('EGPD_Input', 'execute')]})[:120])
    B.compile_bp(RM)
