"""T1.4 terminal: BP_Terminal actor — variables, functions, event graph, F key.

Run:  python _tools/terminal_actor.py
"""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

BP = '/Game/Substrate/Core/BP_Terminal.BP_Terminal'
ACT = 'editor_toolset.toolsets.actor.ActorTools'


def g(name):
    return {'refPath': BP + ':' + name}


def balance(code):
    depth = 0
    for ch in code:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
    if depth > 0:
        print('  (auto-closing', depth, 'parens)')
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code


def write(name, code):
    r = M.bp('write_graph_dsl', {'graph': g(name), 'code': balance(code)})
    print('  graph', name, '->', r[:500])
    return r


def add_var(name, type_name, container=None, obj_class=None):
    args = {'blueprint': {'refPath': BP}, 'name': name}
    if obj_class:
        args['object_class'] = {'refPath': obj_class}
        if container:
            args['container_type'] = container
        r = M.bp('add_object_variable', args)
    else:
        args['type_name'] = type_name
        if container:
            args['container_type'] = container
        r = M.bp('add_variable', args)
    print('  var', name, '->', r[:150])
    return r


def add_fn(name):
    print('  fn', name, M.bp('add_function_graph',
                             {'blueprint': {'refPath': BP}, 'graph_name': name})[:120])


def add_param(fn, pname, ptype, is_input=True):
    print('  param', fn + '.' + pname,
          M.bp('add_function_param', {'graph': g(fn), 'param_name': pname,
                                      'param_type': ptype, 'input_param': is_input})[:110])


def editable(*names):
    for n in names:
        M.bp('set_variable_instance_editable',
             {'blueprint': {'refPath': BP}, 'variable_name': n, 'instance_editable': True})


VARS = [('Raised', 'bool'), ('Bound', 'bool'),
        ('UpOffset', 'Vector'), ('StowOffset', 'Vector')]

ATTACH = '''(fn AttachToPlayer ()
  (bind pawn (Game|GetPlayerPawn :PlayerIndex 0))
  (bind cam (Actor|GetComponentbyClass :self pawn :ComponentClass "/Script/Engine.CameraComponent"))
  (bind cc (Utilities|Casting|CastToCameraComponent :Object cam)
    (:then
      (Transformation|AttachActorToComponent
        :self self
        :Parent cc
        :SocketName "None"
        :LocationRule "KeepRelative"
        :RotationRule "KeepRelative"
        :ScaleRule "KeepRelative"
        :bWeldSimulatedBodies false)
      (Variables|Default|SetBound true)
      (CallFunction|SetRaised :Want false))
    (:CastFailed
      (Development|PrintString :InString "TERMINAL: no camera to attach to" :Duration 3.0))))
'''

RAISED = '''(fn SetRaised (Want)
  (Variables|Default|SetRaised Want)
  (if Want
    (Transformation|SetActorRelativeLocation
      :self self
      :NewLocation (Variables|Default|GetUpOffset))
    (else
      (Transformation|SetActorRelativeLocation
        :self self
        :NewLocation (Variables|Default|GetStowOffset))))
  (Rendering|SetActorHiddenInGame :self self :NewHidden (not Want)))
'''

SHOW = '''(fn ShowChecklist (Header Body Footer)
  (bind w (UserInterface|GetUserWidgetObject :self (Variables|Default|GetScreen)))
  (bind tw (Utilities|Casting|CastToWBP_Terminal :Object w)
    (:then
      (Class|WBPTerminal|SetChecklist :self tw :Header Header :Body Body :Footer Footer))
    (:CastFailed
      (Development|PrintString :InString "TERMINAL: widget missing" :Duration 3.0))))
'''

BEGIN = '''(event EventBeginPlay
  (CallFunction|AttachToPlayer)
  (Development|PrintString
    :InString "TERMINAL: F raises / stows the checklist"
    :Duration 5.0))
'''


def key_nodes():
    """F key -> toggle raise. Key nodes need explicit pin wiring (no DSL event form)."""
    def node(t, x, y):
        return json.loads(M.bp('create_node', {'graph': g('EventGraph'), 'type_id': t,
                                              'pos': {'x': x, 'y': y}}))['returnValue']

    def info(n):
        return json.loads(M.bp('get_node_infos', {'nodes': [n]}))['returnValue'][0]

    k = node('Input|KeyboardEvents|F', 0, 700)
    b = node('Utilities|FlowControl|Branch', 320, 700)
    print('  key F:', k['refPath'].split('.')[-1], 'branch:', b['refPath'].split('.')[-1])
    ki, bi = info(k), info(b)
    pressed = next(p for p in ki['output_pins'] if p['name'] == 'Pressed')
    ex = next(p for p in bi['input_pins'] if p['type_id'] == 'Exec')
    cond = next(p for p in bi['input_pins'] if p['name'] == 'Condition')
    M.bp('connect_pins', {'output_pin': pressed['pin_id'], 'input_pin': ex['pin_id']})
    # condition = Raised
    rais = node('Variables|Default|GetRaised', -40, 820)
    ri = info(rais)
    rp = next(p for p in ri['output_pins'] if p['name'] == 'Raised')
    M.bp('connect_pins', {'output_pin': rp['pin_id'], 'input_pin': cond['pin_id']})
    return b


def main():
    M.init()
    print('== vars')
    for n, t in VARS:
        add_var(n, t)
    editable('UpOffset', 'StowOffset')
    print('  vars now:', M.bp('list_variables', {'blueprint': {'refPath': BP}})[:400])
    print('== functions')
    for n in ('AttachToPlayer', 'SetRaised', 'ShowChecklist'):
        add_fn(n)
    add_param('SetRaised', 'Want', 'bool', True)
    add_param('ShowChecklist', 'Header', 'string', True)
    add_param('ShowChecklist', 'Body', 'string', True)
    add_param('ShowChecklist', 'Footer', 'string', True)
    print('== graphs')
    write('AttachToPlayer', ATTACH)
    write('SetRaised', RAISED)
    write('ShowChecklist', SHOW)
    write('EventGraph', BEGIN)
    print('== F key')
    key_nodes()
    print('  compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': BP}})[:600])
    print('  readback:', M.bp('read_graph_dsl', {'graph': g('EventGraph')})[:900])


if __name__ == '__main__':
    main()
