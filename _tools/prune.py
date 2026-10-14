"""Report orphaned (unreachable) nodes in a Blueprint graph.

write_graph_dsl appends statements, so repeated writes leave dead chains behind.

WARNING - do not delete nodes with this.  The tool only reports pin connections
on one side, so genuine data nodes (variable getters feeding an expression) look
unreachable and deleting them silently breaks the graph.  Use it as a report,
and rebuild a graph by clearing every non-entry node and writing it once with
Tools/rebuild.py instead.
"""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M


def nodes(graph):
    r = json.loads(M.bp('find_nodes', {'graph': {'refPath': graph}, 'title': ''}))
    return r['returnValue']


def infos(graph, ns):
    if not ns:
        return []
    return json.loads(M.bp('get_node_infos', {'nodes': ns}))['returnValue']


def prune(graph, dry=True):
    ns = nodes(graph)
    nf = infos(graph, ns)
    by_ref = {}
    for n in nf:
        by_ref[n['node']['refPath']] = n
    edges = {}
    for n in nf:
        src = n['node']['refPath']
        for p in n.get('output_pins', []):
            for c in p.get('connected_pins', []):
                tgt = c['node']['refPath']
                edges.setdefault(src, set()).add(tgt)
    seen = set()
    def is_root(n):
        t = n.get('type_id', '')
        if t.startswith('AddEvent') or 'KeyboardEvents' in t:
            return True
        # function graphs: the entry node has an unconnected exec input and a
        # connected exec output.
        ins = [p for p in n.get('input_pins', []) if p.get('type_id') == 'Exec']
        outs = [p for p in n.get('output_pins', []) if p.get('type_id') == 'Exec']
        return not ins and any(p['connected_pins'] for p in outs)

    stack = [n['node']['refPath'] for n in nf if is_root(n)]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        for nxt in edges.get(cur, ()):  # only for nodes present in the graph
            if nxt in by_ref:
                stack.append(nxt)
    dead = [r for r in by_ref if r not in seen]
    print('  ', graph.split(':')[-1], 'nodes', len(by_ref), 'reachable', len(seen), 'dead', len(dead))
    if not dry:
        for r in dead:
            M.bp('delete_node', {'node': {'refPath': r}})
    return dead


if __name__ == '__main__':
    M.init()
    args = sys.argv[1:]
    dry = '--apply' not in args
    for g in [a for a in args if a != '--apply']:
        prune(g, dry=dry)
