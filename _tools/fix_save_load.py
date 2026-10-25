"""Progress persistence. Before: SaveShiftState stored only the round, LoadShiftState was never called, and when it ran it
read each saved codex/overtime value and then reset the live variable to 0/false instead. BP_SubstrateSave's helper
functions (SetCodexData, GetDiscoveredMask, ...) were empty stubs; they were removed so the Class|BPSubstrateSave|Get/Set
ids below resolve to the save object's variables. Backups: _backups/saveload_20261024/."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
FIELDS = ['DiscoveredMask', 'DiscoveredCount', 'CompletedSectorD', 'OvertimeUnlocked', 'HighestOvertimeShift']
PIN = {'OvertimeUnlocked': 'bOvertimeUnlocked'}  # the bool setter's value pin keeps the b prefix
NL = '\n'
LOAD_FIELDS = NL.join(f'    (Variables|Default|Set{f} (Class|BPSubstrateSave|Get{f} _save))' for f in FIELDS)
SAVE_FIELDS = NL.join(f'    (Class|BPSubstrateSave|Set{f} :self _save :{PIN.get(f, f)} (Variables|Default|Get{f}))' for f in FIELDS)  # setter pins: value first, then self
LOAD = f'''(fn LoadShiftState ()
  (bind _exists (SaveGame|DoesSaveGameExist "Substrate_0"))
  (if _exists
    (bind _loaded (SaveGame|LoadGameFromSlot "Substrate_0"))
    (bind _save (Utilities|Casting|CastToBP_SubstrateSave _loaded))
    (bind _round (Class|BPSubstrateSave|GetSavedRound _save))
    (if (> _round 1)
      (Variables|Default|SetCurrentRound (- _round 1)))
{LOAD_FIELDS}))
'''
SAVE = f'''(fn SaveShiftState ()
  (if (> (Variables|Default|GetCurrentRound) 1)
    (bind _created (SaveGame|CreateSaveGameObject "/Game/Substrate/Core/BP_SubstrateSave.BP_SubstrateSave_C"))
    (bind _save (Utilities|Casting|CastToBP_SubstrateSave _created))
    (Class|BPSubstrateSave|ApplySaveData _save (Variables|Default|GetCurrentRound))
{SAVE_FIELDS}
    (SaveGame|SaveGameToSlot _save "Substrate_0")
    (Development|PrintString "Game saved to slot Substrate_0" false false "(R=0.200000,G=0.800000,B=1.000000,A=1.000000)" 3.0)))
'''
def read(g):
    return json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'read_graph_dsl', 'arguments': {'graph': {'refPath': RM + ':' + g}}})).get('returnValue', '')
if __name__ == '__main__':
    for name, code in (('LoadShiftState', LOAD), ('SaveShiftState', SAVE)):
        if len(sys.argv) > 1 and name not in sys.argv[1:]: continue
        print(name, '->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':' + name}, 'code': code})[:400])
        print(read(name))
    print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:300])
