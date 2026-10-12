import json,urllib.request
URL='http://127.0.0.1:8000/mcp'
_sid=None
def _post(obj):
    global _sid
    h={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
    if _sid: h['Mcp-Session-Id']=_sid
    r=urllib.request.urlopen(urllib.request.Request(URL,json.dumps(obj).encode(),h),timeout=120)
    _sid=_sid or r.headers.get('Mcp-Session-Id')
    t=r.read().decode()
    return json.loads(t) if t.strip() else None
def init():
    _post({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"claude-code","version":"1"}}})
    _post({"jsonrpc":"2.0","method":"notifications/initialized"})
def call(name,args=None):
    r=_post({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":name,"arguments":args or {}}})
    if 'error' in r: return r['error']
    return ''.join(c.get('text','') for c in r['result']['content'])
def tool(toolset,name,args=None):
    return call('call_tool',{'toolset_name':toolset,'tool_name':name,'arguments':args or {}})
