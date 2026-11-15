"""Pause menu: the raised terminal (a world-space widget) showed through the translucent backdrop and overlapped the
settings rows, and the subtitle said SECTOR C in every sector. The backdrop is now opaque and the subtitle is static.
Usage: python _tools/pause_backdrop.py   (PIE stopped), then save WBP_Pause."""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M
WP = '/Game/Substrate/UI/WBP_Pause.WBP_Pause'
WT = WP + ':WidgetTree.'

def obj(tool, ref, **kw):
    return M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': tool, 'arguments': {'instance': {'refPath': ref}, **kw}})

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    before = obj('get_properties', WT + 'RootBorder', properties=['BrushColor'])
    assert 'BrushColor' in before or 'brushColor' in before, 'WBP_Pause not found: is the editor on Substrate?'
    print('before', before[:200])
    c = json.loads(json.loads(before)['returnValue'])
    c = c.get('BrushColor') or c.get('brushColor')
    c['a'] = 1.0   # full struct back: partial struct dicts can clear the other fields
    print(obj('set_properties', WT + 'RootBorder', values=json.dumps({'BrushColor': c}))[:120])
    print(obj('set_properties', WT + 'TxtSector', values=json.dumps({'Text': 'SUBSTRATE FACILITY'}))[:120])
    print('after', obj('get_properties', WT + 'RootBorder', properties=['BrushColor'])[:200],
          obj('get_properties', WT + 'TxtSector', properties=['Text'])[:200])
    print(M.call('call_tool', {'toolset_name': 'UMGToolSet.UMGToolSet', 'tool_name': 'CompileWidgetBlueprint', 'arguments': {'widgetBlueprint': {'refPath': WP}}})[:200])
