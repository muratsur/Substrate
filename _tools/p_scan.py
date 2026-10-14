import sys
sys.path.insert(0, '_tools')
import ue_mcp

SCRIPT = r'''
import json

def bounds_of(rp):
    r = execute_tool("editor_toolset.toolsets.actor.ActorTools.get_actor_bounds",
                     json.dumps({"actor": {"refPath": rp}}))
    return r["returnValue"]

def run():
    world_actors = execute_tool("editor_toolset.toolsets.scene.SceneTools.find_actors",
                     json.dumps({"name": "", "tag": "", "collision_channels": [], "actor_type": {"refPath": ""}}))
    refs = world_actors["returnValue"]
    out = []
    for a in refs:
        rp = a["refPath"]
        try:
            bb = bounds_of(rp)
        except Exception:
            continue
        mn = bb["min"]
        mx = bb["max"]
        if mn["x"] <= -1604 <= mx["x"] and mn["y"] - 250 <= 8409 <= mx["y"] + 250 and mn["z"] < 470 and mx["z"] > 280:
            out.append("%s x[%d..%d] y[%d..%d] z[%d..%d]" % (rp.split(":")[-1], mn["x"], mx["x"], mn["y"], mx["y"], mn["z"], mx["z"]))
    return {"n": len(refs), "crossers": out}
'''

ue_mcp.init()
r = ue_mcp.call('call_tool', {'toolset_name': 'editor_toolset.toolsets.programmatic.ProgrammaticToolset',
                              'tool_name': 'execute_tool_script', 'arguments': {'script': SCRIPT}})
print(str(r)[:3500])
