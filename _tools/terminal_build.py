"""T1.4 terminal: style WBP_Terminal's tree and expose the text blocks as variables.

Run:  python _tools/terminal_build.py style
"""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

W = 'UMGToolSet.UMGToolSet'
O = 'editor_toolset.toolsets.object.ObjectTools'
P = '/Game/Substrate/UI/WBP_Terminal.WBP_Terminal'
WID = P + ':WidgetTree.'


def u(name, args):
    return M.call('call_tool', {'toolset_name': W, 'tool_name': name, 'arguments': args})


def o(name, args):
    return M.call('call_tool', {'toolset_name': O, 'tool_name': name, 'arguments': args})


def setp(path, values):
    # 'values' is a JSON *string*, not an object.
    r = o('set_properties', {'instance': {'refPath': path}, 'values': json.dumps(values)})
    print('  set', path.split(':')[-1], '->', r[:150])


def style():
    # Terminal screen: near-black panel, pale amber phosphor text.
    setp(WID + 'Bg', {'brushColor': {'r': 0.01, 'g': 0.012, 'b': 0.015, 'a': 0.94},
                      'padding': {'left': 18, 'top': 12, 'right': 18, 'bottom': 12}})
    setp(WID + 'TxtHeader', {
        'text': 'SHIFT ---',
        'colorAndOpacity': {'specifiedColor': {'r': 0.85, 'g': 0.78, 'b': 0.55, 'a': 1.0},
                            'colorUseRule': 'UseColor_Specified'},
        'font': {'size': 22}})
    setp(WID + 'TxtBody', {
        'text': '(no checklist)',
        'colorAndOpacity': {'specifiedColor': {'r': 0.72, 'g': 0.68, 'b': 0.5, 'a': 1.0},
                            'colorUseRule': 'UseColor_Specified'},
        'font': {'size': 15},
        'autoWrapText': False})
    setp(WID + 'TxtFooter', {
        'text': 'CLOSE SHIFT: BLOCKED',
        'colorAndOpacity': {'specifiedColor': {'r': 0.8, 'g': 0.3, 'b': 0.25, 'a': 1.0},
                            'colorUseRule': 'UseColor_Specified'},
        'font': {'size': 16}})


def vars_on():
    for n in ('TxtHeader', 'TxtBody', 'TxtFooter'):
        r = u('ToggleWidgetAsVariable', {'widgetBlueprint': P, 'widget': WID + n, 'bIsVariable': True})
        print('  var', n, '->', r[:120])


def main():
    M.init()
    step = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if step in ('style', 'all'):
        print('== style ==')
        style()
    if step in ('vars', 'all'):
        print('== variables ==')
        vars_on()


if __name__ == '__main__':
    main()
