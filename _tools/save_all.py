import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
def at(n,a=None): return M.call('call_tool', {'toolset_name':M.AT,'tool_name':n,'arguments':a or {}})

ASSETS = [
    '/Game/Substrate/Maps/L_SectorC',          # the map (parked meshes, geometry fixes)
    '/Game/Substrate/Core/BP_Airlock',         # EventTick -> TryTransit wiring
    '/Game/Substrate/Core/BP_CanalRescue',     # rescue teleport (unchanged, but ensure clean)
    '/Game/Substrate/Core/BP_RoundManager',    # input wiring / GateOpen fix from earlier
    '/Game/Substrate/Core/BP_Fixture',         # LogResult fields used by livetest writes
    '/Game/Substrate/Core/BP_Terminal',
    '/Game/Substrate/Core/BP_AnomalyDirector',
]
for p in ASSETS:
    r = at('save_assets', {'asset_paths': [p]})
    print('%-50s -> %s' % (p, r[:120]))
