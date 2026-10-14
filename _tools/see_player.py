"""Where is the player, and what are they looking at?

Reads the pawn's transform in the running PIE world and captures the viewport from
exactly that pose, so the screenshot shows what the player sees.

Run:  python _tools/see_player.py [out.png]
"""
import sys
import json
import base64
import os
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
EA = 'EditorToolset.EditorAppToolset'
OUT = sys.argv[1] if len(sys.argv) > 1 else '_tools/shots/player_view.png'


def find(cls):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                             'arguments': {'name': '', 'tag': '', 'collision_channels': [],
                                           'actor_type': {'refPath': cls}}})
    try:
        return [a['refPath'] for a in json.loads(r).get('returnValue', [])]
    except Exception:
        return []


M.init()
print('PIE running:', M.app('IsPIERunning', {})[:40])
pawn = (find('/Script/Engine.Character') or [None])[0]
if not pawn:
    sys.exit('no pawn found - is PIE running?')
print('pawn:', pawn)

r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_transform',
                         'arguments': {'actor': {'refPath': pawn}}})
t = json.loads(r)['returnValue']
loc = t['location']
rot = t.get('rotation') or {}
print('player at (%.0f, %.0f, %.0f)  yaw=%.0f pitch=%.0f' % (loc['x'], loc['y'], loc['z'],
                                                             rot.get('yaw', 0), rot.get('pitch', 0)))

pose = {'location': {'x': loc['x'], 'y': loc['y'], 'z': loc['z'] + 60},
        'rotation': {'pitch': rot.get('pitch', 0), 'yaw': rot.get('yaw', 0), 'roll': 0}}
r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'CaptureViewport',
                         'arguments': {'captureTransform': pose, 'annotations': {}}})
d = json.loads(r)['returnValue']
img = d.get('image') or d
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'wb') as f:
    f.write(base64.b64decode(img['data']))
print('captured', OUT, os.path.getsize(OUT), 'bytes')

r = M.call('call_tool', {'toolset_name': EA, 'tool_name': 'GetVisibleActors', 'arguments': {}})
try:
    vis = [a['refPath'].split(':')[-1] for a in json.loads(r)['returnValue']]
except Exception:
    vis = r[:200]
print('in view (%d):' % len(vis), vis[:30])
