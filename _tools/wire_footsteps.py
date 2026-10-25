"""Footsteps (DESIGN.md: 'Footsteps with correct surface variation. Non-negotiable.'). CheckFootstep was an empty stub and
nothing referenced the FS_* sounds. Writes CheckFootstep on BP_RoundManager (every 0.5 s while the player walks: a random
FS_Sewer step on floors (FS_WetConcrete was too bright/hissy - zero-crossing ~10/ms vs ~3-5), FS_River when wading at canal level) and appends a looping timer to EventBeginPlay.
Back up first: _backups/footsteps_20261024/BP_RoundManager.uasset."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
A = '/Game/Substrate/Audio/'
def play(name):
    return f'(Audio|PlaySoundatLocation :Sound "{A}{name}.{name}" :Location feet :VolumeMultiplier 0.35 :PitchMultiplier pitch)'
def pick(prefix, n):  # random one of prefix_01..n via an if/elif chain (the DSL has no array literal)
    code = play(f'{prefix}_{n:02d}')
    for i in range(n - 1, 0, -1):
        code = f'(if (== r {i}) {play(f"{prefix}_{i:02d}")} (else {code}))'
    return code
CHECK_FOOTSTEP = f'''(fn CheckFootstep ()
  (bind pawn (Game|GetPlayerPawn 0))
  (Utilities|IsValid pawn
    (:"Is Valid"
      (bind vel (Transformation|GetVelocity :self pawn))
      (bind spd (Math|Vector|VectorLength vel))
      (if (> spd 60.0)
        (bind loc (Transformation|GetActorLocation :self pawn))
        (bind feet (- loc (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 90.0)))
        (bind pitch (Math|Random|RandomFloatinRange 0.85 1.0))
        (bind r (Math|Random|RandomIntegerinRange 1 5))
        (if (< (.z loc) 300.0)
          {pick("FS_River", 5)}
          (else
            {pick("FS_Sewer", 5)}))))
    (:"Is Not Valid")))
'''
# write_graph_dsl REPLACES an event's body (verified 2026-10-24, contrary to ANOMALY_SYSTEM.md), so restate the existing
# BeginPlay statements and add the timer at the end.
# EnableInput needs named pins: the positional form wired the controller into Target, so the manager got no keys.
BEGINPLAY_APPEND = '''(event EventBeginPlay
  (CallFunction|LoadShiftState)
  (CallFunction|StartShift)
  (Input|EnableInput :self self :PlayerController (Game|GetPlayerController 0))
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "CheckFootstep" :Time 0.5 :bLooping true))
'''
if __name__ == '__main__':
    print(M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':CheckFootstep'}, 'code': CHECK_FOOTSTEP})[:400])
    if '--fn-only' not in sys.argv:
        print(M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':EventGraph'}, 'code': BEGINPLAY_APPEND})[:400])
    print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:400])
