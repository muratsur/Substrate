"""Fix EndDemo and QuitApp in BP_RoundManager."""
import sys
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'

END_DEMO = '''(fn EndDemo ()
  (Input|DisableInput :self self :PlayerController (Game|GetPlayerController 0))
  (CallFunction|PushTerminal
    :Header "SHIFT TERMINATED"
    :Names "SUBSTRATE DEMO COMPLETE"
    :States ""
    :Footer "THANK YOU FOR PLAYING")
  (CameraFades|StartCameraFade
    :self (Game|GetPlayerCameraManager 0)
    :FromAlpha 0.0
    :ToAlpha 1.0
    :Duration 3.0
    :Color "(R=0.000000,G=0.000000,B=0.000000,A=1.000000)"
    :bShouldFadeAudio true
    :bHoldWhenFinished true)
  (Utilities|Time|SetTimerbyFunctionName
    :Object self
    :FunctionName "QuitApp"
    :Time 5.0
    :bLooping false)
  (Development|PrintString "SUBSTRATE DEMO COMPLETE - THANK YOU FOR PLAYING" true true "(R=0.200000,G=1.000000,B=0.500000,A=1.000000)" 10.0))
'''

QUIT_APP = '''(fn QuitApp ()
  (Game|QuitGame :SpecificPlayer (Game|GetPlayerController 0)))
'''

def main():
    M.init()
    print('Writing EndDemo...')
    r1 = M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:EndDemo'}, 'code': END_DEMO})
    print('  EndDemo ->', r1)
    print('Writing QuitApp...')
    r2 = M.bp('write_graph_dsl', {'graph': {'refPath': f'{RM}:QuitApp'}, 'code': QUIT_APP})
    print('  QuitApp ->', r2)
    c = M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})
    print('  compile ->', c)
    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM]}})
    print('  save ->', s)

if __name__ == '__main__':
    main()
