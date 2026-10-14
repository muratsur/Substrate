"""Print input/output pin names for Blueprint node type ids."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

CTX = '/Game/Substrate/Anomalies/BP_AnomalySocket.BP_AnomalySocket:EventGraph'


def pins(*type_ids, ctx=CTX):
    for t in type_ids:
        r = M.bp('get_node_type_pins', {'graph': {'refPath': ctx}, 'type_id': t})
        try:
            d = json.loads(r)
        except Exception:
            print('##', t, 'ERR', r[:200])
            continue
        v = d.get('returnValue')
        print('##', t)
        if isinstance(v, dict):
            for k in ('input_pins', 'output_pins', 'inputs', 'outputs'):
                if k in v:
                    print('  ', k, ':', [p.get('name') for p in v[k]])
        else:
            print('  ', v)


if __name__ == '__main__':
    M.init()
    pins(*sys.argv[1:])
