"""Search Blueprint node type ids by name filter."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

CTX = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager:EventGraph'


def find(*filters, ctx=CTX, limit=2000):
    for f in filters:
        r = M.bp('find_node_types', {'graph': {'refPath': ctx}, 'type_id_filter': f,
                                     'context_pins': []})
        try:
            d = json.loads(r)
        except Exception:
            print('##', f, r[:300])
            continue
        ids = d.get('returnValue', [])
        if isinstance(ids, dict):
            ids = ids.get('type_ids') or ids.get('typeIds') or list(ids.values())[0]
        print('## ' + f)
        for i in (ids or [])[:limit]:
            print('   ', i)
    return


if __name__ == '__main__':
    M.init()
    find(*sys.argv[1:])
