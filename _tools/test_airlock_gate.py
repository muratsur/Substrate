"""A/B test the airlock gate, without pressing E/Q.

  mode "log"     - write the correct LogResult on every fixture in the gate's row range
                   (exactly what E/Q write)  -> expect the gate to Transit the pawn
  mode "control" - write LogResult 0 (nothing logged) -> expect the gate to refuse and
                   print "Airlock locked"

Run:  python _tools/test_airlock_gate.py [log|control] [0|1]
"""
import sys
import json
import time
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
MODE = sys.argv[1] if len(sys.argv) > 1 else 'log'
WHICH = int(sys.argv[2]) if len(sys.argv) > 2 else 0
GATES = [(0, 4, 'BP_Airlock_C_0', 'BP_Airlock_C_1', (300, 1400, 420), (8560, 4520, 420)),
         (5, 7, 'BP_Airlock_C_1', 'BP_Airlock_C_0', (8560, 4520, 420), (300, 1400, 420))]
LO, HI, HERE, OTHER, HERE_XY, OTHER_XY = GATES[WHICH]
OUT_XY = (-2500, 1400, 450) if HERE_XY[1] < 5000 else (-2500, 8000, 450)


def find(cls):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                             'arguments': {'name': '', 'tag': '', 'collision_channels': [],
                                           'actor_type': {'refPath': cls}}})
    try:
        return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception:
        return []


def prop(ref, key):
    r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'get_properties',
                             'arguments': {'instance': {'refPath': ref}, 'properties': [key]}})
    try:
        v = json.loads(r)['returnValue']
        d = json.loads(v) if isinstance(v, str) else v
        return d.get(key)
    except Exception:
        return None


def setp(ref, values):
    return M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties',
                                'arguments': {'instance': {'refPath': ref},
                                              'values': json.dumps(values)}})[:60]


def put(ref, xyz):
    M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
                         'arguments': {'actor': {'refPath': ref},
                                       'xform': {'location': {'x': float(xyz[0]), 'y': float(xyz[1]),
                                                              'z': float(xyz[2])}}}})


def loc(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
                             'arguments': {'actor': {'refPath': ref}}})
    try:
        v = json.loads(r)['returnValue']['location']
        return (round(v['x']), round(v['y']), round(v['z']))
    except Exception:
        return None


def user_log(pat=''):
    r = M.call('call_tool', {'toolset_name': 'EditorToolset.LogsToolset', 'tool_name': 'GetLogEntries',
                             'arguments': {'category': 'LogBlueprintUserMessages', 'pattern': pat}})
    try:
        return json.loads(r)['returnValue']
    except Exception:
        return []


def gate_policy():
    """'open' when GateOpen has the free-roam patch, else 'gated'."""
    try:
        dsl = json.loads(M.bp('read_graph_dsl', {'graph': {
            'refPath': '/Game/Substrate/Core/BP_Airlock.BP_Airlock:GateOpen'}}))['returnValue']
    except Exception:
        return 'unknown'
    # free-roam patch = SetGateOK true at the top AND again after the loop, with no SetGateOK false
    return 'open' if (dsl.count('SetGateOK true') >= 2 and 'SetGateOK false' not in dsl) else 'gated'


M.init()
POLICY = gate_policy()
print('gate policy: %s' % POLICY)
if 'true' not in M.app('IsPIERunning', {}):
    M.app('StartPIE', {'options': {'bSimulate': False}})
    time.sleep(12)
pawn = (find('/Script/Engine.Character') or [None])[0]
if not pawn:
    sys.exit('no pawn in PIE')
print('MODE=%s  gate %s (rows %d-%d) -> %s' % (MODE, HERE, LO, HI, OTHER))

print('--- fixture LogResult writes ---')
for f in find('/Game/Substrate/Core/BP_Fixture.BP_Fixture_C'):
    row, state = prop(f, 'RowOrder'), prop(f, 'FixtureState')
    if row is None or not (LO <= row <= HI):
        continue
    if MODE == 'control':
        want = 0
    else:
        want = 1 if state == 0 else 2      # IsLoggedCorrectly: PASS if healthy, else FLAG
    setp(f, {'LogResult': want})
    print('  row %-2s %-22s state=%s -> LogResult=%d' % (row, f.split(':')[-1], state, want))

print('--- pawn walk: in, out, in ---')
put(pawn, HERE_XY)
time.sleep(2.5)
first = loc(pawn)
print('  first entry :', first)
if first and abs(first[0] - OTHER_XY[0]) < 400 and abs(first[1] - OTHER_XY[1]) < 400:
    put(pawn, OUT_XY)              # already transited; go back to the original side to re-test
    time.sleep(2.0)
put(pawn, OUT_XY)
time.sleep(2.0)
print('  stepped out :', loc(pawn))
put(pawn, HERE_XY)
time.sleep(3.0)
p = loc(pawn)
print('  second entry:', p)

transited = bool(p) and abs(p[0] - OTHER_XY[0]) < 400 and abs(p[1] - OTHER_XY[1]) < 400
stayed = bool(p) and abs(p[0] - HERE_XY[0]) < 400 and abs(p[1] - HERE_XY[1]) < 400
print()
if MODE == 'control':
    locked = [l for l in user_log() if 'Airlock locked' in l]
    print('last locked message: %s' % (locked[-1][:150] if locked else 'none'))
    if POLICY == 'open':
        print('RESULT: %s' % ('PASS - gate is open (transits with nothing logged), as intended by the free-roam patch'
                              if transited else 'FAIL - gate is patched open but the pawn did not transit'))
    else:
        print('RESULT: %s' % ('PASS - gate refused to open with nothing logged (still gated)' if stayed
                              else 'FAIL - gate opened with nothing logged'))
else:
    print('RESULT: %s' % ('PASS - gate transited the pawn' if transited
                          else 'FAIL - pawn stayed at %s' % (p,)))
print('recent user messages:')
for l in user_log()[-5:]:
    print('   ', l[:160])
