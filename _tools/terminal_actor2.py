"""T1.4 terminal: BP_Terminal.ShowChecklist(Header, Names, States, Footer) + ScreenYaw.

Run:  python _tools/terminal_actor2.py
"""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

BP = '/Game/Substrate/Core/BP_Terminal.BP_Terminal'
CDO = '/Game/Substrate/Core/BP_Terminal.Default__BP_Terminal_C'


def g(n):
    return {'refPath': BP + ':' + n}


def compile_bp():
    print('  compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': BP}})[:250])


SHOW = '''(fn ShowChecklist (Header Names States Footer)
  (bind w (UserInterface|GetUserWidgetObject :self (Variables|Default|GetScreen)))
  (bind tw (Utilities|Casting|CastToWBP_Terminal :Object w)
    (:then
      (Class|WBPTerminal|SetChecklist
        :self tw
        :Header Header
        :Names Names
        :States States
        :Footer Footer))
    (:CastFailed
      (Development|PrintString :InString "TERMINAL: widget missing" :Duration 3.0))))
'''

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
      (Transformation|SetActorRelativeRotation
        :self self
        :NewRelativeRotation (Math|Rotator|MakeRotator
          :Pitch 0.0
          :Yaw (Variables|Default|GetScreenYaw)
          :Roll 0.0))
      (Variables|Default|SetBound true)
      (CallFunction|ApplyRaised :self self :Want false))
    (:CastFailed
      (Development|PrintString :InString "TERMINAL: no camera to attach to" :Duration 3.0))))
'''


def main():
    M.init()
    print('rm ShowChecklist ->', M.bp('remove_function_graph',
                                      {'blueprint': {'refPath': BP},
                                       'graph_name': 'ShowChecklist'})[:120])
    compile_bp()
    print('add ShowChecklist ->', M.bp('add_function_graph',
                                       {'blueprint': {'refPath': BP},
                                        'graph_name': 'ShowChecklist'})[:180])
    for p in ('Header', 'Names', 'States', 'Footer'):
        M.bp('add_function_param', {'graph': g('ShowChecklist'), 'param_name': p,
                                    'param_type': 'string', 'input_param': True})
    print('add ScreenYaw ->', M.bp('add_variable', {'blueprint': {'refPath': BP},
                                                   'name': 'ScreenYaw',
                                                   'type_name': 'Float'})[:120])
    M.bp('set_variable_instance_editable', {'blueprint': {'refPath': BP},
                                            'variable_name': 'ScreenYaw',
                                            'instance_editable': True})
    compile_bp()
    print('set ScreenYaw default ->', M.call('call_tool', {
        'toolset_name': M.OBJ, 'tool_name': 'set_properties',
        'arguments': {'instance': {'refPath': CDO},
                      'values': json.dumps({'ScreenYaw': 180.0})}})[:150])
    for n, code in (('ShowChecklist', SHOW), ('AttachToPlayer', ATTACH)):
        print('  graph', n, '->', M.bp('write_graph_dsl', {'graph': g(n), 'code': code})[:300])
    compile_bp()
    for n in ('ShowChecklist', 'AttachToPlayer', 'Toggle', 'ApplyRaised'):
        print('==', n)
        print(json.loads(M.bp('read_graph_dsl', {'graph': g(n)}))['returnValue'][:700])


if __name__ == '__main__':
    main()
