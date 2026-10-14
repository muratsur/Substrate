import sys, json
sys.path.insert(0, '_tools')
import ue_mcp

SCRIPT = r'''
import unreal

def run():
    world = unreal.UnrealEditorSubsystem().get_game_world()
    if not world:
        return {"error": "no world"}
    hit = unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(-1500.0, 8409.0, 350.0),
        unreal.Vector(-1750.0, 8409.0, 350.0),
        unreal.TraceTypeQuery1, False, [], unreal.DrawDebugTrace.NONE, True)
    if hit and hit.hit_component:
        a = hit.to_actor()
        return {"hit": a.get_name() if a else "component-only"}
    return {"hit": "none"}
'''

import urllib.request, urllib.error
body = json.dumps({'arguments': {'script': SCRIPT}, 'tool_name': 'execute_tool_script',
                   'toolset_name': 'editor_toolset.toolsets.programmatic.ProgrammaticToolset'}).encode()
req = urllib.request.Request(ue_mcp.URL, data=body, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=100) as resp:
        print('OK:', resp.read().decode()[:1500])
except urllib.error.HTTPError as e:
    print('HTTP', e.code)
    print('body:', e.read().decode(errors='replace')[:2000])
