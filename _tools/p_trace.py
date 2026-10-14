import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

SCRIPT = r'''
import unreal

def run():
    us = unreal.UnrealEditorSubsystem()
    world = us.get_game_world()
    if not world:
        return {"error": "no game world - PIE not running?"}
    out = {}
    start = unreal.Vector(-1500.0, 8409.0, 350.0)
    end = unreal.Vector(-1750.0, 8409.0, 350.0)
    for n in range(1, 25):
        try:
            tq = unreal.TraceTypeQuery(n)
        except Exception:
            continue
        try:
            hit = unreal.SystemLibrary.line_trace_single(world, start, end, tq, False, [], unreal.DrawDebugTrace.NONE, True)
        except Exception as e:
            out["ch%d" % n] = "err " + str(e)[:60]
            continue
        if hit and hit.hit_component:
            a = hit.to_actor()
            nm = a.get_name() if a else "?"
            out["ch%d" % n] = "%s @ %.0f" % (nm, hit.location.x)
        else:
            out["ch%d" % n] = "no hit"
    return {"traces": out}
'''

r = M.call('call_tool', {'toolset_name': 'editor_toolset.toolsets.programmatic.ProgrammaticToolset',
                         'tool_name': 'execute_tool_script', 'arguments': {'script': SCRIPT}})
print(r[:2500])
