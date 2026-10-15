"""Phase 3 Step 4: Update BP_AnomalyDirector PickType and Budgets for Rounds 3-8."""
import sys
import json
sys.path.insert(0, '_tools')
import mcpx as M

DIR = '/Game/Substrate/Anomalies/BP_AnomalyDirector.BP_AnomalyDirector'

def balance(code):
    depth = code.count('(') - code.count(')')
    if depth > 0:
        code = code.rstrip('\n') + ')' * depth + '\n'
    return code

def main():
    M.init()
    print('--- Step 4: Updating BP_AnomalyDirector PickType and Budgets ---')

    PICKTYPE = '''(fn PickType (Round)
  (bind r3 (Math|Random|RandomIntegerInRange 0 2))
  (bind r5 (Math|Random|RandomIntegerInRange 0 6))
  (bind c5 (select (== r5 6) 7 r5))
  (bind r6 (Math|Random|RandomIntegerInRange 0 9))
  (return (select (<= Round 2) 0 (select (== Round 3) r3 (select (<= Round 5) c5 r6)))))
'''

    GET_BUDGET_MIN = '''(fn GetBudgetMin (Round)
  (return (select (<= Round 1) 0 (select (<= Round 5) 1 2))))
'''

    GET_BUDGET_MAX = '''(fn GetBudgetMax (Round)
  (return (select (<= Round 1) 0 (select (== Round 2) 1 (select (<= Round 5) 2 3)))))
'''

    print('Writing PickType...')
    r_pt = M.bp('write_graph_dsl', {'graph': {'refPath': f'{DIR}:PickType'}, 'code': balance(PICKTYPE)})
    print('  PickType ->', r_pt[:150])

    print('Writing GetBudgetMin...')
    r_bmin = M.bp('write_graph_dsl', {'graph': {'refPath': f'{DIR}:GetBudgetMin'}, 'code': balance(GET_BUDGET_MIN)})
    print('  GetBudgetMin ->', r_bmin[:150])

    print('Writing GetBudgetMax...')
    r_bmax = M.bp('write_graph_dsl', {'graph': {'refPath': f'{DIR}:GetBudgetMax'}, 'code': balance(GET_BUDGET_MAX)})
    print('  GetBudgetMax ->', r_bmax[:150])

    c = M.bp('compile_blueprint', {'blueprint': {'refPath': DIR}})
    print('compile BP_AnomalyDirector ->', c[:150])

    s = M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': []}})
    print('save dirty ->', s[:100])

if __name__ == '__main__':
    main()
