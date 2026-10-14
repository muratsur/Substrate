import sys, json, urllib.request, urllib.error
sys.path.insert(0, '_tools')
import ue_mcp

SCRIPT = r'''
import unreal

def run():
    world = unreal.UnrealEditorSubsystem().get_game_world()
    if not world:
        return {"error": "no world - PIE not running?"}
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

# initialize session first (same as ue_mcp.init) then post with session id
ue_mcp.init()
body = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                   "params": {"name": "call_tool",
                              "arguments": {"toolset_name": "editor_toolset.toolsets.programmatic.ProgrammaticToolset",
                                            "tool_name": "execute_tool_script",
                                            "arguments": {"script": SCRIPT}}}}).encode()
h = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
if ue_mcp._sid:
    h['Mcp-Session-Id'] = ue_mcp._sid
req = urllib.request.Request(ue_mcp.URL, data=body, headers=h)
try:
    with urllib.request.urlopen(req, timeout=110) as resp:
        t = resp.read().decode()
        print('OK:', t[:2000])
except urllib.error.HTTPError as e:
    print('HTTP', e.code, 'body:', e.read().decode(errors='replace')[:1500])
