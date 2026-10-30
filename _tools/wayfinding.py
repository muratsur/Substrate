"""Wayfinding after Sector A: the first full playtest stalled on "where are the last 4 rows?"
- A lamp over each gated airlock (tags WayLampC at the Dock, WayLampB at the Transit end): red while its gate is shut,
  green once its rows are done. BP_RoundManager.UpdateWayfinding recolours them after every log or photo, and
  0.5 s after StartShift (red again).
- Stage hints, once per shift: sewer rows done -> "SEWER LOGGED - TRANSIT AIRLOCK OPEN"; transit rows done ->
  "TRANSIT LOGGED - AIRLOCK BACK TO DOCK"; everything done -> OpenWestGate's hint now names the dome console.
- BP_Airlock.GateOpen counts a photographed fixture as done, the same as the audit does (add_inspection_camera.py);
  before, a photo satisfied the audit but left the airlock shut.
"Done" is the gate's own test (logged correctly or photographed), so the lamp tells you no more than the gate does.
Since overtime_title.py, TakePhoto only routes (title -> TitleOvertime, else PhotoShot): after re-running this
script, run overtime_title.photo() again so the photo body lands in PhotoShot.
Usage: python _tools/wayfinding.py   (PIE stopped), then save L_SectorC, BP_RoundManager, BP_Airlock."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
import build_sector_a as A
import add_inspection_camera as CAM
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
AL = '/Game/Substrate/Core/BP_Airlock.BP_Airlock'
FX = '/Game/Substrate/Core/BP_Fixture.BP_Fixture_C'
RED, GREEN = '(R=1.000000,G=0.120000,B=0.080000,A=1.000000)', '(R=0.200000,G=1.000000,B=0.350000,A=1.000000)'
LAMPS = {'WayLampC': (300, 1400, 600), 'WayLampB': (8560, 4520, 620)}   # over Airlock_DockToTransit / Airlock_TransitToDock
read = lambda bp, g: json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': bp + ':' + g}})).get('returnValue', '')

def write(bp, g, code):
    before = read(bp, g)
    print(g, '->', M.bp('write_graph_dsl', {'graph': {'refPath': bp + ':' + g}, 'code': code})[:200])
    print(''.join(difflib.unified_diff(before.splitlines(True), read(bp, g).splitlines(True), 'before', 'after')))

def lamp_colour(tag, pend):
    return f'''  (for l (Actor|GetAllActorsWithTag "{tag}")
    (bind _lc (Utilities|Casting|CastToLightComponent (Actor|GetComponentByClass l "/Script/Engine.LightComponent"))
      (:then
        (if (== (Variables|Default|Get{pend}) 0)
          (Rendering|Components|Light|SetLightColor _lc "{GREEN}" true)
          (else
            (Rendering|Components|Light|SetLightColor _lc "{RED}" true))))
      (:CastFailed)))'''

def stage_hint(pend, flag, text):
    return f'''  (if (and (== (Variables|Default|Get{pend}) 0) (not (Variables|Default|Get{flag})))
    (Variables|Default|Set{flag} true)
    (CallFunction|ShowHint :Text "{text}"))'''

WAY = f'''(fn UpdateWayfinding ()
  (Variables|Default|SetPendC 0)
  (Variables|Default|SetPendB 0)
  (for a (Actor|GetAllActorsOfClass "{FX}")
    (bind _f (Utilities|Casting|CastToBP_Fixture a))
    (if (not (or (Class|BPFixture|IsLoggedCorrectly _f) {CAM.PHOTOGRAPHED('_f')}))
      (if (Class|BPFixture|InRowRange _f 0 4)
        (Variables|Default|SetPendC (+ (Variables|Default|GetPendC) 1)))
      (if (Class|BPFixture|InRowRange _f 5 7)
        (Variables|Default|SetPendB (+ (Variables|Default|GetPendB) 1)))))
{lamp_colour('WayLampC', 'PendC')}
{lamp_colour('WayLampB', 'PendB')}
{stage_hint('PendC', 'HintSewerDone', 'SEWER LOGGED - TRANSIT AIRLOCK OPEN')}
{stage_hint('PendB', 'HintTransitDone', 'TRANSIT LOGGED - AIRLOCK BACK TO DOCK')})
'''

def lamps():
    for tag, loc in LAMPS.items():
        xf = {'location': dict(zip('xyz', loc)), 'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
        a = A.place(tag, lambda: A.call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.PointLight'}, 'name': tag, 'xform': xf}), xf)
        A.call(M.ACT, 'add_tag', {'actor': a, 'tag': tag})
        A.call(M.SCN, 'set_actor_folder', {'actor': a, 'folder_path': 'Substrate/Wayfinding'})
        A.call(M.OBJ, 'set_properties', {'instance': {'refPath': a['refPath'] + '.LightComponent0'}, 'values': json.dumps(
            {'Intensity': 25.0, 'IntensityUnits': 'Candelas', 'AttenuationRadius': 450.0, 'LightColor': {'r': 1.0, 'g': 0.12, 'b': 0.08, 'a': 1.0}, 'Mobility': 'Movable'})})

def round_manager():
    have = [v['name'] if isinstance(v, dict) else v for v in json.loads(M.bp('list_variables', {'blueprint': {'refPath': RM}}))['returnValue']]
    for v, t in (('PendC', 'int'), ('PendB', 'int'), ('HintSewerDone', 'bool'), ('HintTransitDone', 'bool')):
        if v not in have: B.add_var(RM, v, t)
    try: M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': 'UpdateWayfinding'})
    except Exception as e: print('UpdateWayfinding exists:', str(e)[:60])
    B.compile_bp(RM)
    write(RM, 'UpdateWayfinding', WAY)
    B.compile_bp(RM)
    s = read(RM, 'StartShift')
    if 'UpdateWayfinding' not in s:
        old = '  (Variables|Default|SetPhotoIDs "")\n'
        assert s.count(old) == 1
        write(RM, 'StartShift', s.replace(old, old + '  (Variables|Default|SetHintSewerDone false)\n  (Variables|Default|SetHintTransitDone false)\n'
                                          '  (Utilities|Time|SetTimerbyFunctionName :Object _self :FunctionName "UpdateWayfinding" :Time 0.5)\n'))
    s = read(RM, 'LogLookedAtFixture')
    if 'UpdateWayfinding' not in s:
        s = s.replace('(CallFunction|ShowHint "', '(CallFunction|ShowHint :Text "')   # read-back is positional
        assert s.rstrip().endswith('(CallFunction|RefreshTerminal))')
        write(RM, 'LogLookedAtFixture', s.rstrip()[:-1] + '\n  (CallFunction|UpdateWayfinding))\n')
    if 'UpdateWayfinding' not in read(RM, 'TakePhoto'):
        write(RM, 'TakePhoto', CAM.TAKE.rstrip()[:-1] + '\n  (CallFunction|UpdateWayfinding))\n')
    s = read(RM, 'OpenWestGate')
    if 'DOME CONSOLE' not in s:
        import hints_on_terminal as H
        write(RM, 'OpenWestGate', H.CODE['OpenWestGate'].replace('"WEST GATE OPEN - ALL FIXTURES LOGGED"', '"ALL LOGGED - CLOSE SHIFT AT DOME CONSOLE"'))
    B.compile_bp(RM)

def airlock_gate():
    s = read(AL, 'GateOpen')
    if 'GetPhotoIDs' in s: print('GateOpen already patched'); return
    old = '(bind _correct (Class|BPFixture|IsLoggedCorrectly _asbp_fixture))'
    assert s.count(old) == 1
    rm = '(Utilities|Casting|CastToBP_RoundManager (Actor|GetActorOfClass "/Game/Substrate/Core/BP_RoundManager.BP_RoundManager_C"))'
    photo = CAM.PHOTOGRAPHED('_asbp_fixture').replace('(Variables|Default|GetPhotoIDs)', f'(Class|BPRoundManager|GetPhotoIDs {rm})')
    write(AL, 'GateOpen', s.replace(old, f'(bind _correct (or (Class|BPFixture|IsLoggedCorrectly _asbp_fixture) {photo}))'))
    B.compile_bp(AL)

if __name__ == '__main__':
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    lamps(); round_manager(); airlock_gate()
