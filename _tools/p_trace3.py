import sys
sys.path.insert(0, '_tools')
import ue_mcp

SCRIPT = r'''
import unreal

def run():
    world = unreal.UnrealEditorSubsystem().get_game_world()
    if not world:
        return {"error": "no world - PIE not running?"}
    # sweep all trace channels 1..24 westward at chest height through the x=-1604 plane
    out = {}
    start = unreal.Vector(-1500.0, 8409.0, 350.0)
    end = unreal.Vector(-1750.0, 8409.0, 350.0)
    for n in range(1, 25):
        tq = None
        try:
            tq = getattr(unreal, "TraceTypeQuery%d" % n)
        except AttributeError:
            out["ch%d" % n] = "n/a"
            continue
        try:
            hit = unreal.SystemLibrary.line_trace_single(world, start, end, tq, False, [], unreal.DrawDebugTrace.NONE, True)
            if hit and hit.hit_component:
                a = hit.to_actor()
                out["ch%d" % n] = "%s @ x=%.0f" % (a.get_name() if a else "component", hit.location.x)
            else:
                out["ch%d" % n] = "no hit"
        except Exception as e:
            out["ch%d" % n] = "err " + str(e)[:50]
    return {"traces": out}
'''

r = ue_mcp.call('call_tool', {'toolset_name': 'editor_toolset.toolsets.programmatic.ProgrammaticToolset',
                              'tool_name': 'execute_tool_script', 'arguments': {'script': SCRIPT}})
print(str(r)[:2500])
