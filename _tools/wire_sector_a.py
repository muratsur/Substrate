"""Wire Sector A (built by build_sector_a.py) into the shift loop.
- Shifts start in A: PlayerStart_0 moves into the dome.
- Shifts close in A: the BP_RoundManager actor IS the close-shift trigger (its overlap calls TryCloseShift, which fails
  the audit if anything is unlogged), so it sits at the control console, off the walking line.
- A <-> C airlock pair: Airlock_AToDock in A's +Y doorway, Airlock_DockToA at the old spawn. Both gates are open
  (rows 100..100 match no fixture). BP_Airlock used to send you to "every other airlock" (fine with two, wrong with
  four), so each airlock now has a Partner and Transit goes there.
- A_DoorBack closes the -Y doorway; A_DoorOuter sits behind the airlock so you can't walk past it into the void.
Usage: python _tools/wire_sector_a.py   (PIE stopped), then save L_SectorC + BP_Airlock."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
import build_sector_a as A
AL = '/Game/Substrate/Core/BP_Airlock.BP_Airlock'
LV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
X, Y, Z = A.X, A.Y, A.Z
read = lambda g: json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': AL + ':' + g}})).get('returnValue', '')
PAIRS = [('Airlock_DockToTransit', 'Airlock_TransitToDock'), ('Airlock_AToDock', 'Airlock_DockToA')]
NEW_AIRLOCKS = {'Airlock_AToDock': (X, Y + 520, Z + 128), 'Airlock_DockToA': (-300, 1400, 390)}   # not (0, 1400): BP_CanalRescue drops fallers there
TRANSIT = '''(fn Transit (Traveler)
  (bind _self self)
  (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Teleport_Committed.Teleport_Committed" 0.7 0.6)
  (CameraFades|StartCameraFade (Game|GetPlayerCameraManager 0) 1.0 0.0 0.8 "(R=0.000000,G=0.000000,B=0.000000,A=1.000000)" false false)
  (if (Variables|Default|GetLoopBackThisOnce)
    (Variables|Default|SetLoopBackThisOnce false)
    (CallFunction|Disarm _self)
    (Transformation|SetActorLocation Traveler (Transformation|GetActorLocation _self))
    (CallFunction|FaceNearestFixture _self Traveler)
    (else
      (bind _p (Variables|Default|GetPartner))
      (CallFunction|Disarm _p)
      (Transformation|SetActorLocation Traveler (Transformation|GetActorLocation _p))
      (CallFunction|FaceNearestFixture _p Traveler))))
'''

def airlock_bp():
    have = [v['name'] if isinstance(v, dict) else v for v in json.loads(M.bp('list_variables', {'blueprint': {'refPath': AL}}))['returnValue']]
    if 'Partner' not in have:
        B.add_var(AL, 'Partner', None, obj_class=AL + '_C')
        B.editable(AL, 'Partner')
    B.compile_bp(AL)
    before = read('Transit')
    print('Transit ->', M.bp('write_graph_dsl', {'graph': {'refPath': AL + ':Transit'}, 'code': TRANSIT})[:200])
    print(''.join(difflib.unified_diff(before.splitlines(True), read('Transit').splitlines(True), 'before', 'after')))
    B.compile_bp(AL)

def level():
    for label, loc in NEW_AIRLOCKS.items():
        xf = {'location': dict(zip('xyz', loc)), 'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
        a = A.place(label, lambda: A.call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': AL + '_C'}, 'name': label, 'xform': xf}), xf)
        A.call(M.OBJ, 'set_properties', {'instance': a, 'values': json.dumps({'GateRowMin': 100, 'GateRowMax': 100})})
    for p, q in PAIRS:
        pa, qa = A.find(p), A.find(q)
        assert pa and qa, (p, q)
        for me, other in ((pa, qa), (qa, pa)):
            print(p, q, A.call(M.OBJ, 'set_properties', {'instance': me, 'values': json.dumps({'Partner': {'refPath': other['refPath']}})}))
    for label, dy in (('A_DoorBack', -600), ('A_DoorOuter', 690)):
        xf = A.xform(0, dy, 0)
        A.place(label, lambda: A.call(M.SCN, 'add_to_scene_from_asset', {'asset_path': A.KIT + 'Door/SM_door', 'name': label, 'xform': xf}), xf)
    # crates in front of the back door so it reads as blocked storage, not a way out
    xf = A.xform(0, -470, 0)
    A.place('A_BackCrates', lambda: A.call(M.SCN, 'add_to_scene_from_asset', {'asset_path': A.KIT + 'Crates/SM_crates_group_', 'name': 'A_BackCrates', 'xform': xf}), xf)
    # green lamp over each always-open airlock, so the way out and the way back can be seen
    for label, loc in (('A_AirlockLampA', (X, Y + 430, Z + 320)), ('A_AirlockLampDock', (-300, 1400, 600))):
        xf = {'location': dict(zip('xyz', loc)), 'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
        a = A.place(label, lambda: A.call(M.SCN, 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.PointLight'}, 'name': label, 'xform': xf}), xf)
        A.call(M.OBJ, 'set_properties', {'instance': {'refPath': a['refPath'] + '.LightComponent0'}, 'values': json.dumps(
            {'Intensity': 25.0, 'IntensityUnits': 'Candelas', 'AttenuationRadius': 450.0, 'LightColor': {'r': 0.2, 'g': 1.0, 'b': 0.35, 'a': 1.0}, 'Mobility': 'Movable'})})
    move = lambda ref, loc, yaw: A.call(M.ACT, 'set_actor_transform', {'actor': {'refPath': LV + ref}, 'xform': {'location': dict(zip('xyz', loc)), 'rotation': {'pitch': 0, 'yaw': yaw, 'roll': 0}}})
    move('PlayerStart_0', (X + 220, Y - 250, Z + 100), 120)   # facing the table and the airlock doorway
    move('BP_RoundManager_C_1', (X - 330, Y + 180, Z + 128), 0)   # close-shift trigger at the console

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
ROUTE_TIP = '''(fn ShowRouteTip ()
  (if (== (Variables|Default|GetCurrentRound) 1)
    (CallFunction|ShowHint :Text "GREEN DOOR: AIRLOCK   CONSOLE: CLOSE SHIFT")))
'''

def route_tip():
    """Shift 1: after the key tip clears (4 s hint at 1 s), say where the way out and the shift close are."""
    try: M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': 'ShowRouteTip'})
    except Exception as e: print('ShowRouteTip exists:', str(e)[:60])
    B.compile_bp(RM)
    print('ShowRouteTip ->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':ShowRouteTip'}, 'code': ROUTE_TIP})[:200])
    s = json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': RM + ':StartShift'}}))['returnValue']
    if 'ShowRouteTip' not in s:
        old = '  (Utilities|Time|SetTimerbyFunctionName _self "ShowFTip" 1.0)\n'
        assert s.count(old) == 1
        print('StartShift ->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':StartShift'}, 'code': s.replace(old, old + '  (Utilities|Time|SetTimerbyFunctionName :Object _self :FunctionName "ShowRouteTip" :Time 5.5)\n')})[:200])
    B.compile_bp(RM)

if __name__ == '__main__':
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    airlock_bp(); level(); route_tip()
