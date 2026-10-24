"""Turn off bSimulatePhysics on rubble that also has NoCollision (UE logs 'Invalid Simulate Options' for each and never simulates them).
Finds them by scanning every cached SM_detail actor in the editor world."""
import sys, json
from pathlib import Path
sys.path.insert(0, '_tools')
import mcpx as M
M.init()
LEVEL = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
names = json.loads(Path('_tools/preflight_rubble_cache.json').read_text())
SCRIPT = """
import json
def run():
    T = lambda tool, args: execute_tool(tool, json.dumps(args))['returnValue']
    fixed = []
    for n in %NAMES%:
        rp = '%LEVEL%' + n + '.StaticMeshComponent0'
        try:
            bi = json.loads(T('editor_toolset.toolsets.object.ObjectTools.get_properties', {'instance': {'refPath': rp}, 'properties': ['BodyInstance']}))['BodyInstance']
        except Exception:
            continue
        if bi.get('bSimulatePhysics') and bi.get('collisionEnabled') == 'NoCollision':
            T('editor_toolset.toolsets.object.ObjectTools.set_properties', {'instance': {'refPath': rp}, 'values': json.dumps({'BodyInstance': {'bSimulatePhysics': False}})})
            after = json.loads(T('editor_toolset.toolsets.object.ObjectTools.get_properties', {'instance': {'refPath': rp}, 'properties': ['BodyInstance']}))['BodyInstance']
            fixed.append((n, after.get('bSimulatePhysics')))
    return {'fixed': fixed}
""".replace('%LEVEL%', LEVEL)
fixed = []
for i in range(0, len(names), 150):
    r = M.call('call_tool', {'toolset_name': 'editor_toolset.toolsets.programmatic.ProgrammaticToolset', 'tool_name': 'execute_tool_script',
                             'arguments': {'script': SCRIPT.replace('%NAMES%', repr(names[i:i + 150]))}})
    fixed += json.loads(json.loads(r)['returnValue'])['fixed']
bad = [n for n, sim in fixed if sim]
print(f'turned off simulate on {len(fixed)} rubble actors, still simulating: {bad}')
assert not bad
if fixed:
    print(M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}}))
