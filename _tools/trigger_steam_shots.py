"""Trigger steam shots sequence in PIE."""
import sys
import json
import time
import os
import glob
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
EG = {'refPath': RM + ':EventGraph'}
ENABLE_INPUT = f'{RM}:EventGraph.K2Node_CallFunction_51'

def add_hook():
    print('Connecting RunSteamCapture timer to EnableInput...')
    # Create timer node
    r_t = M.bp('create_node', {
        'graph': EG,
        'type_id': 'Utilities|Time|SetTimerbyFunctionName',
        'pos': {'x': 800, 'y': 0}
    })
    t_ref = json.loads(r_t)['returnValue']['refPath']
    info = json.loads(M.bp('get_node_infos', {'nodes': [{'refPath': t_ref}, {'refPath': ENABLE_INPUT}]}))['returnValue']
    ti = [i for i in info if i['node']['refPath'] == t_ref][0]
    ei = [i for i in info if i['node']['refPath'] == ENABLE_INPUT][0]

    # Set parameters on timer node
    for p in ti['input_pins']:
        if p['name'] == 'FunctionName':
            M.bp('set_pin_value', {'pin': p['pin_id'], 'value': 'RunSteamCapture'})
        elif p['name'] == 'Time':
            M.bp('set_pin_value', {'pin': p['pin_id'], 'value': '3.0'})
        elif p['name'] == 'bLooping':
            M.bp('set_pin_value', {'pin': p['pin_id'], 'value': 'false'})

    # Connect EnableInput then -> Timer execute
    e_then = [p for p in ei['output_pins'] if p['name'] == 'then'][0]
    t_exec = [p for p in ti['input_pins'] if p['type_id'] == 'Exec'][0]
    M.bp('connect_pins', {'output_pin': e_then['pin_id'], 'input_pin': t_exec['pin_id']})

    c = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('compile RM ->', c[:100])
    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM]}})
    return t_ref

def remove_hook(t_ref):
    print(f'Removing timer hook {t_ref}...')
    M.bp('delete_node', {'node': {'refPath': t_ref}})
    M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM]}})

def main():
    M.init()
    # 1. Add hook
    t_ref = add_hook()

    # 2. Start PIE
    print('Starting PIE for Steam Screenshot capture...')
    M.app('StartPIE', {'options': {'bSimulate': False}})

    # 3. Wait for the 6 shots (3s delay + 6 * 1.5s = ~12s total)
    print('Waiting 18 seconds for shots sequence...')
    for i in range(18):
        time.sleep(1)
        shots = glob.glob('Saved/Screenshots/WindowsEditor/*.png')
        print(f'  second {i+1}: {len(shots)} screenshots found')
        if len(shots) >= 6:
            time.sleep(2)
            break

    # 4. Stop PIE
    print('Stopping PIE...')
    M.app('StopPIE', {})
    time.sleep(4)

    # 5. Remove hook
    remove_hook(t_ref)

    # 6. Report results
    shots = sorted(glob.glob('Saved/Screenshots/WindowsEditor/*.png'))
    print(f'Done! Total screenshots captured: {len(shots)}')
    for s in shots:
        print(' ', s, os.path.getsize(s), 'bytes')

if __name__ == '__main__':
    main()
