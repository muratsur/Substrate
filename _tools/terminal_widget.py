"""T1.4 terminal: the WBP_Terminal display API (SetChecklist / SetShiftState).

Run:  python _tools/terminal_widget.py
"""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

P = '/Game/Substrate/UI/WBP_Terminal.WBP_Terminal'


def g(bp, name):
    return {'refPath': bp + ':' + name}


def add_fn(name):
    print('  fn', name, M.bp('add_function_graph',
                              {'blueprint': {'refPath': P}, 'graph_name': name})[:120])


def add_param(fn, pname, ptype, is_input=True):
    print('  param', fn + '.' + pname,
          M.bp('add_function_param', {'graph': g(P, fn), 'param_name': pname,
                                      'param_type': ptype, 'input_param': is_input})[:120])


def write(fn, code):
    r = M.bp('write_graph_dsl', {'graph': g(P, fn), 'code': code})
    print('  graph', fn, '->', r[:500])


SET = '''(fn SetChecklist (Header Body Footer)
  (Widget|SetText(Text)
    :self (Variables|WBP_Terminal|GetTxtHeader)
    :InText (Utilities|Text|ToText(String) Header))
  (Widget|SetText(Text)
    :self (Variables|WBP_Terminal|GetTxtBody)
    :InText (Utilities|Text|ToText(String) Body))
  (Widget|SetText(Text)
    :self (Variables|WBP_Terminal|GetTxtFooter)
    :InText (Utilities|Text|ToText(String) Footer)))
'''


def main():
    M.init()
    add_fn('SetChecklist')
    add_param('SetChecklist', 'Header', 'string', True)
    add_param('SetChecklist', 'Body', 'string', True)
    add_param('SetChecklist', 'Footer', 'string', True)
    write('SetChecklist', SET)
    print('FNS:', M.bp('list_functions', {'blueprint': {'refPath': P}})[:400])
    print('READBACK:', M.bp('read_graph_dsl', {'graph': g(P, 'SetChecklist')})[:1500])
    print('COMPILE:', M.call('call_tool', {'toolset_name': 'UMGToolSet.UMGToolSet',
                                           'tool_name': 'CompileWidgetBlueprint',
                                           'arguments': {'widgetBlueprint': P}})[:600])


if __name__ == '__main__':
    main()
