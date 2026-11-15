"""Walk the shift loop in Play-in-Editor without input: log each gate's rows by setting LogResult to the right value
(what E/Q would do), drop the pawn into each airlock and into the close-shift trigger, and report where it lands and
whether the round advances. Covers the parts no human has played: transit, the way back, closing at the dome console.
shortcut: logging is done by property, so the E/Q view test, the terminal and the title key choice are not exercised.
Usage: python _tools/pie_route_check.py   (PIE stopped; starts and stops its own session. A clean close runs the game's own save, so the editor's save slot can change)"""
import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
APP = 'EditorToolset.EditorAppToolset'
RMP = ['CurrentRound', 'ShiftOpen', 'AllCorrect', 'AuditMissedAnomaly', 'bIsOvertime']

def c(ts, t, a):
    r = M.call('call_tool', {'toolset_name': ts, 'tool_name': t, 'arguments': a})
    try: return json.loads(r).get('returnValue')
    except Exception: return r[:300]
def find(cls): return [a['refPath'] for a in (c(M.SCN, 'find_actors', {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': cls}}) or [])]
def get(ref, props):
    r = c(M.OBJ, 'get_properties', {'instance': {'refPath': ref}, 'properties': props})
    try: return json.loads(r)
    except Exception: return r
def loc(ref): return {k: round(v) for k, v in c(M.ACT, 'get_actor_transform', {'actor': {'refPath': ref}})['location'].items()}
def drop(pawn, at, dz=160):
    t = c(M.ACT, 'get_actor_transform', {'actor': {'refPath': pawn}})
    t['location'] = {'x': float(at['x']), 'y': float(at['y']), 'z': float(at['z'] + dz)}   # from above: spawning inside a trigger is not entering it
    c(M.ACT, 'set_actor_transform', {'actor': {'refPath': pawn}, 'xform': t}); time.sleep(3)
    return loc(pawn)

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    M.app('StartPIE', {'options': {'bSimulate': False}}); time.sleep(14)
    try:
        pawn = find('/Script/Engine.Character')[0]; rm = find('/Game/Substrate/Core/BP_RoundManager.BP_RoundManager_C')[0]
        assert 'UEDPIE_0_L_SectorC' in pawn, 'not Substrate'
        fx = {r: get(r, ['FixtureID', 'RowOrder', 'FixtureState', 'LogResult']) for r in find('/Game/Substrate/Core/BP_Fixture.BP_Fixture_C')}
        locks = {c(M.ACT, 'get_label', {'actor': {'refPath': r}}): r for r in find('/Game/Substrate/Core/BP_Airlock.BP_Airlock_C')}
        print('start', get(rm, RMP), 'pawn', loc(pawn))
        # the title needs a key press, so no shift is open: open one by flag (TryCloseShift only checks ShiftOpen)
        print('shift open', c(M.OBJ, 'set_properties', {'instance': {'refPath': rm}, 'values': json.dumps({'ShiftOpen': True})}))
        def log_rows(lo, hi):
            for r, p in fx.items():
                if lo <= p['RowOrder'] <= hi:
                    c(M.OBJ, 'set_properties', {'instance': {'refPath': r}, 'values': json.dumps({'LogResult': 1 if p['FixtureState'] == 0 else 2})})
        def gate(name, expect):
            at = loc(locks[name]); land = drop(pawn, at)
            moved = abs(land['x'] - at['x']) + abs(land['y'] - at['y']) > 300
            print(f"{name:24} at {at} -> pawn {land}  {'TRANSIT' if moved else 'stayed'} (expected {expect})  hint={get(rm, ['HintText'])}")
            return moved
        res = []
        res.append(('transit locked while sewer unlogged', not gate('Airlock_DockToTransit', 'stayed')))
        log_rows(0, 4);  res.append(('dock -> transit', gate('Airlock_DockToTransit', 'TRANSIT')))
        res.append(('return locked while transit unlogged', not gate('Airlock_TransitToDock', 'stayed')))
        log_rows(5, 7);  res.append(('transit -> dock', gate('Airlock_TransitToDock', 'TRANSIT')))
        res.append(('dock -> dome', gate('Airlock_DockToA', 'TRANSIT')))
        before = get(rm, RMP)
        land = drop(pawn, loc(rm)); mid = get(rm, RMP)
        print('console with dome rows unlogged ->', mid, 'pawn', land)
        res.append(('close refused while dome rows unlogged', mid.get('CurrentRound') == before.get('CurrentRound')))
        log_rows(9, 11)
        drop(pawn, {'x': 16000, 'y': 12000, 'z': 1000}, dz=120)   # step out of the trigger, then back in
        land = drop(pawn, loc(rm)); time.sleep(4); after = get(rm, RMP)
        print('console with every row logged ->', after, 'pawn', land)
        end = loc(pawn)   # from round 8 a clean close enters Sector D (arrival tube near -660, -8500) instead of raising the round
        print('pawn after close', end)
        res.append(('shift closes at the console', after.get('CurrentRound') != before.get('CurrentRound') or end['y'] < -5000))
        for name, ok in res: print(('PASS ' if ok else 'FAIL ') + name)
    finally:
        print('stop', M.app('StopPIE', {})[:60])
