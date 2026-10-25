"""Checklist corruption (anomaly type 8, DESIGN.md table row 9: 'renames one you know'). Apply case 8 only marked the
socket applied and nothing read it, so the terminal never changed. BP_AnomalySocket's Apply/Revert cannot be round-tripped
through the graph DSL, so the effect lives in BP_RoundManager.AddRowIfMatch instead: while an applied type-8 socket targets
a fixture, that fixture's row shows the socket's Note (Socket_Checklist_C3: 'C-03 DO NOT INSPECT') instead of its FixtureID.
Revert already clears Applied, so the row restores itself; the fixture's real ID never changes.
(wire_overtime_anomalies.py imports CODE and extends the type check to 13.)"""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M

RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
G = RM + ':AddRowIfMatch'
CODE = '''(fn AddRowIfMatch (Fixture Row)
  (bind _asbp_fixture (Utilities|Casting|CastToBP_Fixture Fixture))
  (if (== (Class|BPFixture|GetRowOrder _asbp_fixture) Row)
    (Variables|Default|SetRowLabel (Utilities|String|ToString(Name) (Class|BPFixture|GetFixtureID _asbp_fixture)))
    (bind _sockets (Actor|GetAllActorsOfClass "/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket_C"))
    (for _socket_actor _sockets
      (bind _socket (Utilities|Casting|CastToBP_AnomalySocket _socket_actor))
      (if (and (Class|BPAnomalySocket|GetApplied _socket) (and (== (Class|BPAnomalySocket|GetAnomalyType _socket) 8) (== (Class|BPAnomalySocket|GetTarget _socket) Fixture)))
        (Variables|Default|SetRowLabel (Class|BPAnomalySocket|GetNote _socket))))
    (Variables|Default|SetTerminalNames (Utilities|String|Append (Variables|Default|GetTerminalNames) (Utilities|String|Append (Variables|Default|GetRowLabel) (Variables|Default|GetNL))))
    (Variables|Default|SetTerminalStates (Utilities|String|Append (Variables|Default|GetTerminalStates) (Utilities|String|Append (select (== (Class|BPFixture|GetLogResult _asbp_fixture) 0) "[ ]" (select (== (Class|BPFixture|GetLogResult _asbp_fixture) 1) "[PASS]" "[FLAG]")) (Variables|Default|GetNL))))
    (bind _correct (Class|BPFixture|IsLoggedCorrectly _asbp_fixture))
    (if (and (not _correct) (<= Row (Variables|Default|GetRequiredRowMax)))
      (Variables|Default|SetTerminalRemaining (+ (Variables|Default|GetTerminalRemaining) 1)))))
'''

if __name__ == '__main__':
    M.init()
    read = lambda: json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'read_graph_dsl', 'arguments': {'graph': {'refPath': G}}})).get('returnValue', '')
    vars_ = json.loads(M.call('call_tool', {'toolset_name': M.BP, 'tool_name': 'list_variables', 'arguments': {'blueprint': {'refPath': RM}}}))['returnValue']
    if 'RowLabel' not in vars_:
        print('add RowLabel ->', M.bp('add_variable', {'blueprint': {'refPath': RM}, 'name': 'RowLabel', 'type_name': 'string'})[:120])
    before = read()
    print(M.bp('write_graph_dsl', {'graph': {'refPath': G}, 'code': CODE})[:300])
    print('compile ->', M.bp('compile_blueprint', {'blueprint': {'refPath': RM}})[:200])
    print(''.join(difflib.unified_diff(before.splitlines(True), read().splitlines(True), 'before', 'after')))
