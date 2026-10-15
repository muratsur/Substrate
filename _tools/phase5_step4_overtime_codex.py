"""Phase 5 Step 4: Overtime Codex & Steam Achievement Hooks.

1. Expanded Codex Bitmask:
   - Extend career anomaly catalog from 10 bits to 16 bits to accommodate Codes 10 through 15 (Tier-2 variants).
2. Steam Achievement Integration:
   - ACH_OVERTIME_START: Complete your first Overtime Shift (OT-01).
   - ACH_OVERTIME_VETERAN: Reach Overtime Shift OT-05.
   - ACH_MASTER_AUDITOR: Catalog all 16 Anomaly Codes (Standard + Tier-2 variants).
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
EG = f'{RM}:EventGraph'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

def ensure_fns(bp_path, fns):
    graphs = [g['refPath'].split(':')[-1] for g in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': bp_path}})).get('returnValue', [])]
    for fn in fns:
        if fn not in graphs:
            print(f'Adding function {fn} to {bp_path}...')
            M.bp('add_function_graph', {'blueprint': {'refPath': bp_path}, 'graph_name': fn})

def wire_achievement_event(event_name, ach_name, y_pos):
    print(f'Wiring achievement event {event_name} -> {ach_name} at y={y_pos}...')
    ev = json.loads(M.bp('add_event', {'blueprint': {'refPath': RM}, 'event_name': event_name, 'position': {'x': 1000, 'y': y_pos}}))['returnValue']
    wp = json.loads(M.bp('create_node', {'graph': {'refPath': EG}, 'type_id': 'Online|Achievements|WriteProgress', 'pos': {'x': 1400, 'y': y_pos}}))['returnValue']
    pc = json.loads(M.bp('create_node', {'graph': {'refPath': EG}, 'type_id': 'Game|GetPlayerController', 'pos': {'x': 1150, 'y': y_pos + 100}}))['returnValue']

    ev_info = json.loads(M.bp('get_node_infos', {'nodes': [ev]}))['returnValue'][0]
    wp_info = json.loads(M.bp('get_node_infos', {'nodes': [wp]}))['returnValue'][0]
    pc_info = json.loads(M.bp('get_node_infos', {'nodes': [pc]}))['returnValue'][0]

    ev_then = [p for p in ev_info['output_pins'] if p['name'] == 'then'][0]
    wp_exec = [p for p in wp_info['input_pins'] if p['name'] == 'execute'][0]
    wp_name = [p for p in wp_info['input_pins'] if p['name'] == 'AchievementName'][0]
    wp_prog = [p for p in wp_info['input_pins'] if p['name'] == 'Progress'][0]
    wp_pc = [p for p in wp_info['input_pins'] if p['name'] == 'PlayerController'][0]
    pc_ret = [p for p in pc_info['output_pins'] if p['name'] == 'ReturnValue'][0]

    M.bp('connect_pins', {'output_pin': ev_then['pin_id'], 'input_pin': wp_exec['pin_id']})
    M.bp('connect_pins', {'output_pin': pc_ret['pin_id'], 'input_pin': wp_pc['pin_id']})
    M.bp('set_pin_value', {'pin': wp_name['pin_id'], 'value': ach_name})
    M.bp('set_pin_value', {'pin': wp_prog['pin_id'], 'value': '100.0'})
    print(f'  wired {ach_name} successfully.')

def main():
    M.init()
    print('=== PHASE 5 - STEP 4: OVERTIME CODEX & STEAM ACHIEVEMENTS ===')

    ensure_fns(RM, ['CheckSteamAchievements', 'RecordDiscoveredAnomalies'])

    # 1. Wire the 3 Achievement events in EventGraph
    wire_achievement_event('UnlockAchOvertimeStart', 'ACH_OVERTIME_START', 2500)
    wire_achievement_event('UnlockAchOvertimeVeteran', 'ACH_OVERTIME_VETERAN', 2800)
    wire_achievement_event('UnlockAchMasterAuditor', 'ACH_MASTER_AUDITOR', 3100)

    # 2. Write CheckSteamAchievements
    CHECK_ACH = '''(fn CheckSteamAchievements ()
  (bind ot (Variables|Default|GetOvertimeShift))
  (bind cnt (Variables|Default|GetDiscoveredCount))
  (bind isot (Variables|Default|GetIsOvertime))
  (if isot
    (if (>= ot 1)
      (CallFunction|UnlockAchOvertimeStart self)
      (Development|PrintString "ACHIEVEMENT: ACH_OVERTIME_START (OT-01 Completed)" true true "(R=0.200000,G=1.000000,B=0.500000,A=1.000000)" 6.0))
    (if (>= ot 5)
      (CallFunction|UnlockAchOvertimeVeteran self)
      (Development|PrintString "ACHIEVEMENT: ACH_OVERTIME_VETERAN (OT-05 Reached)" true true "(R=0.200000,G=1.000000,B=0.500000,A=1.000000)" 6.0)))
  (if (>= cnt 16)
    (CallFunction|UnlockAchMasterAuditor self)
    (Development|PrintString "ACHIEVEMENT: ACH_MASTER_AUDITOR (All 16 Anomaly Codes Catalogued!)" true true "(R=0.200000,G=1.000000,B=0.500000,A=1.000000)" 8.0)))
'''
    print('Writing BP_RoundManager:CheckSteamAchievements...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:CheckSteamAchievements'}, 'code': balance(CHECK_ACH)})

    # 3. Update RecordDiscoveredAnomalies to support full 16-bit catalog
    RECORD_16BIT = '''(fn RecordDiscoveredAnomalies ()
  (bind socks (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C"))
  (for s socks
    (bind sock (Utilities|Casting|CastToBP_AnomalySocket s)
      (:then
        (if (Class|BPAnomalySocket|GetApplied sock)
          (bind code (Class|BPAnomalySocket|GetAnomalyType sock))
          (if (and (>= code 0) (<= code 15))
            (bind bit (Math|Integer|bit_shift_left 1 code))
            (if (== (Math|Integer|bit_and (Variables|Default|GetDiscoveredMask) bit) 0)
              (Variables|Default|SetDiscoveredMask (Math|Integer|bit_or (Variables|Default|GetDiscoveredMask) bit))
              (Variables|Default|SetDiscoveredCount (+ (Variables|Default|GetDiscoveredCount) 1))))))
      (:CastFailed)))
  (CallFunction|CheckSteamAchievements))
'''
    print('Writing BP_RoundManager:RecordDiscoveredAnomalies (16-bit codex)...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:RecordDiscoveredAnomalies'}, 'code': balance(RECORD_16BIT)})

    print('Compiling BP_RoundManager...')
    c_rm = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('  compile BP_RoundManager ->', c_rm[:150])

    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM]}})
    print('Step 4 Overtime Codex & Steam Achievements completed successfully!')

if __name__ == '__main__':
    main()
