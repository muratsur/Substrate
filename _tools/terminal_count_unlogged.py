"""The terminal's "CLOSE SHIFT: BLOCKED (N left)" counted wrongly-logged rows too, so it changed the instant a guess
was wrong and players could find anomalies by flagging rows one at a time and watching the number (playtest
2026-11-08). The terminal now counts only rows not yet logged (or photographed); once all are logged it says
"ALL ROWS LOGGED - CLOSE AT CONSOLE" whether they are right or not. Wrong answers surface only at the airlocks and
the close-shift console. TerminalRemaining (which still counts wrong rows) is unchanged and still drives OpenWestGate.
Usage: python _tools/terminal_count_unlogged.py   (PIE stopped). Saves BP_RoundManager. Re-runnable."""
import sys
sys.path.insert(0, '_tools')
import mcpx as M
from aim_and_airlock_feedback import RM, FIX, add_var, patch, ok

COUNT = '''(Variables|Default|SetTerminalUnlogged 0)
  (for _unlogged_actor (Actor|GetAllActorsOfClass "%s")
    (bind _unlogged_fixture (Utilities|Casting|CastToBP_Fixture _unlogged_actor))
    (if (and (== (Class|BPFixture|GetLogResult _unlogged_fixture) 0) (and (<= (Class|BPFixture|GetRowOrder _unlogged_fixture) (Variables|Default|GetRequiredRowMax)) (not (Utilities|String|Contains (Variables|Default|GetPhotoIDs) (Utilities|String|Append (Utilities|String|Append "|" (Utilities|String|ToString(Name) (Class|BPFixture|GetFixtureID _unlogged_fixture))) "|")))))
      (Variables|Default|SetTerminalUnlogged (+ (Variables|Default|GetTerminalUnlogged) 1))))
  (if (Variables|Default|GetDebugTerminal)''' % FIX

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    add_var(RM, 'TerminalUnlogged', 'int')
    patch(RM, 'RefreshTerminal', '(if (Variables|Default|GetDebugTerminal)', COUNT, 'SetTerminalUnlogged 0')
    patch(RM, 'RefreshTerminal', '(bind _terminalremaining (Variables|Default|GetTerminalRemaining))',
          '(bind _terminalremaining (Variables|Default|GetTerminalUnlogged))', 'GetTerminalUnlogged))')
    patch(RM, 'RefreshTerminal', '"CLOSE SHIFT: READY"', '"ALL ROWS LOGGED - CLOSE AT CONSOLE"', 'ALL ROWS LOGGED')
    patch(RM, 'RefreshTerminal', '" left)"', '" TO LOG)"', 'TO LOG)')
    print('compile', ok(M.bp('compile_blueprint', {'blueprint': {'refPath': RM}}), 'compile')[:120])
    print('save', M.call('call_tool', {'toolset_name': M.AT, 'tool_name': 'save_assets', 'arguments': {'asset_paths': [RM]}})[:100])
