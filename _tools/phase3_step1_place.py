"""Phase 3 Step 1: Place Anomaly Sites for Codes 4..9 in L_SectorC."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

BASE = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
SOCKCLASS = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C'
FOLDER = 'Substrate/Anomalies'

def spawn_class(actor_type, name, loc, scale=(1, 1, 1)):
    r = M.call('call_tool', {
        'toolset_name': M.SCN,
        'tool_name': 'add_to_scene_from_class',
        'arguments': {
            'actor_type': {'refPath': actor_type},
            'name': name,
            'xform': {
                'location': {'x': loc[0], 'y': loc[1], 'z': loc[2]},
                'scale': {'x': scale[0], 'y': scale[1], 'z': scale[2]}
            }
        }
    })
    print('  spawn class', name, r[:140])
    try:
        return json.loads(r)['returnValue']['refPath']
    except Exception:
        return None

def spawn_asset(asset_path, name, loc, scale=(1, 1, 1)):
    r = M.call('call_tool', {
        'toolset_name': M.SCN,
        'tool_name': 'add_to_scene_from_asset',
        'arguments': {
            'asset_path': asset_path,
            'name': name,
            'xform': {
                'location': {'x': loc[0], 'y': loc[1], 'z': loc[2]},
                'scale': {'x': scale[0], 'y': scale[1], 'z': scale[2]}
            }
        }
    })
    print('  spawn asset', name, r[:140])
    try:
        return json.loads(r)['returnValue']['refPath']
    except Exception:
        return None

def set_props(ref, values):
    r = M.call('call_tool', {
        'toolset_name': M.OBJ,
        'tool_name': 'set_properties',
        'arguments': {'instance': {'refPath': ref}, 'values': json.dumps(values)}
    })
    print('   set', ref.split('.')[-1], r[:120])

def set_label(ref, label):
    M.call('call_tool', {
        'toolset_name': M.ACT,
        'tool_name': 'set_label',
        'arguments': {'actor': {'refPath': ref}, 'label': label}
    })

def set_folder(ref, folder):
    M.call('call_tool', {
        'toolset_name': M.SCN,
        'tool_name': 'set_actor_folder',
        'arguments': {'actor': {'refPath': ref}, 'folder_path': folder}
    })

def main():
    M.init()
    print('--- Step 1: Authoring Anomaly Sites for Codes 4..9 ---')

    # 1. Site A: Code 5 (Shadow)
    print('1. Setting up Site A: Shadow C-02...')
    shadow_mesh = '/Game/Alien_Biomass/Meshes/Alien_organism/SM_alien_organism_05'
    shadow_caster = spawn_asset(shadow_mesh, 'ShadowCaster_C2', (2920, 6100, 390), (0.6, 0.6, 0.8))
    if shadow_caster:
        set_label(shadow_caster, 'ShadowCaster_C2')
        set_folder(shadow_caster, FOLDER)
        # Actor Hidden In Game, Cast Shadow true, Cast Hidden Shadow false, Collision false
        set_props(shadow_caster, {
            'bHidden': True,
            'bActorEnableCollision': False
        })
        comp_ref = shadow_caster + '.StaticMeshComponent0'
        set_props(comp_ref, {
            'CastShadow': True,
            'bCastHiddenShadow': False
        })

    sock_shadow = spawn_class(SOCKCLASS, 'Socket_Shadow_C2', (3000, 6150, 430))
    if sock_shadow:
        set_label(sock_shadow, 'Socket_Shadow_C2')
        set_folder(sock_shadow, FOLDER)
        set_props(sock_shadow, {
            'anomalyType': 5,
            'minRound': 3,
            'maxRound': 0,
            'cooldownRounds': 3,
            'revertRule': 0,
            'severity': 1.0,
            'note': 'Shadow anomaly near C-02',
            'targetActor': {'refPath': shadow_caster or (BASE + 'ShadowCaster_C2')}
        })

    # 2. Site B: Code 4 (Addition)
    print('2. Setting up Site B: Addition Transit...')
    add_mesh = '/Game/Modular_Sewer_Kit/Meshes/Details/SM_detail_03'
    add_prop = spawn_asset(add_mesh, 'AdditionProp_Transit', (8420, 3680, 320))
    if add_prop:
        set_label(add_prop, 'AdditionProp_Transit')
        set_folder(add_prop, FOLDER)
        set_props(add_prop, {
            'bHidden': True,
            'bActorEnableCollision': False
        })

    sock_add = spawn_class(SOCKCLASS, 'Socket_Addition_Transit', (8560, 3680, 450))
    if sock_add:
        set_label(sock_add, 'Socket_Addition_Transit')
        set_folder(sock_add, FOLDER)
        set_props(sock_add, {
            'anomalyType': 4,
            'minRound': 4,
            'maxRound': 0,
            'cooldownRounds': 3,
            'revertRule': 0,
            'severity': 1.0,
            'note': 'Addition anomaly in Transit',
            'targetActor': {'refPath': add_prop or (BASE + 'AdditionProp_Transit')}
        })

    # 3. Site C: Code 6 (Geometry)
    print('3. Setting up Site C: Geometry C-04...')
    geom_mesh = '/Game/Modular_Sewer_Kit/Meshes/Modules/Walls/SM_pillar'
    geom_norm = spawn_asset(geom_mesh, 'GeomNormal_C4', (-1516, 8000, 300))
    if geom_norm:
        set_label(geom_norm, 'GeomNormal_C4')
        set_folder(geom_norm, FOLDER)
        set_props(geom_norm, {
            'bHidden': False,
            'bActorEnableCollision': True
        })

    geom_shift = spawn_asset(geom_mesh, 'GeomShifted_C4', (-1516, 7820, 300), (1.0, 1.25, 1.0))
    if geom_shift:
        set_label(geom_shift, 'GeomShifted_C4')
        set_folder(geom_shift, FOLDER)
        set_props(geom_shift, {
            'bHidden': True,
            'bActorEnableCollision': False
        })

    sock_geom = spawn_class(SOCKCLASS, 'Socket_Geometry_C4', (-1516, 8000, 420))
    if sock_geom:
        set_label(sock_geom, 'Socket_Geometry_C4')
        set_folder(sock_geom, FOLDER)
        set_props(sock_geom, {
            'anomalyType': 6,
            'minRound': 6,
            'maxRound': 0,
            'cooldownRounds': 4,
            'revertRule': 0,
            'severity': 1.0,
            'note': 'Geometry shift near C-04',
            'targetActor': {'refPath': geom_norm or (BASE + 'GeomNormal_C4')},
            'secondaryActor': {'refPath': geom_shift or (BASE + 'GeomShifted_C4')}
        })

    # 4. Site D: Code 7 (Audio)
    print('4. Setting up Site D: Audio Sewer Silence...')
    sock_audio = spawn_class(SOCKCLASS, 'Socket_Audio_SewerSilence', (0, 3000, 430))
    if sock_audio:
        set_label(sock_audio, 'Socket_Audio_SewerSilence')
        set_folder(sock_audio, FOLDER)
        set_props(sock_audio, {
            'anomalyType': 7,
            'minRound': 4,
            'maxRound': 0,
            'cooldownRounds': 4,
            'revertRule': 0,
            'severity': 1.0,
            'note': 'Audio anomaly: sewer room tone stopped',
            'targetActor': {'refPath': BASE + 'AmbientSound_0'}
        })

    # 5. Site E: Code 8 (Checklist Corruption)
    print('5. Setting up Site E: Checklist Corruption C-03...')
    sock_check = spawn_class(SOCKCLASS, 'Socket_Checklist_C3', (-2480, 7212, 460))
    if sock_check:
        set_label(sock_check, 'Socket_Checklist_C3')
        set_folder(sock_check, FOLDER)
        set_props(sock_check, {
            'anomalyType': 8,
            'minRound': 6,
            'maxRound': 0,
            'cooldownRounds': 4,
            'revertRule': 0,
            'severity': 1.0,
            'note': 'C-03 DO NOT INSPECT',
            'targetActor': {'refPath': BASE + 'BP_Fixture_C_2'}
        })

    # 6. Site F: Code 9 (Airlock Repetition)
    print('6. Setting up Site F: Airlock Repetition...')
    sock_rep = spawn_class(SOCKCLASS, 'Socket_Repetition_TransitAirlock', (8560, 4520, 480))
    if sock_rep:
        set_label(sock_rep, 'Socket_Repetition_TransitAirlock')
        set_folder(sock_rep, FOLDER)
        set_props(sock_rep, {
            'anomalyType': 9,
            'minRound': 6,
            'maxRound': 0,
            'cooldownRounds': 5,
            'revertRule': 0,
            'severity': 1.0,
            'note': 'Repetition anomaly: Transit airlock looped',
            'targetActor': {'refPath': BASE + 'BP_Airlock_C_1'}
        })

    print('Saving level and assets...')
    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}})
    print('save dirty ->', s[:100])

if __name__ == '__main__':
    main()
