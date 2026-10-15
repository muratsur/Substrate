"""Phase 4 Step 5: Visual & Lighting Polish in L_SectorC."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

BF = '/Game/Substrate/Core/BP_Fixture.BP_Fixture'
MAP_REF = '/Game/Substrate/Maps/L_SectorC.L_SectorC'
PP_REF = f'{MAP_REF}:PersistentLevel.PostProcessVolume_1'
FOG_REF = f'{MAP_REF}:PersistentLevel.ExponentialHeightFog_1.HeightFogComponent0'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

def main():
    M.init()
    print('=== PHASE 4 - STEP 5: VISUAL & LIGHTING POLISH ===')

    # 1. Update BP_Fixture ConstructionScript for CatchLight LED
    CS = '''(fn ConstructionScript ()
  (bind cl (Variables|Default|GetCatchLight))
  (Utilities|IsValid cl
    (:"Is Valid"
      (Transformation|SetRelativeLocation cl (Math|Vector|MakeVector 0.0 20.0 10.0))
      (Rendering|Components|Light|SetIntensity cl 35.0)
      (Rendering|Components|Light|SetAttenuationRadius cl 140.0)
      (Rendering|Components|Light|SetLightColor cl (Math|Color|MakeColor 0.2 0.85 0.9 1.0) false))))
'''
    print('Writing BP_Fixture:UserConstructionScript...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{BF}:UserConstructionScript'}, 'code': balance(CS)})
    c_bf = M.bp('compile_blueprint', {'blueprint': {'refPath': BF}})
    print('  compile BP_Fixture ->', c_bf)

    # 2. Update PostProcessVolume_1 settings in L_SectorC
    print('Updating PostProcessVolume_1 settings...')
    pp_settings = {
        'Settings': {
            'bOverride_ColorOffsetShadows': True,
            'colorOffsetShadows': {'x': 0.015, 'y': 0.02, 'z': 0.025, 'w': 0.0},
            'bOverride_FilmToe': True,
            'filmToe': 0.62
        }
    }
    r_pp = M.call('call_tool', {
        'toolset_name': M.OBJ,
        'tool_name': 'set_properties',
        'arguments': {
            'instance': {'refPath': PP_REF},
            'values': json.dumps(pp_settings)
        }
    })
    print('  PostProcessVolume_1 updated:', r_pp)

    # 3. Update HeightFogComponent0 settings in L_SectorC
    print('Updating HeightFogComponent0 settings...')
    fog_settings = {
        'FogDensity': 0.22
    }
    r_fog = M.call('call_tool', {
        'toolset_name': M.OBJ,
        'tool_name': 'set_properties',
        'arguments': {
            'instance': {'refPath': FOG_REF},
            'values': json.dumps(fog_settings)
        }
    })
    print('  HeightFogComponent0 updated:', r_fog)

    # 4. Save assets
    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [BF]}})
    print('Step 5 Visual & Lighting Polish successfully applied and saved!')

if __name__ == '__main__':
    main()
