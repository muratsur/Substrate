"""Step 5: Automated 4K Steam Screenshots Capture for L_SectorC."""
import sys
import os
import glob
import time
import shutil
from PIL import Image
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
EG = {'refPath': RM + ':EventGraph'}
ENABLE_INPUT = f'{RM}:EventGraph.K2Node_CallFunction_51'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

STEP_CAPTURE = '''(fn StepSteamCapture ()
  (bind pawn (Game|GetPlayerPawn 0))
  (bind ctrl (Game|GetPlayerController 0))
  (bind term (Variables|Default|GetTerminal))
  (bind step (Variables|Default|GetSteamShotStep))
  (switch int step
    (:0
      (Variables|Default|SetSteamShotStep 1)
      (Class|BPTerminal|ApplyRaised :self term :Want false)
      (Transformation|SetActorLocationAndRotation :self pawn :NewLocation (Math|Vector|MakeVector 600.0 3500.0 420.0) :NewRotation (Math|Rotator|MakeRotator 0.0 90.0 0.0) :bSweep false)
      (Pawn|SetControlRotation :self ctrl :NewRotation (Math|Rotator|MakeRotator 0.0 90.0 0.0))
      (Development|ExecuteConsoleCommand "HighResShot 3840x2160")
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "StepSteamCapture" :Time 2.5 :bLooping false))
    (:1
      (Variables|Default|SetSteamShotStep 2)
      (Class|BPTerminal|ApplyRaised :self term :Want false)
      (Transformation|SetActorLocationAndRotation :self pawn :NewLocation (Math|Vector|MakeVector 8560.0 4300.0 420.0) :NewRotation (Math|Rotator|MakeRotator 0.0 -90.0 0.0) :bSweep false)
      (Pawn|SetControlRotation :self ctrl :NewRotation (Math|Rotator|MakeRotator 0.0 -90.0 0.0))
      (Development|ExecuteConsoleCommand "HighResShot 3840x2160")
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "StepSteamCapture" :Time 2.5 :bLooping false))
    (:2
      (Variables|Default|SetSteamShotStep 3)
      (Transformation|SetActorLocationAndRotation :self pawn :NewLocation (Math|Vector|MakeVector 1469.0 4150.0 420.0) :NewRotation (Math|Rotator|MakeRotator -5.0 90.0 0.0) :bSweep false)
      (Pawn|SetControlRotation :self ctrl :NewRotation (Math|Rotator|MakeRotator -5.0 90.0 0.0))
      (CallFunction|LogLookedAtFixture 1)
      (Class|BPTerminal|ApplyRaised :self term :Want true)
      (Development|ExecuteConsoleCommand "HighResShot 3840x2160")
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "StepSteamCapture" :Time 2.5 :bLooping false))
    (:3
      (Variables|Default|SetSteamShotStep 4)
      (Variables|Default|SetCurrentRound 5)
      (CallFunction|RefreshTerminal)
      (Class|BPTerminal|ApplyRaised :self term :Want true)
      (Transformation|SetActorLocationAndRotation :self pawn :NewLocation (Math|Vector|MakeVector 1469.0 4150.0 420.0) :NewRotation (Math|Rotator|MakeRotator -5.0 90.0 0.0) :bSweep false)
      (Pawn|SetControlRotation :self ctrl :NewRotation (Math|Rotator|MakeRotator -5.0 90.0 0.0))
      (Development|ExecuteConsoleCommand "HighResShot 3840x2160")
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "StepSteamCapture" :Time 2.5 :bLooping false))
    (:4
      (Variables|Default|SetSteamShotStep 5)
      (Class|BPTerminal|ApplyRaised :self term :Want false)
      (bind gn (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_GrowthNode.BP_GrowthNode_C"))
      (for elem gn
        (bind gnode (Utilities|Casting|CastToBP_GrowthNode elem)
          (:then
            (Class|BPGrowthNode|ForceAdvance :self gnode)
            (Class|BPGrowthNode|ForceAdvance :self gnode)
            (Class|BPGrowthNode|ForceAdvance :self gnode))
          (:CastFailed)))
      (Transformation|SetActorLocationAndRotation :self pawn :NewLocation (Math|Vector|MakeVector 2200.0 4950.0 370.0) :NewRotation (Math|Rotator|MakeRotator -15.0 90.0 0.0) :bSweep false)
      (Pawn|SetControlRotation :self ctrl :NewRotation (Math|Rotator|MakeRotator -15.0 90.0 0.0))
      (Development|ExecuteConsoleCommand "HighResShot 3840x2160")
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "StepSteamCapture" :Time 2.5 :bLooping false))
    (:5
      (Variables|Default|SetSteamShotStep 6)
      (bind socks (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C"))
      (for s socks
        (bind sock (Utilities|Casting|CastToBP_AnomalySocket s)
          (:then
            (if (== (Class|BPAnomalySocket|GetAnomalyType :self sock) 0)
              (Class|BPAnomalySocket|Apply :self sock :Round 2)))
          (:CastFailed)))
      (CallFunction|RefreshTerminal)
      (Class|BPTerminal|ApplyRaised :self term :Want true)
      (Transformation|SetActorLocationAndRotation :self pawn :NewLocation (Math|Vector|MakeVector -1516.0 8050.0 410.0) :NewRotation (Math|Rotator|MakeRotator -5.0 90.0 0.0) :bSweep false)
      (Pawn|SetControlRotation :self ctrl :NewRotation (Math|Rotator|MakeRotator -5.0 90.0 0.0))
      (Development|ExecuteConsoleCommand "HighResShot 3840x2160")
      (Development|PrintString "ALL 6 STEAM SCREENSHOTS CAPTURED!" true true "(R=0.200000,G=1.000000,B=0.500000,A=1.000000)" 8.0))
    (:Default)))
'''

def add_hook():
    import json
    print('Connecting RunSteamCapture timer to EnableInput...')
    r_t = M.bp('create_node', {
        'graph': EG,
        'type_id': 'Utilities|Time|SetTimerbyFunctionName',
        'pos': {'x': 800, 'y': 0}
    })
    t_ref = json.loads(r_t)['returnValue']['refPath']
    info = json.loads(M.bp('get_node_infos', {'nodes': [{'refPath': t_ref}, {'refPath': ENABLE_INPUT}]}))['returnValue']
    ti = [i for i in info if i['node']['refPath'] == t_ref][0]
    ei = [i for i in info if i['node']['refPath'] == ENABLE_INPUT][0]

    for p in ti['input_pins']:
        if p['name'] == 'FunctionName':
            M.bp('set_pin_value', {'pin': p['pin_id'], 'value': 'RunSteamCapture'})
        elif p['name'] == 'Time':
            M.bp('set_pin_value', {'pin': p['pin_id'], 'value': '3.0'})
        elif p['name'] == 'bLooping':
            M.bp('set_pin_value', {'pin': p['pin_id'], 'value': 'false'})

    e_then = [p for p in ei['output_pins'] if p['name'] == 'then'][0]
    t_exec = [p for p in ti['input_pins'] if p['type_id'] == 'Exec'][0]
    M.bp('connect_pins', {'output_pin': e_then['pin_id'], 'input_pin': t_exec['pin_id']})

    M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM]}})
    return t_ref

def remove_hook(t_ref):
    print(f'Removing timer hook {t_ref}...')
    try:
        M.bp('delete_node', {'node': {'refPath': t_ref}})
        M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
        M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM]}})
    except Exception as e:
        print('Error removing hook:', e)

def main():
    M.init()
    print('=== STEP 5: CAPTURE 6 STEAM 4K SCREENSHOTS ===')

    # 1. Clean existing screenshots in WindowsEditor folder
    scr_dir = 'Saved/Screenshots/WindowsEditor'
    os.makedirs(scr_dir, exist_ok=True)
    for old in glob.glob(os.path.join(scr_dir, '*.png')):
        try:
            os.remove(old)
        except Exception:
            pass
    print('Cleaned old screenshots in', scr_dir)

    # 2. Update StepSteamCapture in BP_RoundManager
    print('Updating StepSteamCapture...')
    r_sc = M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:StepSteamCapture'}, 'code': balance(STEP_CAPTURE)})
    print('  StepSteamCapture written:', r_sc[:150])
    c_r = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('  Compile BP_RoundManager:', c_r[:100])
    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM]}})

    # 3. Add hook & launch PIE
    t_ref = add_hook()
    print('Launching PIE...')
    M.app('StartPIE', {'options': {'bSimulate': False}})

    # 4. Wait for shots: 3.0s initial + 6 * 2.5s = 18s -> wait up to 25s
    print('Waiting for screenshot sequence to complete (up to 26 seconds)...')
    target_count = 6
    for sec in range(26):
        time.sleep(1)
        shots = glob.glob(os.path.join(scr_dir, '*.png'))
        print(f'  second {sec+1:02d}: {len(shots)}/6 screenshots captured')
        if len(shots) >= target_count:
            print('  All 6 shots detected on disk! Waiting 2s for file flushing...')
            time.sleep(2)
            break

    # 5. Stop PIE
    print('Stopping PIE...')
    M.app('StopPIE', {})
    time.sleep(3)

    # 6. Remove hook
    remove_hook(t_ref)

    # 7. Check and organize the screenshots
    final_shots = sorted(glob.glob(os.path.join(scr_dir, '*.png')))
    print(f'Total screenshots captured: {len(final_shots)}')
    steam_dest_dir = 'Saved/Screenshots/Steam'
    os.makedirs(steam_dest_dir, exist_ok=True)

    names = [
        '01_Atmosphere_Sewer.png',
        '02_Atmosphere_Transit.png',
        '03_Terminal_Logging.png',
        '04_Terminal_PhantomRow.png',
        '05_Growth_MidLadder.png',
        '06_Absence_C04_CapsuleHook.png'
    ]

    for idx, f in enumerate(final_shots):
        if idx < len(names):
            dest = os.path.join(steam_dest_dir, names[idx])
            shutil.copyfile(f, dest)
            im = Image.open(dest)
            sz = os.path.getsize(dest)
            print(f'  [{idx+1}/6] {names[idx]} -> {im.size[0]}x{im.size[1]} ({sz // 1024} KB)')

    print('Step 5 Complete!')

if __name__ == '__main__':
    main()
