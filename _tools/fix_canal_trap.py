"""Untrap the canal walkway.

BP_CanalRescue_C_0 is a trigger box whose world box is currently
  x -3100..2500, y 8980..10820, z 100..240
i.e. exactly a standing player's height above the channel floor at z=100, so walking the
low channel teleported you to the spawn.  The box is moved/sized so its top sits under the
walkable floor (z<=40) while still catching anyone who actually drops into the canal here.

Original: location (-300, 9900, 170), scale (70, 23, 1.75), BoxExtent 40
New     : location (-300, 9900, -130), scale (70, 23, 4.25)   -> box z -300..40

Run:  python _tools/fix_canal_trap.py            (apply + save)
      python _tools/fix_canal_trap.py revert     (put it back)
"""
import sys
import json
import os
import time
sys.path.insert(0, '_tools')
import mcpx as M

AT = 'editor_toolset.toolsets.actor.ActorTools'
LEV = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.'
ACTOR = 'BP_CanalRescue_C_0'
REF = LEV + ACTOR
UMAP = 'Content/Substrate/Maps/L_SectorC.umap'
ORIG = {'location': {'x': -300.0, 'y': 9900.0, 'z': 170.0},
        'scale': {'x': 70.0, 'y': 23.0, 'z': 1.75}}
FIXED = {'location': {'x': -300.0, 'y': 9900.0, 'z': -130.0},
         'scale': {'x': 70.0, 'y': 23.0, 'z': 4.25}}


def bounds(a=ACTOR):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'get_actor_bounds',
                             'arguments': {'actor': {'refPath': LEV + a}}})
    try:
        v = json.loads(r)['returnValue']
        return tuple(round(v['min'][k]) for k in 'xyz') + tuple(round(v['max'][k]) for k in 'xyz')
    except Exception:
        return r[:120]


def apply(xform):
    r = M.call('call_tool', {'toolset_name': AT, 'tool_name': 'set_actor_transform',
                             'arguments': {'actor': {'refPath': REF}, 'xform': xform}})
    return r[:90]


M.init()
pie = M.app('IsPIERunning', {})
if 'true' in pie:
    sys.exit('PIE is running - stop it first, the running world has its own copy of this actor')
print('before:', bounds())
print('set   :', apply(ORIG if (len(sys.argv) > 1 and sys.argv[1] == 'revert') else FIXED))
time.sleep(1)
print('after :', bounds())
print('save  :', M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets',
                                      'arguments': {'asset_paths': ['/Game/Substrate/Maps/L_SectorC']}})[:80])
time.sleep(2)
st = os.stat(UMAP)
print('umap  : %d bytes  %s' % (st.st_size, time.strftime('%m-%d %H:%M:%S', time.localtime(st.st_mtime))))
