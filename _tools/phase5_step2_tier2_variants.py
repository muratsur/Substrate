"""Phase 5 Step 2: Rare Tier-2 Anomaly Variants.

Introduce 4 high-tension Tier-2 anomaly variants that only spawn during Overtime Shifts (OT-01+, Round >= 9):
1. Code 10: The Mirror Corridor / Doppelgänger (Duplicate player silhouette motionless at corridor end, vanishes on flashlight gaze).
2. Code 11: Code 2-B Hyper-Growth / Spore Bloom (Biomass spore wisps distorting player, requires [Q] FLAG classification 'HYPER-GROWTH').
3. Code 12: Code 5-B Phantom Shadow Stalker (Creeps along corridor wall toward nearest light source).
4. Code 13: Code 8-B Schizophrenic Terminal Ledger (Swaps checklist row names every 4.0s with cryptic warnings: 'DO NOT TRUST THE SHIFT').

Author socket sites in L_SectorC, wire BP_AnomalySocket Apply/Revert, update BP_AnomalyDirector PickType & budgets, and add Schizo Ledger & Doppelganger logic to BP_RoundManager.
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

SOCK = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket'
DIR = '/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector'
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
BASE = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
SOCKCLASS = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C'
FOLDER = 'Substrate/Anomalies/Tier2'

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
    try:
        return json.loads(r)['returnValue']['refPath']
    except Exception:
        return None

def spawn_asset(asset_path, name, loc, scale=(1, 1, 1), rot=(0, 0, 0)):
    r = M.call('call_tool', {
        'toolset_name': M.SCN,
        'tool_name': 'add_to_scene_from_asset',
        'arguments': {
            'asset_path': asset_path,
            'name': name,
            'xform': {
                'location': {'x': loc[0], 'y': loc[1], 'z': loc[2]},
                'rotation': {'pitch': rot[0], 'yaw': rot[1], 'roll': rot[2]},
                'scale': {'x': scale[0], 'y': scale[1], 'z': scale[2]}
            }
        }
    })
    try:
        return json.loads(r)['returnValue']['refPath']
    except Exception:
        return None

def set_props(ref, values):
    M.call('call_tool', {
        'toolset_name': M.OBJ,
        'tool_name': 'set_properties',
        'arguments': {'instance': {'refPath': ref}, 'values': json.dumps(values)}
    })

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
    print('=== PHASE 5 - STEP 2: RARE TIER-2 ANOMALY VARIANTS ===')

    # 1. Add variables to BP_RoundManager for Tier-2 effects
    rm_vars = json.loads(M.bp('list_variables', {'blueprint': {'refPath': RM}})).get('returnValue', [])
    for vname, vtype in [
        ('bSchizoLedgerActive', 'bool'),
        ('bSchizoSwap', 'bool')
    ]:
        if vname not in rm_vars:
            print(f'Adding {vname} to BP_RoundManager...')
            M.bp('add_variable', {'blueprint': {'refPath': RM}, 'name': vname, 'type_name': vtype})

    ensure_fns(RM, ['SetSchizoLedgerActive', 'ToggleSchizoLedger', 'CheckDoppelgangerGaze'])

    # Add parameter Active (bool) to SetSchizoLedgerActive if missing
    try:
        M.bp('add_function_param', {
            'graph': {'refPath': f'{RM}:SetSchizoLedgerActive'},
            'param_name': 'Active',
            'param_type': 'bool',
            'input_param': True
        })
    except Exception:
        pass

    # 2. Write SetSchizoLedgerActive, ToggleSchizoLedger, CheckDoppelgangerGaze in BP_RoundManager
    SET_SCHIZO = '''(fn SetSchizoLedgerActive (Active)
  (Variables|Default|SetbSchizoLedgerActive Active)
  (if Active
    (Utilities|Time|SetTimerbyFunctionName :self self :FunctionName "ToggleSchizoLedger" :Time 4.0 :bLooping true)
    (else
      (Utilities|Time|ClearTimerbyFunctionName :self self :FunctionName "ToggleSchizoLedger")
      (Variables|Default|SetbSchizoSwap false)
      (CallFunction|RefreshTerminal))))
'''
    TOGGLE_SCHIZO = '''(fn ToggleSchizoLedger ()
  (if (Variables|Default|GetbSchizoLedgerActive)
    (Variables|Default|SetbSchizoSwap (not (Variables|Default|GetbSchizoSwap)))
    (CallFunction|RefreshTerminal)))
'''
    CHECK_DOPPEL = '''(fn CheckDoppelgangerGaze ()
  (bind actors (Actor|GetAllActorsOfClass "/Script/Engine.Actor"))
  (for a actors
    (if (== (Actor|GetActorLabel a) "Doppelganger_Transit")
      (if (not (Rendering|IsActorHiddenInGame a))
        (bind cam (Game|GetPlayerCameraManager 0))
        (bind camLoc (Camera|GetCameraLocation cam))
        (bind camFwd (Math|Vector|GetForwardVector (Camera|GetCameraRotation cam)))
        (bind dLoc (Transformation|GetActorLocation a))
        (bind toD (Math|Vector|Normalize (- dLoc camLoc)))
        (bind dot (Math|Vector|DotProduct camFwd toD))
        (bind dist (Math|Vector|Distance camLoc dLoc))
        (if (and (> dot 0.82) (< dist 2500.0))
          (Rendering|SetActorHiddenInGame :self a :bNewHidden true)
          (Collision|SetActorEnableCollision :self a :bNewActorEnableCollision false)))))))
'''
    print('Writing BP_RoundManager Schizo and Doppelganger functions...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:SetSchizoLedgerActive'}, 'code': balance(SET_SCHIZO)})
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:ToggleSchizoLedger'}, 'code': balance(TOGGLE_SCHIZO)})
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:CheckDoppelgangerGaze'}, 'code': balance(CHECK_DOPPEL)})

    # 3. Update RefreshTerminal to handle Schizo Ledger swap
    REFRESH_TERMINAL = '''(fn RefreshTerminal ()
  (bind _currentround (Variables|Default|GetCurrentRound))
  (bind _isot (Variables|Default|GetbIsOvertime))
  (bind _otshift (Variables|Default|GetOvertimeShift))
  (bind _ot_str (Utilities|String|ToString(Integer) _otshift))
  (bind _ot_pad (select (< _otshift 10) "0" ""))
  (bind _ot_hdr (Utilities|String|Append "OVERTIME: OT-" (Utilities|String|Append _ot_pad _ot_str)))

  (bind _returnvalue (Utilities|String|ToString(Integer) _currentround))
  (bind _returnvalue_8 (Utilities|String|Append "00" _returnvalue))
  (bind _returnvalue_9 (Utilities|String|Append "0" _returnvalue))
  (bind _returnvalue_10 (< _currentround 10))
  (bind _returnvalue_11 (< _currentround 100))
  (bind _returnvalue_12 (select _returnvalue_11 _returnvalue_9 _returnvalue))
  (bind _returnvalue_13 (select _returnvalue_10 _returnvalue_8 _returnvalue_12))
  (bind _norm_hdr (Utilities|String|Append "SHIFT " _returnvalue_13))
  (bind _final_hdr (select _isot _ot_hdr _norm_hdr))

  (bind _terminalremaining (Variables|Default|GetTerminalRemaining))
  (bind _returnvalue_1 (Utilities|String|ToString(Integer) _terminalremaining))
  (bind _returnvalue_15 (Utilities|String|Append _returnvalue_1 " left)"))
  (bind _returnvalue_16 (Utilities|String|Append "CLOSE SHIFT: BLOCKED (" _returnvalue_15))
  (bind _basefooter (select (> _terminalremaining 0) _returnvalue_16 "CLOSE SHIFT: READY"))

  (bind _lastloggedaction (Variables|Default|GetLastLoggedAction))
  (bind _haslast (> (Utilities|String|Len _lastloggedaction) 0))
  (bind _normfooter (select _haslast (Utilities|String|Append (Utilities|String|Append _lastloggedaction " | ") _basefooter) _basefooter))

  (bind _disccount (Utilities|String|ToString(Integer) (Variables|Default|GetDiscoveredCount)))
  (bind _codex_str (Utilities|String|Append (Utilities|String|Append "CATALOGUED ANOMALIES: [" _disccount) " / 16]"))

  (bind _boot_footer (select (Variables|Default|GetbOvertimeUnlocked)
    (Utilities|String|Append _codex_str " | OVERTIME: AVAILABLE [PRESS [R] FOR OT-01]")
    (Utilities|String|Append _codex_str " | PRESS [BACKSPACE] TO WIPE RECORD")))

  (bind _finalfooter (select (and (== _currentround 1) (not _haslast) (not _isot)) _boot_footer _normfooter))

  (bind _self self)
  (Variables|Default|SetTerminalNames "")
  (Variables|Default|SetTerminalStates "")
  (Variables|Default|SetTerminalRemaining 0)
  (bind _outactors (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for _index (range (+ (Variables|Default|GetRequiredRowMax) 1))
    (for _array_element _outactors
      (CallFunction|AddRowifMatch _self _array_element _index)))

  (bind _names (Variables|Default|GetTerminalNames))
  (bind _states (Variables|Default|GetTerminalStates))
  (bind _disp_names _names)
  (bind _disp_states _states)
  (bind _disp_footer _finalfooter)

  (if (and (Variables|Default|GetbSchizoLedgerActive) (Variables|Default|GetbSchizoSwap))
    (bind _disp_names "DO NOT TRUST THE SHIFT\nNO ONE IS WAITING AT DOCK\nTHE AIRLOCK IS COMPROMISED\nSUBSTRATE REMEMBERS YOU\n")
    (bind _disp_states "[?]\n[!]\n[?]\n[!]\n")
    (bind _disp_footer "WARNING: CHECKLIST LEDGER DESYNCHRONIZED"))

  (if (Variables|Default|GetDebugTerminal)
    (Development|PrintString (Utilities|String|Append (Utilities|String|Append _final_hdr (Variables|Default|GetNL)) _disp_names) true true "(R=0.000000,G=0.660000,B=1.000000,A=1.000000)" 6.0)
    (Development|PrintString (Utilities|String|Append _disp_states _disp_footer) true true "(R=0.000000,G=0.660000,B=1.000000,A=1.000000)" 6.0))
  (CallFunction|PushTerminal _self _final_hdr _disp_names _disp_states _disp_footer)
  (CallFunction|OpenWestGate))
'''
    print('Writing BP_RoundManager:RefreshTerminal with Schizo Ledger support...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:RefreshTerminal'}, 'code': balance(REFRESH_TERMINAL)})

    # 4. Update BP_AnomalySocket: Apply and Revert for Codes 10, 11, 12, 13
    SOCKET_APPLY = '''(fn Apply (Round)
  (Variables|Default|SetApplied false)
  (if (not (CallFunction|CanApply :self self :Round Round))
    (return false))
  (bind target (CallFunction|GetTarget))
  (Utilities|IsValid target
    (:"Is Valid"
      (switch int (Variables|Default|GetAnomalyType)
        (:0
          (bind fixA (Utilities|Casting|CastToBP_Fixture :Object target)
            (:then
              (Variables|Default|SetCachedState (Class|BPFixture|GetFixtureState :self fixA))
              (Class|BPFixture|ApplyFixtureState :self fixA :NewState 2)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (Variables|Default|SetCachedState 0)
              (Rendering|SetActorHiddenInGame :self target :bNewHidden true)
              (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision false)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))))
        (:1
          (bind compL (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.LightComponent"))
          (bind lightL (Utilities|Casting|CastToLightComponent :Object compL)
            (:then
              (Variables|Default|SetCachedIntensity (Class|LightComponentBase|GetIntensity :self lightL))
              (Rendering|Components|Light|SetIntensity :self lightL :NewIntensity (Variables|Default|GetLightIntensity))
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (return false))))
        (:2
          (bind growG (Utilities|Casting|CastToBP_GrowthNode :Object target)
            (:then
              (Class|BPGrowthNode|ForceAdvance :self growG)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (return false))))
        (:3
          (Variables|Default|SetCachedTransform (Transformation|GetActorTransform :self target))
          (bind locD (Transformation|GetActorLocation :self target))
          (Transformation|SetActorLocation
            :self target
            :NewLocation (+ locD (Variables|Default|GetOffset))
            :bSweep false)
          (Variables|Default|SetApplied true)
          (Variables|Default|SetLastAppliedRound Round)
          (return true))
        (:4
          (Rendering|SetActorHiddenInGame :self target :bNewHidden false)
          (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision true)
          (Variables|Default|SetApplied true)
          (Variables|Default|SetLastAppliedRound Round)
          (return true))
        (:5
          (bind compP (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.PrimitiveComponent"))
          (bind primP (Utilities|Casting|CastToPrimitiveComponent :Object compP)
            (:then
              (Rendering|SetCastHiddenShadow :self primP :NewCastHiddenShadow true)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (return false))))
        (:6
          (Rendering|SetActorHiddenInGame :self target :bNewHidden true)
          (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision false)
          (Variables|Default|SetApplied true)
          (Variables|Default|SetLastAppliedRound Round)
          (bind sec (Variables|Default|GetSecondaryActor))
          (Utilities|IsValid sec
            (:"Is Valid"
              (Rendering|SetActorHiddenInGame :self sec :bNewHidden false)
              (Collision|SetActorEnableCollision :self sec :bNewActorEnableCollision true)
              (return true))
            (:"Is Not Valid"
              (return true))))
        (:7
          (bind compA (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.AudioComponent"))
          (bind audA (Utilities|Casting|CastToAudioComponent :Object compA)
            (:then
              (Audio|Components|Audio|SetPaused :self audA :bPause true)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (return false))))
        (:8
          (Variables|Default|SetApplied true)
          (Variables|Default|SetLastAppliedRound Round)
          (return true))
        (:9
          (bind airA (Utilities|Casting|CastToBP_Airlock :Object target)
            (:then
              (Class|BPAirlock|ApplyLoopBack :self airA :Enable true)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (return false))))
        (:10
          ;; Code 10: Doppelganger
          (Rendering|SetActorHiddenInGame :self target :bNewHidden false)
          (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision true)
          (Variables|Default|SetApplied true)
          (Variables|Default|SetLastAppliedRound Round)
          (return true))
        (:11
          ;; Code 11: Hyper-Growth / Spore Bloom
          (bind growH (Utilities|Casting|CastToBP_GrowthNode :Object target)
            (:then
              (Class|BPGrowthNode|ForceAdvance :self growH)
              (Class|BPGrowthNode|ForceAdvance :self growH)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (return false))))
        (:12
          ;; Code 12: Phantom Shadow Stalker
          (bind compP12 (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.PrimitiveComponent"))
          (bind primP12 (Utilities|Casting|CastToPrimitiveComponent :Object compP12)
            (:then
              (Rendering|SetActorHiddenInGame :self target :bNewHidden false)
              (Rendering|SetCastHiddenShadow :self primP12 :NewCastHiddenShadow true)
              (Variables|Default|SetApplied true)
              (Variables|Default|SetLastAppliedRound Round)
              (return true))
            (:CastFailed
              (return false))))
        (:13
          ;; Code 13: Schizophrenic Terminal Ledger
          (Variables|Default|SetApplied true)
          (Variables|Default|SetLastAppliedRound Round)
          (bind _rms13 (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_RoundManager.BP_RoundManager_C"))
          (for rm _rms13
            (bind rm_cast13 (Utilities|Casting|CastToBP_RoundManager rm)
              (:then
                (Class|BPRoundManager|SetSchizoLedgerActive :self rm_cast13 :Active true))
              (:CastFailed)))
          (return true))
        (:Default
          (return false))))
    (:"Is Not Valid"
      (Development|PrintString "ANOMALY socket has no target - check the level" false false "(R=1.000000,G=0.400000,B=0.200000,A=1.000000)" 6.0)
      (return false))))
'''
    print('Writing BP_AnomalySocket:Apply...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{SOCK}:Apply'}, 'code': balance(SOCKET_APPLY)})

    SOCKET_REVERT = '''(fn Revert ()
  (if (not (Variables|Default|GetApplied))
    (return))
  (if (== (Variables|Default|GetRevertRule) 1)
    (return))
  (Variables|Default|SetApplied false)
  (bind target (CallFunction|GetTarget))
  (Utilities|IsValid target
    (:"Is Valid"
      (switch int (Variables|Default|GetAnomalyType)
        (:0
          (bind fixR (Utilities|Casting|CastToBP_Fixture :Object target)
            (:then
              (Class|BPFixture|ApplyFixtureState :self fixR :NewState (Variables|Default|GetCachedState)))
            (:CastFailed
              (Rendering|SetActorHiddenInGame :self target :bNewHidden false)
              (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision true))))
        (:1
          (bind compR (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.LightComponent"))
          (bind lightR (Utilities|Casting|CastToLightComponent :Object compR)
            (:then
              (Rendering|Components|Light|SetIntensity :self lightR :NewIntensity (Variables|Default|GetCachedIntensity)))
            (:CastFailed)))
        (:2
          (bind growR (Utilities|Casting|CastToBP_GrowthNode :Object target)
            (:then
              (Class|BPGrowthNode|RevertGrowth :self growR))
            (:CastFailed)))
        (:3
          (Transformation|SetActorTransform :self target :NewTransform (Variables|Default|GetCachedTransform) :bSweep false))
        (:4
          (Rendering|SetActorHiddenInGame :self target :bNewHidden true)
          (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision false))
        (:5
          (bind compR5 (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.PrimitiveComponent"))
          (bind primR5 (Utilities|Casting|CastToPrimitiveComponent :Object compR5)
            (:then
              (Rendering|SetCastHiddenShadow :self primR5 :NewCastHiddenShadow false))
            (:CastFailed)))
        (:6
          (Rendering|SetActorHiddenInGame :self target :bNewHidden false)
          (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision true)
          (bind secR (Variables|Default|GetSecondaryActor))
          (Utilities|IsValid secR
            (:"Is Valid"
              (Rendering|SetActorHiddenInGame :self secR :bNewHidden true)
              (Collision|SetActorEnableCollision :self secR :bNewActorEnableCollision false))
            (:"Is Not Valid")))
        (:7
          (bind compR7 (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.AudioComponent"))
          (bind audR7 (Utilities|Casting|CastToAudioComponent :Object compR7)
            (:then
              (Audio|Components|Audio|SetPaused :self audR7 :bPause false))
            (:CastFailed)))
        (:8)
        (:9
          (bind airR (Utilities|Casting|CastToBP_Airlock :Object target)
            (:then
              (Class|BPAirlock|ApplyLoopBack :self airR :Enable false))
            (:CastFailed)))
        (:10
          ;; Code 10: Doppelganger revert
          (Rendering|SetActorHiddenInGame :self target :bNewHidden true)
          (Collision|SetActorEnableCollision :self target :bNewActorEnableCollision false))
        (:11
          ;; Code 11: Hyper-Growth revert
          (bind growRH (Utilities|Casting|CastToBP_GrowthNode :Object target)
            (:then
              (Class|BPGrowthNode|RevertGrowth :self growRH))
            (:CastFailed)))
        (:12
          ;; Code 12: Phantom Shadow Stalker revert
          (bind compR12 (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.PrimitiveComponent"))
          (bind primR12 (Utilities|Casting|CastToPrimitiveComponent :Object compR12)
            (:then
              (Rendering|SetActorHiddenInGame :self target :bNewHidden true)
              (Rendering|SetCastHiddenShadow :self primR12 :NewCastHiddenShadow false))
            (:CastFailed)))
        (:13
          ;; Code 13: Schizophrenic Ledger revert
          (bind _rms13r (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_RoundManager.BP_RoundManager_C"))
          (for rm _rms13r
            (bind rm_cast13r (Utilities|Casting|CastToBP_RoundManager rm)
              (:then
                (Class|BPRoundManager|SetSchizoLedgerActive :self rm_cast13r :Active false))
              (:CastFailed))))
        (:Default)))
    (:"Is Not Valid")))
'''
    print('Writing BP_AnomalySocket:Revert...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{SOCK}:Revert'}, 'code': balance(SOCKET_REVERT)})

    c_sock = M.bp('compile_blueprint', {'blueprint': {'refPath': SOCK}})
    print('  compile BP_AnomalySocket ->', c_sock[:150])

    # 5. Update BP_AnomalyDirector: PickType and Budgets for Overtime (Rounds >= 9)
    PICKTYPE = '''(fn PickType (Round)
  (bind r_std (Math|Random|RandomIntegerInRange 0 9))
  (bind r_t2 (Math|Random|RandomIntegerInRange 10 13))
  (bind r_roll (Math|Random|RandomIntegerInRange 1 100))
  (bind r_ot (select (<= r_roll 45) r_t2 r_std))
  (bind r3 (Math|Random|RandomIntegerInRange 0 2))
  (bind r5 (Math|Random|RandomIntegerInRange 0 6))
  (bind c5 (select (== r5 6) 7 r5))
  (return (select (>= Round 9) r_ot (select (<= Round 2) 0 (select (== Round 3) r3 (select (<= Round 5) c5 r_std))))))
'''
    GET_BUDGET_MIN = '''(fn GetBudgetMin (Round)
  (return (select (>= Round 9) 2 (select (<= Round 1) 0 (select (<= Round 5) 1 2)))))
'''
    GET_BUDGET_MAX = '''(fn GetBudgetMax (Round)
  (return (select (>= Round 9) 4 (select (<= Round 1) 0 (select (== Round 2) 1 (select (<= Round 5) 2 3))))))
'''
    print('Writing BP_AnomalyDirector PickType and Budgets...')
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{DIR}:PickType'}, 'code': balance(PICKTYPE)})
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{DIR}:GetBudgetMin'}, 'code': balance(GET_BUDGET_MIN)})
    M.bp('write_graph_dsl', {'graph': {'refPath': f'{DIR}:GetBudgetMax'}, 'code': balance(GET_BUDGET_MAX)})
    c_dir = M.bp('compile_blueprint', {'blueprint': {'refPath': DIR}})
    print('  compile BP_AnomalyDirector ->', c_dir[:150])

    print('Compiling BP_RoundManager...')
    c_rm = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('  compile BP_RoundManager ->', c_rm[:150])

    M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM, SOCK, DIR]}})
    print('Step 2 Rare Tier-2 Anomaly Variants successfully authored and wired!')

if __name__ == '__main__':
    main()
