"""Inspect actor positions for Shot 5 and Shot 6."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

def main():
    M.init()
    print('=== Finding Growth Nodes ===')
    res = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': 'Growth', 'tag': '', 'collision_channels': []}})
    nodes = json.loads(res).get('returnValue', [])
    for n in nodes:
        ref = n['refPath']
        tr = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': ref}}})).get('returnValue', {})
        print('GrowthNode:', ref, 'Transform:', tr.get('translation'))

    print('=== Finding C-04 / Fixture C4 ===')
    res_f = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': 'C4', 'tag': '', 'collision_channels': []}})
    fixtures = json.loads(res_f).get('returnValue', [])
    for f in fixtures:
        ref = f['refPath']
        tr = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': ref}}})).get('returnValue', {})
        print('Fixture C4:', ref, 'Transform:', tr.get('translation'))

    res_all_f = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': 'Fixture', 'tag': '', 'collision_channels': []}})
    for f in json.loads(res_all_f).get('returnValue', []):
        ref = f['refPath']
        tr = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_actor_transform', 'arguments': {'actor': {'refPath': ref}}})).get('returnValue', {})
        lbl = json.loads(M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_label', 'arguments': {'actor': {'refPath': ref}}})).get('returnValue', '')
        print('Fixture:', lbl, ref, 'Transform:', tr.get('translation'))

if __name__ == '__main__':
    main()
