"""Read-only: live PIE pawn position, BlockingVolume_2 transform, and the Message Log 'Play In Editor' entries.

Run:  python -u _tools/pie_status.py
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
M.init()
print('PIE running:', M.app('IsPIERunning', {})[:40])


def find(cls):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                             'arguments': {'name': '', 'tag': '', 'collision_channels': [],
                                           'actor_type': {'refPath': cls}}})
    try:
        return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception:
        return []


def xform(ref):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
                             'arguments': {'actor': {'refPath': ref}}})
    return json.loads(r)['returnValue']


pawn = find('/Script/Engine.Character')[0]
p = xform(pawn)
print('pawn:', pawn.split(':')[-1], 'at', p['location'], 'yaw', p.get('rotation', {}).get('yaw'))
for ref in find('/Script/Engine.BlockingVolume'):
    if ref.endswith('BlockingVolume_2'):
        print('BV2:', xform(ref))
