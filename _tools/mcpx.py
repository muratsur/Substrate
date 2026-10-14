"""Compact helpers over ue_mcp for exploring and calling editor tools.

Usage:
    import mcpx as M
    M.init()
    M.tools('editor_toolset.toolsets.blueprint.BlueprintTools')
    M.bp('create_blueprint', {...})
"""
import json
import ue_mcp as _u

URL = _u.URL
init = _u.init
call = _u.call


def tools(toolset_name, full=False):
    """Print the tool names (and short descriptions) of a toolset."""
    d = json.loads(call('describe_toolset', {'toolset_name': toolset_name}))
    for t in d.get('tools', []):
        short = t['name'].split('.')[-1]
        if full:
            props = t.get('inputSchema', {}).get('properties', {})
            print('---', short)
            print('   ', t.get('description', '').splitlines()[0][:200])
            for k, v in props.items():
                print('      ', k, v.get('type', v.get('title', '?')), v.get('description', '')[:130])
        else:
            print(short, '|', t.get('description', '').splitlines()[0][:110])
    return d


def schema(toolset_name, tool_name):
    d = json.loads(call('describe_toolset', {'toolset_name': toolset_name}))
    for t in d.get('tools', []):
        if t['name'].split('.')[-1].lower() == tool_name.lower():
            print(json.dumps(t, indent=1)[:6000])
            return t
    print('not found:', tool_name)


BP = 'editor_toolset.toolsets.blueprint.BlueprintTools'
DT = 'editor_toolset.toolsets.data_table.DataTableTools'
DA = 'editor_toolset.toolsets.data_asset.DataAssetTools'
AT = 'editor_toolset.toolsets.asset.AssetTools'
ACT = 'editor_toolset.toolsets.actor.ActorTools'
APP = 'EditorToolset.EditorAppToolset'
SCN = 'editor_toolset.toolsets.scene.SceneTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'


def bp(name, args=None):
    return call('call_tool', {'toolset_name': BP, 'tool_name': name, 'arguments': args or {}})


def dt(name, args=None):
    return call('call_tool', {'toolset_name': DT, 'tool_name': name, 'arguments': args or {}})


def at(name, args=None):
    return call('call_tool', {'toolset_name': AT, 'tool_name': name, 'arguments': args or {}})


def actor(name, args=None):
    return call('call_tool', {'toolset_name': ACT, 'tool_name': name, 'arguments': args or {}})


def app(name, args=None):
    return call('call_tool', {'toolset_name': APP, 'tool_name': name, 'arguments': args or {}})
