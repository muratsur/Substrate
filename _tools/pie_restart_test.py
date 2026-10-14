import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
def app(n,a=None): return M.call('call_tool', {'toolset_name':M.APP,'tool_name':n,'arguments':a or {}})
def at(n,a=None): return M.call('call_tool', {'toolset_name':M.ACT,'tool_name':n,'arguments':a or {}})
def scn(n,a=None): return M.call('call_tool', {'toolset_name':M.SCN,'tool_name':n,'arguments':a or {}})

# stop PIE
print('stop:', app('StopPIE', {})[:80])
time.sleep(3)
print('PIE now:', app('IsPIERunning', {})[:80])

# save the dirty airlock asset (try bare path)
for p in ('/Game/Substrate/Core/BP_Airlock', '/Game/Substrate/Core/BP_Airlock.BP_Airlock'):
    r = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [p]}})
    print('save %s ->' % p, r[:100])

print('start PIE:', app('StartPIE', {'options': {'bSimulate': False}})[:80])
time.sleep(14)
print('PIE now:', app('IsPIERunning', {})[:80])
