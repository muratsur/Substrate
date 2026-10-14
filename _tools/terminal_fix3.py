"""T1.4 terminal: rename SetRaised -> ApplyRaised (avoids the Set<Var> collision).

Run:  python _tools/terminal_fix3.py
"""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

BP = '/Game/Substrate/Core/BP_Terminal.BP_Terminal'
EG = BP + ':EventGraph'


def g(name):
    return {'refPath': BP + ':' + name}


def write(name, code):
    r = M.bp('write_graph_dsl', {'graph': g(name), 'code': code})
    print('  graph', name, '->', r[:300])
    return r


APPLY = '''(fn ApplyRaised (Want)
  (Variables|Default|SetRaised Want)
  (if Want
    (Transformation|SetActorRelativeLocation
      :self self
      :NewRelativeLocation (Variables|Default|GetUpOffset))
    (else
      (Transformation|SetActorRelativeLocation
        :self self
        :NewRelativeLocation (Variables|Default|GetStowOffset))))
  (Rendering|SetActorHiddenInGame :self self :bNewHidden (not Want)))
'''

TOGGLE = '''(fn Toggle ()
  (if (Variables|Default|GetRaised)
    (CallFunction|ApplyRaised :self self :Want false)
    (else
      (CallFunction|ApplyRaised :self self :Want true))))
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
      (Variables|Default|SetBound true)
      (CallFunction|ApplyRaised :self self :Want false))
    (:CastFailed
      (Development|PrintString :InString "TERMINAL: no camera to attach to" :Duration 3.0))))
'''


def main():
    M.init()
    # drop the colliding function, add the renamed one
    print('  rm SetRaised ->', M.bp('remove_function_graph',
                                     {'blueprint': {'refPath': BP},
                                      'graph_name': 'SetRaised'})[:150])
    print('  add ApplyRaised ->', M.bp('add_function_graph',
                                        {'blueprint': {'refPath': BP},
                                         'graph_name': 'ApplyRaised'})[:150])
    M.bp('add_function_param', {'graph': g('ApplyRaised'), 'param_name': 'Want',
                                'param_type': 'bool', 'input_param': True})
    print('  compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': BP}})[:200])
    write('ApplyRaised', APPLY)
    write('Toggle', TOGGLE)
    write('AttachToPlayer', ATTACH)
    print('  compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': BP}})[:300])
    # confirm the F key actually reaches Toggle
    keys = json.loads(M.bp('find_nodes', {'graph': {'refPath': EG}, 'title': 'F'}))['returnValue']
    print('  key -> subgraph:', M.bp('get_connected_subgraph',
                                     {'node': {'refPath': keys[0]['refPath']}})[:500])
    for n in ('ApplyRaised', 'Toggle', 'AttachToPlayer'):
        print('== readback', n)
        print(M.bp('read_graph_dsl', {'graph': g(n)})[:700])


if __name__ == '__main__':
    main()
