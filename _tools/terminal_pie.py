"""T1.4 terminal: PIE test harness — raise the terminal without key input, mark the panel.

Run:  python _tools/terminal_pie.py prep
      python _tools/terminal_pie.py restore
"""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

WBP = '/Game/Substrate/UI/WBP_Terminal.WBP_Terminal'
WID = WBP + ':WidgetTree.'
UP = {'x': 48.0, 'y': 10.0, 'z': -12.0}
STOW = {'x': 30.0, 'y': 4.0, 'z': -34.0}
MGR_CLS = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager_C'
TERM_CLS = '/Game/Substrate/Core/BP_Terminal.BP_Terminal_C'


def u(name, args):
    return M.call('call_tool', {'toolset_name': 'UMGToolSet.UMGToolSet',
                                'tool_name': name, 'arguments': args})


def setp(ref, values):
    r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties',
                             'arguments': {'instance': {'refPath': ref},
                                           'values': json.dumps(values)}})
    print('  set', ref.split('.')[-1], '->', r[:140])


def actors(cls):
    r = M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors',
                             'arguments': {'root': None, 'name': '', 'tag': '',
                                           'actor_type': {'refPath': cls}, 'bounds': None,
                                           'collision_channels': []}})
    try:
        return [a['refPath'] if isinstance(a, dict) else a
                for a in json.loads(r)['returnValue']]
    except Exception:
        print('  find failed:', r[:200])
        return []


def prep():
    for a in actors(MGR_CLS):
        print('  manager:', a)
        setp(a, {'DebugTerminal': True})
    for t in actors(TERM_CLS):
        print('  terminal:', t)
        setp(t, {'StowOffset': UP, 'ScreenYaw': 180.0})   # stowed == raised, so PIE shows it
    setp(WID + 'Bg', {'brushColor': {'r': 1.0, 'g': 0.0, 'b': 1.0, 'a': 1.0}})
    print('  compile wbp ->', u('CompileWidgetBlueprint', {'widgetBlueprint': WBP})[:120])


def restore():
    for t in actors(TERM_CLS):
        setp(t, {'StowOffset': STOW})
    setp(WID + 'Bg', {'brushColor': {'r': 0.01, 'g': 0.012, 'b': 0.015, 'a': 0.94}})
    print('  compile wbp ->', u('CompileWidgetBlueprint', {'widgetBlueprint': WBP})[:120])


if __name__ == '__main__':
    M.init()
    {'prep': prep, 'restore': restore}[sys.argv[1] if len(sys.argv) > 1 else 'prep']()
