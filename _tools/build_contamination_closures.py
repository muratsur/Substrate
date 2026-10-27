"""Contamination rule (from round 8 / Overtime): +1 per failed audit with a missed anomaly, -1 per clean close (min 0).
At 2 the west-canal bridge W (x -3253) closes behind the player: the first time they step off it. At 4 bridge E (x -756)
closes as soon as the player is not on it. Every StartShift reopens both. Ways back were checked with walk_graph.py
--walls plus capsule-width traces (2026-10-26): with W closed, bridge E; with both closed, the walkway along the canal's
east end (x 400..700).
The blockers are SM_module_wall_01 segments on each deck, tagged ContamBlockW / ContamBlockE, hidden with collision off
until closed. The counter is not saved: quitting resets it to 0.
Usage: python _tools/build_contamination_closures.py place|bp   (PIE must be stopped), then save from the editor."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
M.init()
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
MESH = '/Game/Modular_Sewer_Kit/Meshes/Modules/Walls/SM_module_wall_01.SM_module_wall_01'
DECK_Z = 342.0   # deck top 347 at y 765 on both bridges; the mesh pivot is its min corner
BRIDGES = {'W': -3253.0, 'E': -756.0}

def place():
    for side, x in BRIDGES.items():
        label = f'ContamBlock{side}'
        if json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': label, 'tag': '', 'collision_channels': []}})).get('returnValue'):
            print(label, 'already exists'); continue
        res = json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'add_to_scene_from_asset', 'arguments': {
            'asset_path': MESH, 'name': label,
            'xform': {'location': {'x': x - 150.0, 'y': 715.0, 'z': DECK_Z}, 'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0}, 'scale': {'x': 300.0 / 540.0, 'y': 1.0, 'z': 1.0}}}}))
        ref = res['returnValue']['refPath']
        M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': ref + '.StaticMeshComponent0'},
            'values': json.dumps({'BodyInstance': {'collisionEnabled': 'QueryAndPhysics', 'collisionProfileName': 'BlockAll'}})}})
        M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': ref}, 'values': json.dumps({'bHidden': True})}})
        M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'add_tag', 'arguments': {'actor': {'refPath': ref}, 'tag': label}})
        b = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_bounds', 'arguments': {'actor': {'refPath': ref}}}))['returnValue']
        print(label, ref.split('.')[-1], {k: [round(b['min'][k]), round(b['max'][k])] for k in 'xyz'})

# box tests: bridge deck incl. ramps, above the canal bed (z 105)
ON = lambda x0, x1: f'(and (and (> (.x _loc) {x0}) (< (.x _loc) {x1})) (and (and (> (.y _loc) 380.0) (< (.y _loc) 1150.0)) (> (.z _loc) 250.0)))'
# the DSL can't declare typed params on a new function, so the show/hide loop is inlined
SET = lambda tag, closed: f'''(for a (Actor|GetAllActorsWithTag "{tag}")
    (Rendering|SetActorHiddenInGame :self a :bNewHidden {str(not closed).lower()})
    (Collision|SetActorEnableCollision :self a :bNewActorEnableCollision {str(closed).lower()}))'''
CODE = {
    'ReopenCrossings': f'''(fn ReopenCrossings ()
  (Variables|Default|SetClosedW false)
  (Variables|Default|SetClosedE false)
  (Variables|Default|SetOnBridgeW false)
  {SET("ContamBlockW", False)}
  {SET("ContamBlockE", False)}
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "CheckCrossings" :Time 0.2 :bLooping true))
''',
    'CheckCrossings': f'''(fn CheckCrossings ()
  (bind _pawn (Game|GetPlayerPawn 0))
  (Utilities|IsValid _pawn
    (:"Is Valid"
      (bind _loc (Transformation|GetActorLocation _pawn))
      (bind _onw {ON(-3420.0, -3080.0)})
      (if (and (and (>= (Variables|Default|GetContamination) 2) (not (Variables|Default|GetClosedW))) (and (Variables|Default|GetOnBridgeW) (not _onw)))
        (Variables|Default|SetClosedW true)
        {SET("ContamBlockW", True)})
      (Variables|Default|SetOnBridgeW _onw)
      (if (and (and (>= (Variables|Default|GetContamination) 4) (not (Variables|Default|GetClosedE))) (not {ON(-940.0, -570.0)}))
        (Variables|Default|SetClosedE true)
        {SET("ContamBlockE", True)}))))
'''}
LATE = '(or (>= (Variables|Default|GetCurrentRound) 8) (Variables|Default|GetIsOvertime))'

def read(g):
    return json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': RM + ':' + g}})).get('returnValue', '')

def write(g, code):
    before = read(g)
    print(g, '->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':' + g}, 'code': code})[:300])
    print(''.join(difflib.unified_diff(before.splitlines(True), read(g).splitlines(True), 'before', 'after')))

def bp():
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    have = [v['name'] if isinstance(v, dict) else v for v in json.loads(M.bp('list_variables', {'blueprint': {'refPath': RM}}))['returnValue']]
    for name, t in (('Contamination', 'int'), ('ClosedW', 'bool'), ('ClosedE', 'bool'), ('OnBridgeW', 'bool')):
        if name not in have: B.add_var(RM, name, t)
    B.compile_bp(RM)
    for g in CODE:
        try: M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': g})
        except Exception: pass
        write(g, CODE[g])
    B.compile_bp(RM)
    # StartShift reopens; TryCloseShift counts (re-read and patched so the rest of each body stays as it is)
    s = read('StartShift')
    if 'ReopenCrossings' not in s:
        s = s.replace('  (CallFunction|ArmGrowth)\n', '  (CallFunction|ArmGrowth)\n  (CallFunction|ReopenCrossings)\n', 1)
        assert 'ReopenCrossings' in s; write('StartShift', s)
    t = read('TryCloseShift')
    if 'Contamination' not in t:
        a = '      (CallFunction|RecordDiscoveredAnomalies)\n'
        f = '      (else\n        (CallFunction|OnShiftAuditFailed))'
        assert a in t and f in t
        t = t.replace('(|GetbIsOvertime)', '(Variables|Default|GetIsOvertime)')   # read-back form isn't writable
        t = t.replace(a, a + f'      (if (and {LATE} (> (Variables|Default|GetContamination) 0))\n        (Variables|Default|SetContamination (- (Variables|Default|GetContamination) 1)))\n')
        # failure call first: '(else (if ...) X)' is read back as an elif with X inside it
        t = t.replace(f, f'      (else\n        (CallFunction|OnShiftAuditFailed)\n        (if (and {LATE} (Variables|Default|GetAuditMissedAnomaly))\n          (Variables|Default|SetContamination (+ (Variables|Default|GetContamination) 1))))')
        write('TryCloseShift', t)
    B.compile_bp(RM)

if __name__ == '__main__':
    {'place': place, 'bp': bp}[sys.argv[1]]()
