"""T1.4 terminal: finish the actor graph (orphan cleanup, F key, SetRaised pin).

Run:  python _tools/terminal_fix2.py
"""
import sys, json
sys.path.insert(0, '_tools')
import mcpx as M

BP = '/Game/Substrate/Core/BP_Terminal.BP_Terminal'
EG = BP + ':EventGraph'

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
  (Rendering|SetActorHiddenInGame :self self :bNewHidden (not Want)))
'''


def nodes(title=''):
    return json.loads(M.bp('find_nodes', {'graph': {'refPath': EG}, 'title': title}))['returnValue']


def info(n):
    return json.loads(M.bp('get_node_infos', {'nodes': [n]}))['returnValue'][0]


def main():
    M.init()
    # 1. orphans from the first pass
    for t in ('Branch', 'Get Raised'):
        for n in nodes(t):
            ref = n['refPath'] if isinstance(n, dict) else n
            print('  drop', ref.split('.')[-1], M.bp('delete_node', {'node': {'refPath': ref}})[:80])
    # 2. SetRaised with the real pin name
    print('  SetRaised ->', M.bp('write_graph_dsl', {'graph': {'refPath': BP + ':SetRaised'},
                                                    'code': RAISED})[:300])
    # 3. F key -> Toggle
    call = json.loads(M.bp('create_node', {'graph': {'refPath': EG}, 'type_id': 'CallFunction|Toggle',
                                          'pos': {'x': 340, 'y': 700}}))['returnValue']
    keys = nodes('F')
    print('  key nodes:', [k['refPath'].split('.')[-1] for k in keys])
    ki, ci = info(keys[0]), info(call)
    pressed = next(p for p in ki['output_pins'] if p['name'] == 'Pressed')
    ex = next(p for p in ci['input_pins'] if p['type_id'] == 'Exec')
    print('  wire', M.bp('connect_pins', {'output_pin': pressed['pin_id'],
                                          'input_pin': ex['pin_id']})[:120])
    print('  compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': BP}})[:400])
    for n in ('SetRaised', 'AttachToPlayer', 'EventGraph'):
        print('== readback', n)
        print(M.bp('read_graph_dsl', {'graph': {'refPath': BP + ':' + n}})[:800])


if __name__ == '__main__':
    main()
