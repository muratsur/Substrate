"""Pause menu Restart = new run from shift 1. It only reloaded the map, which used to restart because the save was never
loaded; now that LoadShiftState runs at startup, reset the saved round first (codex discoveries and Overtime unlocks are
kept - they are meta-progress). write_graph_dsl replaces the event body, so the whole handler is restated."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
W = '/Game/Substrate/UI/WBP_Pause.WBP_Pause'
RESTART = '''(event OnClicked(BtnRestart)
  (if (Variables|Default|GetConfirmRestart)
    (Game|SetGamePaused false)
    (if (SaveGame|DoesSaveGameExist "Substrate_0")
      (bind _loaded (SaveGame|LoadGameFromSlot "Substrate_0"))
      (bind _save (Utilities|Casting|CastToBP_SubstrateSave _loaded))
      (Class|BPSubstrateSave|ApplySaveData _save 0)
      (SaveGame|SaveGameToSlot _save "Substrate_0"))
    (Game|OpenLevel(byName) "/Game/Substrate/Maps/L_SectorC")
    (else
      (Variables|Default|SetConfirmRestart true)
      (Variables|Default|SetConfirmQuit false)
      (Widget|SetText(Text) (Variables|WBP_Pause|GetTxtConfirm) (Utilities|Text|ToText(String) "CONFIRM: CLICK RESTART AGAIN TO START OVER FROM SHIFT 001")))))
'''
print(M.bp('write_graph_dsl', {'graph': {'refPath': W + ':EventGraph'}, 'code': RESTART})[:400])
print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': W}})[:300])
s = json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'read_graph_dsl', 'arguments': {'graph': {'refPath': W + ':EventGraph'}}})).get('returnValue', '')
open('_backups/saveload_20261024/WBP_Pause_EventGraph_after.dsl', 'w').write(s)
