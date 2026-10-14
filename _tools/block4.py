import sys, json, time
sys.path.insert(0, '_tools')
import mcpx as M
M.init()

def scn(name, args=None):
    return M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': name, 'arguments': args or {}})

def at(name, args=None):
    return M.call('call_tool', {'toolset_name': M.AT, 'tool_name': name, 'arguments': args or {}})

def all_chars():
    r = scn('find_actors', {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': '/Script/Engine.Character'}})
    try:
        return [a['refPath'] for a in json.loads(r)['returnValue']]
    except Exception:
        print('chars err:', r[:200]); return []

def all_pawns():
    r = scn('find_actors', {'name': '', 'tag': '', 'collision_channels': [], 'actor_type': {'refPath': '/Script/Engine.Pawn'}})
    try:
        return [a['refPath'] for a in json.loads(r)['returnValue']]
    except Exception:
        print('pawns err:', r[:200]); return []

print('PIE:', M.app('IsPIERunning', {})[:60])
print('chars:', all_chars())
print('pawns:', all_pawns())
if all_chars() or all_pawns():
    ref = (all_chars() or all_pawns())[0]
    r = at('get_actor_transform', {'actor': {'refPath': ref}})
    print('TRANSFORM:', json.loads(r)['returnValue'])
