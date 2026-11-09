"""Shift debrief reveals what changed (playtest 2026-11-08: two missing fixtures went unnoticed and nothing ever said
what they were). On a clean close the debrief now lists every anomaly applied this shift; sockets stay Applied until the
next StartShift reverts them, so ShowShiftDebrief can read them directly.
1. Rewrites each placed socket's Note as short terminal text ("C-03 PRESSURE GAUGE: MISSING"). Types 8 and 13 keep
   their Note: it is the fake checklist row they inject, so the debrief prints a generic line for them instead.
2. Adds BP_RoundManager.DebriefChanges (String) and CollectDebriefChanges(), and rewrites ShowShiftDebrief.
Usage: python _tools/debrief_reveal.py   (PIE stopped), then save L_SectorC (the notes live on placed sockets).
Re-runnable. Scripts that re-place sockets (fixture_sites.py, light_sites.py, ...) restore the old notes: run this after."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
import build_sector_a as A
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
SOCK = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C'
# old note prefix -> terminal text (the terminal fits ~30 characters a line)
TEXT = {
    'Absence: C-01': 'C-01 INLET VALVE: MISSING', 'Absence: C-02': 'C-02 FILTRATION SEAL: MISSING',
    'Absence: C-03': 'C-03 PRESSURE GAUGE: MISSING', 'Absence: C-04': 'C-04 OVERFLOW LAMP: MISSING',
    'Absence: C-05': 'C-05 OUTFALL GRATE: MISSING', 'Absence: B-01': 'B-01 COOLANT PUMP: MISSING',
    'Absence: B-02': 'B-02 HEAT EXCHANGER: MISSING', 'Absence: B-03': 'B-03 CONDENSER COIL: MISSING',
    'Absence: A-01': 'A-01 COMMS DESK: MISSING', 'Absence: A-02': 'A-02 GENERATOR: MISSING',
    'Absence: A-03': 'A-03 RATION SHELF: MISSING', 'Absence: the mug': 'DOME TABLE: MUG MISSING',
    'Light: the dock rect': 'DOCK LIGHT: DEAD', 'Light: the dome lamp': 'DOME LAMP: DEAD',
    'Light: the lamp over C-01': 'LAMP OVER C-01: DEAD', 'Light: the lamp over C-02': 'LAMP OVER C-02: DEAD',
    'Light: the lamp over C-05': 'LAMP OVER C-05: DEAD', 'Light: the transit light over B-01': 'LIGHT OVER B-01: DEAD',
    'Light: the transit light over B-02': 'LIGHT OVER B-02: DEAD', 'Light: the transit light over B-03': 'LIGHT OVER B-03: DEAD',
    'Growth:': 'SEWER GROWTH: SPREAD', 'Displacement: a dome stool': 'DOME STOOL: MOVED',
    'Displacement: C-02': 'C-02 FILTRATION SEAL: MOVED', 'Displacement: B-02': 'B-02 HEAT EXCHANGER: MOVED',
    'Displacement: C-05': 'C-05 OUTFALL GRATE: MOVED', 'Addition anomaly in Transit': 'TRANSIT: SOMETHING ADDED',
    'Addition: a second mug': 'DOME TABLE: SECOND MUG', 'Shadow anomaly near C-02': 'SHADOW NEAR C-02',
    'Geometry shift near C-04': 'WALLS SHIFTED NEAR C-04', 'Audio anomaly': 'SEWER HUM: STOPPED',
    'Repetition anomaly': 'TRANSIT AIRLOCK: LOOPED', 'Doppelg': 'FIGURE IN TRANSIT',
    'Hyper-Growth': 'SPORE BLOOM', 'Phantom Shadow': 'SHADOW ON THE WALL'}
KEEP = (8, 13)   # Note is the injected checklist row

COLLECT = '''(fn CollectDebriefChanges ()
  (Variables|Default|SetDebriefChanges "")
  (bind _outactors (Actor|GetAllActorsOfClass "%s"))
  (for _array_element _outactors
    (bind _asbp_anomaly_socket (Utilities|Casting|CastToBP_AnomalySocket _array_element))
    (if (Class|BPAnomalySocket|GetApplied _asbp_anomaly_socket)
      (Variables|Default|SetDebriefChanges (Utilities|String|Append (Variables|Default|GetDebriefChanges) (Utilities|String|Append (Utilities|String|Append "- " (select (== (Class|BPAnomalySocket|GetAnomalyType _asbp_anomaly_socket) 8) "CHECKLIST: ROW CORRUPTED" (select (== (Class|BPAnomalySocket|GetAnomalyType _asbp_anomaly_socket) 13) "CHECKLIST: EXTRA ROW" (Class|BPAnomalySocket|GetNote _asbp_anomaly_socket)))) (Variables|Default|GetNL))))))
  (if (== (Utilities|String|Len (Variables|Default|GetDebriefChanges)) 0)
    (Variables|Default|SetDebriefChanges (Utilities|String|Append "- NOTHING" (Variables|Default|GetNL)))))
''' % SOCK

SHOW = '''(fn ShowShiftDebrief ()
  (Variables|Default|SetShiftOpen false)
  (CallFunction|CollectDebriefChanges)
  (bind _debrief_round (Variables|Default|GetCurrentRound))
  (bind _debrief_round_padded (Utilities|String|Append (select (< _debrief_round 10) "00" (select (< _debrief_round 100) "0" "")) (Utilities|String|ToString(Integer) _debrief_round)))
  (bind _debrief_head (Utilities|String|Append (Utilities|String|Append "SHIFT " _debrief_round_padded) (Utilities|String|Append " - AUDIT PASSED" (Variables|Default|GetNL))))
  (bind _debrief_changes (Utilities|String|Append (Utilities|String|Append "WHAT CHANGED THIS SHIFT:" (Variables|Default|GetNL)) (Variables|Default|GetDebriefChanges)))
  (bind _debrief_counts (Utilities|String|Append (Utilities|String|Append "CATALOGUED: " (Utilities|String|ToString(Integer) (Variables|Default|GetDiscoveredCount))) (Utilities|String|Append (Utilities|String|Append " / 14" (Variables|Default|GetNL)) (Utilities|String|Append "CONTAMINATION: " (Utilities|String|ToString(Integer) (Variables|Default|GetContamination))))))
  (bind _debrief_lines (Utilities|String|Append (Utilities|String|Append _debrief_head _debrief_changes) _debrief_counts))
  (bind _debrief_footer (Utilities|String|Append "NEXT SHIFT: " (select (>= (Variables|Default|GetContamination) 4) "WEST + EAST CROSSINGS AT RISK" (select (>= (Variables|Default|GetContamination) 2) "WEST CROSSING AT RISK" "ROUTES STABLE"))))
  (CallFunction|PushTerminal self "SHIFT DEBRIEF" _debrief_lines "" _debrief_footer)
  (CallFunction|RaiseTerminal)
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ContinueAfterDebrief" :Time 12.0 :bLooping false))
'''

def text_for(note):
    for k, v in TEXT.items():
        if note.startswith(k): return v

def check(r, what):
    if any(m in str(r).lower() for m in ('"iserror": true', '"iserror":true', 'does not exist', 'could not', 'traceback', 'cannot rebind', 'assertionerror')):
        raise SystemExit(f'{what} failed, nothing saved:\n{str(r)[:1200]}')

def read(g):
    return json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': f'{RM}:{g}'}})).get('returnValue', '')

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    # 1. socket notes
    socks = A.call(M.SCN, 'find_actors', {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': SOCK}})
    for s in socks:
        p = json.loads(A.call(M.OBJ, 'get_properties', {'instance': s, 'properties': ['anomalyType', 'note']}))
        if p['anomalyType'] in KEEP: continue
        new = text_for(p['note'])
        if new is None:
            if p['note'] not in TEXT.values(): print('  no text for', repr(p['note']), '- left as is')
            continue
        A.call(M.OBJ, 'set_properties', {'instance': s, 'values': json.dumps({'note': new})})
        got = json.loads(A.call(M.OBJ, 'get_properties', {'instance': s, 'properties': ['note']}))['note']
        assert got == new, (p['note'], got)
    print('socket notes rewritten')
    # 2. Round Manager
    vars_ = M.bp('list_variables', {'blueprint': {'refPath': RM}})
    if 'DebriefChanges' not in vars_:
        check(M.bp('add_variable', {'blueprint': {'refPath': RM}, 'name': 'DebriefChanges', 'type_name': 'string'}), 'add DebriefChanges')
    graphs = [g['refPath'].split(':')[-1] for g in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': RM}}))['returnValue']]
    if 'CollectDebriefChanges' not in graphs:
        check(M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': 'CollectDebriefChanges'}), 'add CollectDebriefChanges')
    for g, code, must in (('CollectDebriefChanges', COLLECT, ('GetApplied', 'SetDebriefChanges', 'ROW CORRUPTED')),
                          ('ShowShiftDebrief', SHOW, ('CollectDebriefChanges', 'WHAT CHANGED', 'ContinueAfterDebrief'))):
        check(M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:{g}'}, 'code': code}), 'write ' + g)
        back = read(g)
        missing = [m for m in must if m not in back]
        if missing: raise SystemExit(f'{g} readback missing {missing}; nothing saved')
        print(g, 'written and read back')
    r = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('compile:', r[:300])
    check(r, 'compile')
    print('save RM:', M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM]}})[:100])
