"""Phase 3 Step 2: Sector D Ambience & 3 Terminal Beats."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

def setup_beats():
    print('Setting up Sector D Beats on BP_RoundManager...')

    CHECK_BEATS = '''(fn CheckSectorDBeats ()
  (bind pawn (Game|GetPlayerPawn 0))
  (Utilities|IsValid pawn
    (:"Is Valid"
      (bind loc (Transformation|GetActorLocation :self pawn))
      (bind py (.y loc))
      (if (and (>= py -7900.0) (== (Variables|Default|GetSectorDBeat) 0))
        (Variables|Default|SetSectorDBeat 1)
        (CallFunction|PushTerminal
          :Header "SECTOR D - BIO-CONTAINMENT"
          :Names "C-06 RELIEF VALVE"
          :States "[UNREPORTED - 4 SHIFTS]"
          :Footer "WHY DID YOU KEEP WALKING THE ROUTE?")
        (Audio|PlaySound2D :Sound "/Engine/VREditor/Sounds/UI/Laser_Pull.Laser_Pull" :VolumeMultiplier 0.7 :PitchMultiplier 1.2)
        (Development|PrintString "SECTOR D - BEAT 1" true true "(R=1.000000,G=0.800000,B=0.200000,A=1.000000)" 5.0)
        (else
          (if (and (>= py -7300.0) (== (Variables|Default|GetSectorDBeat) 1))
            (Variables|Default|SetSectorDBeat 2)
            (CallFunction|PushTerminal
              :Header "SHIFT 008 - OVERDUE"
              :Names "C-06 RELIEF VALVE"
              :States "[PRESSURE CRITICAL]"
              :Footer "THE FORM ONLY ASKS IF IT IS THERE.")
            (Audio|PlaySound2D :Sound "/Engine/VREditor/Sounds/UI/Laser_Pull.Laser_Pull" :VolumeMultiplier 0.7 :PitchMultiplier 1.2)
            (Development|PrintString "SECTOR D - BEAT 2" true true "(R=1.000000,G=0.800000,B=0.200000,A=1.000000)" 5.0)
            (else
              (if (and (>= py -6700.0) (== (Variables|Default|GetSectorDBeat) 2))
                (Variables|Default|SetSectorDBeat 3)
                (CallFunction|PushTerminal
                  :Header "SUBSTRATE"
                  :Names "C-06 RELIEF VALVE"
                  :States "[SIGN OFF REQUIRED]"
                  :Footer "PRESS [E] PASS   OR   [Q] FLAG")
                (Audio|PlaySound2D :Sound "/Engine/VREditor/Sounds/UI/Laser_Pull.Laser_Pull" :VolumeMultiplier 0.7 :PitchMultiplier 1.2)
                (Development|PrintString "SECTOR D - BEAT 3" true true "(R=1.000000,G=0.800000,B=0.200000,A=1.000000)" 5.0)))))))
    (:"Is Not Valid")))
'''

    ENTER_SECTOR_D = '''(fn EnterSectorD ()
  (Variables|Default|SetShiftOpen false)
  (Variables|Default|SetSectorDBeat 0)
  (bind pawn (Game|GetPlayerPawn 0))
  (Transformation|SetActorLocationAndRotation
    :self pawn
    :NewLocation (Math|Vector|MakeVector -660.0 -8500.0 450.0)
    :NewRotation (Math|Rotator|MakeRotator 0.0 90.0 0.0)
    :bSweep false)
  (CallFunction|PushTerminal
    :Header "SECTOR D - ACCESS GRANTED"
    :Names "C-06 RELIEF VALVE"
    :States "[ ]"
    :Footer "PROCEED TO RELIEF VALVE")
  (Audio|PlaySound2D :Sound "/Engine/VREditor/Sounds/UI/Laser_Pull.Laser_Pull" :VolumeMultiplier 0.7 :PitchMultiplier 1.2)
  (Utilities|Time|SetTimerbyFunctionName
    :Object self
    :FunctionName "CheckSectorDBeats"
    :Time 0.25
    :bLooping true)
  (Development|PrintString "SECTOR D - ACCESS GRANTED. PROCEED TO RELIEF VALVE." true true "(R=1.000000,G=0.800000,B=0.200000,A=1.000000)" 8.0))
'''

    print('Writing CheckSectorDBeats...')
    r_ck = M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:CheckSectorDBeats'}, 'code': balance(CHECK_BEATS)})
    print('  CheckSectorDBeats ->', r_ck[:150])

    print('Writing EnterSectorD...')
    r_en = M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:EnterSectorD'}, 'code': balance(ENTER_SECTOR_D)})
    print('  EnterSectorD ->', r_en[:150])

    c_r = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('compile BP_RoundManager ->', c_r[:150])

def main():
    M.init()
    setup_beats()
    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}})
    print('save dirty ->', s[:100])

if __name__ == '__main__':
    main()
