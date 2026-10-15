"""Step 8: Lighting & Exposure polish on Transit & Start (Defect D6)."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

def main():
    M.init()
    base = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
    
    # Target lights and their new intensities (80..150 cd)
    targets = {
        'PointLight_1': 120.0,
        'PointLight_2': 120.0,
        'PointLight_3': 120.0,
        'PointLight_5': 90.0,
    }

    for name, intensity in targets.items():
        actor_ref = base + name
        # Find light component
        comps_r = M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_components',
                                       'arguments': {'actor': {'refPath': actor_ref}}})
        comps = json.loads(comps_r).get('returnValue', [])
        lc = [c['refPath'] for c in comps if 'Light' in c['refPath']][0]
        
        # Set intensity
        r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties',
                                 'arguments': {'instance': {'refPath': lc},
                                               'values': json.dumps({'Intensity': intensity})}})
        print(f'Set {name} intensity -> {intensity} cd ({r[:60]})')

    # Save level
    print('Saving level L_SectorC...')
    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                             'arguments': {'asset_paths': ['/Game/Substrate/Maps/L_SectorC']}})
    print('save level ->', s[:100])

if __name__ == '__main__':
    main()
