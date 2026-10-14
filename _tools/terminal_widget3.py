"""T1.4 terminal: (re)create WBP_Terminal.SetChecklist(Header, Names, States, Footer).

Run:  python _tools/terminal_widget3.py
"""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

P = '/Game/Substrate/UI/WBP_Terminal.WBP_Terminal'


def g(n):
    return {'refPath': P + ':' + n}


def compile_wbp():
    r = M.call('call_tool', {'toolset_name': 'UMGToolSet.UMGToolSet',
                             'tool_name': 'CompileWidgetBlueprint',
                             'arguments': {'widgetBlueprint': P}})
    print('  compile ->', r[:250])
    return r


CODE = '''(fn SetChecklist (Header Names States Footer)
  (Widget|SetText(Text) :self (Variables|WBP_Terminal|GetTxtHeader) :InText (Utilities|Text|ToText(String) Header))
  (Widget|SetText(Text) :self (Variables|WBP_Terminal|GetTxtNames) :InText (Utilities|Text|ToText(String) Names))
  (Widget|SetText(Text) :self (Variables|WBP_Terminal|GetTxtStates) :InText (Utilities|Text|ToText(String) States))
  (Widget|SetText(Text) :self (Variables|WBP_Terminal|GetTxtFooter) :InText (Utilities|Text|ToText(String) Footer)))
'''


def main():
    M.init()
    print('add:', M.bp('add_function_graph', {'blueprint': {'refPath': P},
                                             'graph_name': 'SetChecklist'})[:200])
    for p in ('Header', 'Names', 'States', 'Footer'):
        print('  param', p, M.bp('add_function_param', {'graph': g('SetChecklist'), 'param_name': p,
                                                       'param_type': 'string', 'input_param': True})[:90])
    compile_wbp()
    print('write:', M.bp('write_graph_dsl', {'graph': g('SetChecklist'), 'code': CODE})[:300])
    compile_wbp()
    print('readback:', M.bp('read_graph_dsl', {'graph': g('SetChecklist')})[:800])


if __name__ == '__main__':
    main()
