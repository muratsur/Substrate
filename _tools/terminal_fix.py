"""T1.4 terminal: repair pass — correct pins, add Toggle, wire the F key.

Run:  python _tools/terminal_fix.py
"""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

BP = '/Game/Substrate/Core/BP_Terminal.BP_Terminal'
EG = '/Game/Substrate/Core/BP_Terminal.BP_Terminal:EventGraph'


def g(name):
    return {'refPath': BP + ':' + name}


def write(name, code):
    r = M.bp('write_graph_dsl', {'graph': g(name), 'code': code})
    print('  graph', name, '->', r[:400])
    return r


def compile_bp():
    print('  compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': BP}})[:300])


TTACH = '''(fn AttachToPlayer ()
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
      (CallFunction|SetRaised :self self :Want false))
    (:CastFailed
      (Development|PrintString :InString "TERMINAL: no camera to attach to" :Duration 3.0))))
'''

RAISED = '''(fn SetRaised (Want)
  (Variables|Default|SetRaised Want)
  (if Want
    (Transformation|SetActorRelativeLocation
      :self self
      :NewRelativeLocation (Variables|Default|GetUpOffset))
    (else
      (Transformation|SetActorRelativeLocation
        :self self
        :NewRelativeLocation (Variables|Default|GetStowOffset))))
  (Rendering|SetActorHiddenInGame :self self :NewHidden (not Want)))
'''

TOGGLE = '''(fn Toggle ()
  (if (Variables|Default|GetRaised)
    (CallFunction|SetRaised :self self :Want false)
    (else
      (CallFunction|SetRaised :self self :Want true))))
'''


def node(t, x, y):
    return json.loads(M.bp('create_node', {'graph': g('EventGraph'), 'type_id': t,
                                          'pos': {'x': x, 'y': y}}))['returnValue']


def info(n):
    return json.loads(M.bp('get_node_infos', {'nodes': [n]}))['returnValue'][0]


def wire_key():
    """F key -> Toggle (drop the half-wired branch from the first pass)."""
    found = json.loads(M.bp('find_nodes', {'graph': g('EventGraph'),
                                           'node_class': ''}))['returnValue']
    for n in found:
        ref = n['refPath'] if isinstance(n, dict) else str(n)
        short = ref.split('.')[-1]
        if short.startswith('K2Node_IfThenElse') or short.startswith('K2Node_VariableGet'):
            print('  drop', short, M.bp('delete_node', {'node': {'refPath': ref}})[:80])
    key = node('Input|KeyboardEvents|F', 0, 700)
    call = node('CallFunction|Toggle', 320, 700)
    ki, ci = info(key), info(call)
    pressed = next(p for p in ki['output_pins'] if p['name'] == 'Pressed')
    ex = next(p for p in ci['input_pins'] if p['type_id'] == 'Exec')
    print('  wire', M.bp('connect_pins', {'output_pin': pressed['pin_id'],
                                          'input_pin': ex['pin_id']})[:120])


def main():
    M.init()
    compile_bp()  # refresh signatures so local-call nodes see their pins
    M.bp('add_function_graph', {'blueprint': {'refPath': BP}, 'graph_name': 'Toggle'})
    write('Toggle', TOGGLE)
    write('AttachToPlayer', TTACH)
    write('SetRaised', RAISED)
    compile_bp()
    wire_key()
    compile_bp()
    for n in ('Toggle', 'AttachToPlayer', 'SetRaised', 'EventGraph'):
        print('== readback', n)
        print(M.bp('read_graph_dsl', {'graph': g(n)})[:700])


if __name__ == '__main__':
    main()
