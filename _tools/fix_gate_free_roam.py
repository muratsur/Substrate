"""Open the tunnel gate: make BP_Airlock always let the player through.

GateOpen() is the only place GateOK is computed:
    SetGateOK true; SetPending 0
    for each fixture: if it is in this gate's row range AND not logged correctly -> SetGateOK false
and the overlap handler transits the player only when GateOK is true.

This keeps all of that and simply forces GateOK true at the end of GateOpen, so the gate opens
without the fixture logging ritual.  The original graph is stored below and restored verbatim by
`revert`.

Run:  python _tools/fix_gate_free_roam.py            (open the gate)
      python _tools/fix_gate_free_roam.py revert     (restore the gate rule)
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

A = '/Game/Substrate/Core/BP_Airlock.BP_Airlock'

ORIGINAL = '''(fn GateOpen ()
  (Variables|Default|SetGateOK true)
  (Variables|Default|SetPending 0)
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _array_element _outactors
    (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
    (bind _inrange (Class|BPFixture|InRowRange _asbp_fixture (Variables|Default|GetGateRowMin) (Variables|Default|GetGateRowMax)))
    (bind _correct (Class|BPFixture|IsLoggedCorrectly _asbp_fixture))
    (if (and _inrange (not _correct))
      (Variables|Default|SetGateOK false)
      (Variables|Default|SetPending (+ (Variables|Default|GetPending) 1)))))
'''

PATCHED = '''(fn GateOpen ()
  ; FREE ROAM: gate does not require the fixtures to be logged (revert: fix_gate_free_roam.py revert)
  (Variables|Default|SetGateOK true)
  (Variables|Default|SetPending 0)
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _array_element _outactors
    (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture _array_element))
    (bind _inrange (Class|BPFixture|InRowRange _asbp_fixture (Variables|Default|GetGateRowMin) (Variables|Default|GetGateRowMax)))
    (bind _correct (Class|BPFixture|IsLoggedCorrectly _asbp_fixture))
    (if (and _inrange (not _correct))
      (Variables|Default|SetPending (+ (Variables|Default|GetPending) 1))
      (Variables|Default|SetPending (+ (Variables|Default|GetPending) 1))))
  (Variables|Default|SetGateOK true))
'''

M.init()
revert = len(sys.argv) > 1 and sys.argv[1] == 'revert'
code = ORIGINAL if revert else PATCHED
print('PIE:', M.app('IsPIERunning', {})[:40])
print('writing %s GateOpen...' % ('the original' if revert else 'the free-roam'))
print('  write:', str(M.bp('write_graph_dsl', {'graph': {'refPath': A + ':GateOpen'},
                                              'code': code}))[:120])
print('  compile:', str(M.bp('compile_blueprint', {'blueprint': {'refPath': A}}))[:120])
print('  save   :', M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                                        'arguments': {'asset_paths': [A]}})[:80])
print('=== GateOpen now ===')
print(json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': A + ':GateOpen'}}))['returnValue'])
