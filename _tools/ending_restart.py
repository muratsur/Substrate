"""The demo ending holds instead of quitting, and the valve reacts: a low venting sound, the chamber's red lights
(tag DChamberLight) die and the valve light (tag DValveLight) turns cold white. EndDemo used to fade fully to black (hiding the terminal message) and quit
5 s later, which in the editor just looks like Play stopping. Now: terminal raised with SUBSTRATE DEMO COMPLETE, the
screen dims to 85% black over 3 s so the message stays readable, and 9 s in RestartDemo deletes save slot Substrate_0
and reopens L_SectorC at shift 1. (Overtime is never unlocked anywhere, so the reset loses only shift progress.)
Usage: python _tools/ending_restart.py   (PIE stopped), then save BP_RoundManager."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
read = lambda g: json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': RM + ':' + g}})).get('returnValue', '')
CODE = {
    'EndDemo': '''(fn EndDemo ()
  (bind _self self)
  (Input|DisableInput :self _self :PlayerController (Game|GetPlayerController 0))
  (CallFunction|PushTerminal :Header "SHIFT TERMINATED" :Names "SUBSTRATE DEMO COMPLETE" :States "" :Footer "THANK YOU FOR PLAYING")
  (CallFunction|RaiseTerminal)
  (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Teleport_Mode_Entered.Teleport_Mode_Entered" 0.9 0.35)
  (for l (Actor|GetAllActorsWithTag "DChamberLight")
    (bind _lc (Utilities|Casting|CastToLightComponent (Actor|GetComponentByClass l "/Script/Engine.LightComponent"))
      (:then (Rendering|Components|Light|SetIntensity _lc 0.0))
      (:CastFailed)))
  (for v (Actor|GetAllActorsWithTag "DValveLight")
    (bind _vc (Utilities|Casting|CastToLightComponent (Actor|GetComponentByClass v "/Script/Engine.LightComponent"))
      (:then
        (Rendering|Components|Light|SetLightColor _vc "(R=0.850000,G=0.950000,B=1.000000,A=1.000000)" true)
        (Rendering|Components|Light|SetIntensity _vc 60.0))
      (:CastFailed)))
  (CameraFades|StartCameraFade (Game|GetPlayerCameraManager 0) 0.0 0.85 3.0 "(R=0.000000,G=0.000000,B=0.000000,A=1.000000)" true true)
  (Utilities|Time|SetTimerbyFunctionName :Object _self :FunctionName "RestartDemo" :Time 9.0))
''',
    'RestartDemo': '''(fn RestartDemo ()
  (SaveGame|DeleteGameInSlot :SlotName "Substrate_0" :UserIndex 0)
  (Game|OpenLevel(byName) :LevelName "/Game/Substrate/Maps/L_SectorC"))
'''}

def tags():
    import build_sector_a as A
    for label, tag in (('D_ChamberLight_0', 'DChamberLight'), ('D_ChamberLight_1', 'DChamberLight'), ('SectorD_C06_Light', 'DValveLight')):
        A.call(M.ACT, 'add_tag', {'actor': A.find(label), 'tag': tag})

if __name__ == '__main__':
    M.init()
    tags()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    try: M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': 'RestartDemo'})
    except Exception as e: print('RestartDemo exists:', str(e)[:60])
    B.compile_bp(RM)
    for g, c in CODE.items():
        before = read(g)
        print(g, '->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':' + g}, 'code': c})[:200])
        print(''.join(difflib.unified_diff(before.splitlines(True), read(g).splitlines(True), 'before', 'after')))
    B.compile_bp(RM)
