"""T1.4 terminal: two-column checklist rows in WBP_Terminal.

Names and states are separate multi-line TextBlocks inside one HorizontalBox, so the
columns line up without per-row widgets or sorting code.

Run:  python _tools/terminal_widget2.py
"""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

W = M.call  # shorthand guard; real helpers below
P = '/Game/Substrate/UI/WBP_Terminal.WBP_Terminal'
WID = P + ':WidgetTree.'


def u(name, args):
    return M.call('call_tool', {'toolset_name': 'UMGToolSet.UMGToolSet',
                                'tool_name': name, 'arguments': args})


def setp(path, values):
    r = M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties',
                             'arguments': {'instance': {'refPath': path},
                                           'values': json.dumps(values)}})
    print('  set', path.split('.')[-1], '->', r[:110])


def layout():
    print('  add RowBox ->', u('AddWidget', {'widgetBlueprint': P, 'widgetClass': '/Script/UMG.HorizontalBox',
                                           'widgetDisplayName': 'RowBox', 'parentWidget': WID + 'Layout'})[:160])
    print('  rename TxtBody ->', u('RenameWidget', {'widgetBlueprint': P, 'widget': WID + 'TxtBody',
                                                   'newDisplayName': 'TxtNames'})[:160])
    print('  move names ->', u('MoveWidget', {'widgetBlueprint': P, 'widget': WID + 'TxtNames',
                                             'newParent': WID + 'RowBox', 'childIndex': 0})[:160])
    print('  add TxtStates ->', u('AddWidget', {'widgetBlueprint': P, 'widgetClass': '/Script/UMG.TextBlock',
                                               'widgetDisplayName': 'TxtStates',
                                               'parentWidget': WID + 'RowBox'})[:160])
    print('  move rowbox ->', u('MoveWidget', {'widgetBlueprint': P, 'widget': WID + 'RowBox',
                                              'newParent': WID + 'Layout', 'childIndex': 1})[:160])


def style():
    for n in ('TxtHeader', 'TxtNames', 'TxtStates', 'TxtFooter'):
        print('  var', n, u('ToggleWidgetAsVariable', {'widgetBlueprint': P, 'widget': WID + n,
                                                      'bIsVariable': True})[:80])
    setp(WID + 'TxtHeader', {'text': 'SHIFT ---', 'font': {'size': 22, 'bForceMonospaced': True}})
    setp(WID + 'TxtNames', {'text': '(no checklist)',
                            'colorAndOpacity': {'specifiedColor': {'r': 0.72, 'g': 0.68, 'b': 0.5, 'a': 1.0},
                                                'colorUseRule': 'UseColor_Specified'},
                            'font': {'size': 15, 'bForceMonospaced': True}, 'autoWrapText': False})
    setp(WID + 'TxtStates', {'text': '',
                             'colorAndOpacity': {'specifiedColor': {'r': 0.85, 'g': 0.8, 'b': 0.6, 'a': 1.0},
                                                 'colorUseRule': 'UseColor_Specified'},
                             'font': {'size': 15, 'bForceMonospaced': True}, 'autoWrapText': False})


SET = '''(fn SetChecklist (Header Names States Footer)
  (Widget|SetText(Text)
    :self (Variables|WBP_Terminal|GetTxtHeader)
    :InText (Utilities|Text|ToText(String) Header))
  (Widget|SetText(Text)
    :self (Variables|WBP_Terminal|GetTxtNames)
    :InText (Utilities|Text|ToText(String) Names))
  (Widget|SetText(Text)
    :self (Variables|WBP_Terminal|GetTxtStates)
    :InText (Utilities|Text|ToText(String) States))
  (Widget|SetText(Text)
    :self (Variables|WBP_Terminal|GetTxtFooter)
    :InText (Utilities|Text|ToText(String) Footer)))
'''


def main():
    M.init()
    print('== layout')
    layout()
    print('== style')
    style()
    print('tree:', u('GetWidgetDescription', {'widgetBlueprint': P, 'startWidget': None,
                                             'maxDepth': 0})[:900])
    print('== function')
    M.bp('add_function_param', {'graph': {'refPath': P + ':SetChecklist'}, 'param_name': 'States',
                                'param_type': 'string', 'input_param': True})
    print('  graph ->', M.bp('write_graph_dsl', {'graph': {'refPath': P + ':SetChecklist'},
                                                'code': SET})[:300])
    print('  compile ->', u('CompileWidgetBlueprint', {'widgetBlueprint': P})[:400])
    print('readback:', M.bp('read_graph_dsl', {'graph': {'refPath': P + ':SetChecklist'}})[:800])


if __name__ == '__main__':
    main()
