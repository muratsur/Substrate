"""Actors that block the player (QueryAndPhysics, Pawn not ignored) but ignore the Visibility channel, so trace_world
passes through them (e.g. the 230 blocks fixed on 2026-10-23 kept Visibility: Ignore). walk_graph.py overlays their tops.
Writes _evidence/trace_invisible_blockers.json."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
import preflight_collision as P
M.init()
actors = json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': '', 'tag': '', 'collision_channels': []}}))['returnValue']
names = sorted({n for n in (a['refPath'].split('.')[-1] for a in actors) if n.startswith('StaticMeshActor')})
rubble = set(json.load(open('_tools/preflight_rubble_cache.json')))
todo = [n for n in names if n not in rubble]
SCRIPT = (P.COLLECT.replace("if hidden else {'min'", "if True else {'min'")   # always fetch bounds here
          .replace("'dx': b['max']['x'] - b['min']['x'],", "'xmin': b['min']['x'], 'xmax': b['max']['x'], 'ymin': b['min']['y'], 'ymax': b['max']['y'], 'dx': b['max']['x'] - b['min']['x'],"))
assert 'xmin' in SCRIPT and 'if True else' in SCRIPT
out = []
for i in range(0, len(todo), 100):
    r = M.call('call_tool', {'toolset_name': 'editor_toolset.toolsets.programmatic.ProgrammaticToolset', 'tool_name': 'execute_tool_script',
                             'arguments': {'script': SCRIPT.replace('%NAMES%', repr(todo[i:i + 100]))}})
    for row in json.loads(json.loads(r)['returnValue'])['rows']:
        if P.blocks_pawn(row) and row['responses'].get('Visibility') == 'ECR_Ignore' and not row['hidden']:
            out.append(row)
    print(f'  {min(i + 100, len(todo))}/{len(todo)} checked, {len(out)} trace-invisible blockers', flush=True)
json.dump(out, open('_evidence/trace_invisible_blockers.json', 'w'))
