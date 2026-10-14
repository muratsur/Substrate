"""Read-only: list StaticMeshActor / Actor names whose label suggests collision or a barrier.

Run:  python -u _tools/list_blockers_names.py
"""
import sys
import json
import re
sys.path.insert(0, '_tools')
import mcpx as M

M.init()
PAT = re.compile(r'(wall|block|collision|invis|gate|door|barrier|cube|cap|trap|airlock|stop)', re.I)
for cls in ['/Script/Engine.StaticMeshActor', '/Script/Engine.Actor']:
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                             'arguments': {'name': '', 'tag': '', 'collision_channels': [],
                                           'actor_type': {'refPath': cls}}})
    try:
        refs = [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception:
        refs = []
    names = [x.split(':')[-1] for x in refs]
    hits = [n for n in names if PAT.search(n)]
    print(cls, 'total', len(names), 'matching', len(hits))
    for n in hits[:80]:
        print('  ', n)
