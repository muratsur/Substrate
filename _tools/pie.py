"""Start/stop PIE and grep the output log for Substrate messages."""
import sys
import json
import re
import time
sys.path.insert(0, '_tools')
import mcpx as M

KEYS = ['AnomalyDirector', 'SHIFT', 'ANOMALY', 'GROWTH', 'RoundManager',
        'Airlock', 'Error', 'Warning:', 'LogBlueprintUserMessages']


def log_lines(keys=KEYS, max_entries=4000, tail=40):
    pat = '|'.join(re.escape(k) for k in keys)
    r = M.call('call_tool', {'toolset_name': 'EditorToolset.LogsToolset',
                             'tool_name': 'GetLogEntries',
                             'arguments': {'category': '', 'pattern': pat,
                                           'maxEntries': max_entries}})
    try:
        items = json.loads(r)['returnValue']
    except Exception:
        items = [r]
    if isinstance(items, str):
        items = [items]
    return [i.strip()[:240] for i in items if any(k in i for k in keys)][-tail:]


def start(wait=14):
    print('start:', M.app('StartPIE', {'options': {'bSimulate': False}})[:150])
    time.sleep(wait)
    print('running:', M.app('IsPIERunning', {})[:80])
    for line in log_lines():
        print('LOG:', line)


def stop():
    print('stop:', M.app('StopPIE', {})[:120])
    time.sleep(3)


if __name__ == '__main__':
    M.init()
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'start'
    if cmd == 'start':
        start()
    elif cmd == 'stop':
        stop()
    else:
        for line in log_lines():
            print('LOG:', line)
