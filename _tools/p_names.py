import sys
sys.path.insert(0, '_tools')
import ue_mcp

SCRIPT = r'''
def run():
    return {"env": "probe"}
'''
# find exact registered tool names via a script that lists them? try calling get_execution_environment again fully
import json
ue_mcp.init()
r = ue_mcp.call('call_tool', {'toolset_name': 'editor_toolset.toolsets.programmatic.ProgrammaticToolset',
                              'tool_name': 'get_execution_environment', 'arguments': {}})
import re
s = str(r)
print(s[:4000])
