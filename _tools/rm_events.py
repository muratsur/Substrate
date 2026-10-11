import json
BP='editor_toolset.toolsets.blueprint.BlueprintTools'
R='/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
EG={'refPath':R+':EventGraph'}
def base_dsl(debug=False):
    t='  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "DebugTick" :Time 0.3 :bLooping true)\n' if debug else ''
    return '''(event EventBeginPlay
  (CallFunction|StartShift)
%s  (Input|EnableInput :PlayerController (Game|GetPlayerController 0)))

(event Collision|EventActorBeginOverlap (OtherActor)
  (bind ch (Utilities|Casting|CastToCharacter :Object OtherActor)
    (:then
      (CallFunction|TryCloseShift))
    (:CastFailed)))
''' % t
def add_key_nodes(m):
    out=[]
    def node(t,x,y): return json.loads(m.tool(BP,'create_node',{'graph':EG,'type_id':t,'pos':{'x':x,'y':y}}))['returnValue']
    def info(n): return json.loads(m.tool(BP,'get_node_infos',{'nodes':[n]}))['returnValue'][0]
    for key,res,y in (('E',1,600),('Q',2,900)):
        k=node('Input|KeyboardEvents|'+key,0,y); c=node('CallFunction|LogLookedAtFixture',400,y)
        ki,ci=info(k),info(c)
        pressed=next(p for p in ki['output_pins'] if p['name']=='Pressed')
        ex=next(p for p in ci['input_pins'] if p['type_id']=='Exec')
        rp=next(p for p in ci['input_pins'] if p['name']=='Result')
        m.tool(BP,'connect_pins',{'output_pin':pressed['pin_id'],'input_pin':ex['pin_id']})
        m.tool(BP,'set_pin_value',{'pin':rp['pin_id'],'value':str(res)})
