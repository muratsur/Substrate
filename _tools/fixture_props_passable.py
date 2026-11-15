"""Fixture props are solid (the user asked for that after trying walk-through props, 2026-11-14): ApplyFixtureState
enables actor collision for every fixture that is not missing. This script also rewords the airlock's lock hint, which
said "log the fixtures on this side first" even when every row was logged and one was logged wrong.
Check that no solid prop cuts its walkway with _tools/prop_lanes.py.
Usage: python _tools/fixture_props_passable.py   (PIE stopped), then save BP_Fixture and BP_Airlock."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
FX = '/Game/Substrate/Core/BP_Fixture.BP_Fixture'
AL = '/Game/Substrate/Core/BP_Airlock.BP_Airlock'
RMC = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager_C'
GRAPHS = {FX + ':ApplyFixtureState': '''(fn ApplyFixtureState (NewState)
  (bind _self self)
  (Variables|Default|SetFixtureState NewState)
  (Rendering|SetActorHiddenInGame _self (== NewState 2))
  (Collision|SetActorEnableCollision _self (!= NewState 2)))
''', AL + ':TryTransit': f'''(fn TryTransit ()
  (if (and (Variables|Default|GetInsideOK) (not (Variables|Default|GetDisarmed)))
    (CallFunction|GateOpen)
    (if (Variables|Default|GetGateOK)
      (CallFunction|Transit :Traveler (Game|GetPlayerPawn 0))
      (else
        (bind _returnvalue (Actor|GetActorOfClass "{RMC}"))
        (bind _asbp_round_manager (Utilities|Casting|CastToBP_RoundManager _returnvalue))
        (Class|BPRoundManager|ShowHint :self _asbp_round_manager :Text "AIRLOCK LOCKED - A ROW ON THIS SIDE IS UNLOGGED OR LOGGED WRONG")))))
'''}
read = lambda g: json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': g}})).get('returnValue', '')

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    for g, code in GRAPHS.items():
        before = read(g)
        assert before.startswith('(fn '), g + ' not found: is the editor on Substrate?'
        print(g.split(':')[-1], M.bp('write_graph_dsl', {'graph': {'refPath': g}, 'code': code})[:300])
        print(''.join(difflib.unified_diff(before.splitlines(True), read(g).splitlines(True), 'before', 'after')))
    for bp in (FX, AL):
        print(M.bp('compile_blueprint', {'blueprint': {'refPath': bp}})[:300])
