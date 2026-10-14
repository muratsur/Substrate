"""Toggle the canal rescue teleportation in BP_CanalRescue.

Usage:
  python _tools/toggle_canal_rescue.py disable   (disconnects overlap teleport)
  python _tools/toggle_canal_rescue.py enable    (reconnects overlap teleport)
  python _tools/toggle_canal_rescue.py status    (checks whether enabled)
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

BPC = '/Game/Substrate/Core/BP_CanalRescue.BP_CanalRescue'
GRAPH = BPC + ':EventGraph'
OUT_PIN = {'direction': 'EGPD_Output', 'index_id': 1, 'node': {'refPath': GRAPH + '.K2Node_Event_1'}}
IN_PIN = {'direction': 'EGPD_Input', 'index_id': 0, 'node': {'refPath': GRAPH + '.K2Node_IfThenElse_0'}}

M.init()
cmd = sys.argv[1].lower() if len(sys.argv) > 1 else 'status'

if cmd == 'disable':
    M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'break_pins',
                         'arguments': {'output_pin': OUT_PIN, 'input_pin': IN_PIN}})
    M.bp('compile_blueprint', {'blueprint': {'refPath': BPC}})
    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                         'arguments': {'asset_paths': [BPC]}})
    print('Canal rescue teleport: DISABLED')

elif cmd == 'enable':
    M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'connect_pins',
                         'arguments': {'output_pin': OUT_PIN, 'input_pin': IN_PIN}})
    M.bp('compile_blueprint', {'blueprint': {'refPath': BPC}})
    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                         'arguments': {'asset_paths': [BPC]}})
    print('Canal rescue teleport: ENABLED')

dsl = json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'read_graph_dsl',
                                      'arguments': {'graph': {'refPath': GRAPH}}}))['returnValue']
enabled = 'SetActorLocation' in dsl and 'EventActorBeginOverlap' in dsl
print('Current BP_CanalRescue status:', 'ENABLED' if enabled else 'DISABLED')
