import sys,json,time; sys.path.insert(0,'.')
import ue_mcp as m; m.init()
import rm_events as E
BP=E.BP; R=E.R; rb={'refPath':R}
F='/Game/Substrate/Core/BP_Fixture.BP_Fixture'
SC='editor_toolset.toolsets.scene.SceneTools'; AT='editor_toolset.toolsets.actor.ActorTools'; EA='EditorToolset.EditorAppToolset'; OT='editor_toolset.toolsets.object.ObjectTools'
CONE,RANGE=0.8,400.0
# patch constants
m.tool(BP,'write_graph_dsl',{'graph':{'refPath':F+':ViewScore'},'code':'''(fn ViewScore (EyeLocation ViewForward)
  ; distance to the viewer if the fixture is within ~37 degrees of the view direction, else a large number
  (bind delta (- (Transformation|GetActorLocation self) EyeLocation))
  (return (select (> (Math|Vector|DotProduct (Math|Vector|Normalize delta) ViewForward) %s) (Math|Vector|VectorLength delta) 9999.0)))
''' % CONE})
m.tool(BP,'compile_blueprint',{'blueprint':{'refPath':F}})
m.tool(BP,'write_graph_dsl',{'graph':{'refPath':R+':LogLookedAtFixture'},'code':'''(fn LogLookedAtFixture (Result)
  (bind pcm (Game|GetPlayerCameraManager 0))
  (bind eye (Camera|GetCameraLocation :self pcm))
  (bind fwd (Math|Vector|GetForwardVector (Camera|GetCameraRotation :self pcm)))
  (Variables|Default|SetBestDist %s)
  (bind fixtures (Actor|GetAllActorsOfClass "/Game/Substrate/Core/BP_Fixture.BP_Fixture_C"))
  (for f fixtures
    (bind fx (Utilities|Casting|CastToBP_Fixture :Object f))
    (bind s (Class|BPFixture|ViewScore :self fx :EyeLocation eye :ViewForward fwd))
    (if (< s (Variables|Default|GetBestDist))
      (Variables|Default|SetBestDist s)
      (Variables|Default|SetBestFixture fx)))
  (if (< (Variables|Default|GetBestDist) %s)
    (Class|BPFixture|LogFixture :self (Variables|Default|GetBestFixture) :Result Result)))
''' % (RANGE,RANGE)})
print('graph:',json.loads(m.tool(BP,'read_graph_dsl',{'graph':{'refPath':R+':LogLookedAtFixture'}}))['returnValue'][-260:])
def find(cls): return json.loads(m.tool(SC,'find_actors',{'name':'','tag':'','collision_channels':[],'actor_type':{'refPath':cls}}))['returnValue']
def P(a,n):
    r=json.loads(m.tool(OT,'get_properties',{'instance':a,'properties':n}))['returnValue']; return json.loads(r) if isinstance(r,str) else r
def loc(a):
    l=json.loads(m.tool(AT,'get_actor_transform',{'actor':a}))['returnValue']['location']; return round(l['x']),round(l['y']),round(l['z'])
def mv(a,t):
    m.tool(AT,'set_actor_transform',{'actor':a,'xform':{'location':{'x':t[0],'y':t[1],'z':t[2]}}}); return loc(a)
print('add DebugTick',m.tool(BP,'add_function_graph',{'blueprint':rb,'graph_name':'DebugTick'})[:30])
m.tool(BP,'write_graph_dsl',{'graph':{'refPath':R+':DebugTick'},'code':'(fn DebugTick ()\n  (CallFunction|LogLookedAtFixture :Result 1))\n'})
m.tool(BP,'write_graph_dsl',{'graph':E.EG,'code':E.base_dsl(True)}); m.tool(BP,'compile_blueprint',{'blueprint':rb})
try:
    m.tool(EA,'StartPIE',{'options':{'bSimulate':False,'warmupSeconds':2}}); time.sleep(1)
    fx=find('/Game/Substrate/Core/BP_Fixture.BP_Fixture_C'); ch=find('/Script/Engine.Character')[0]
    ids={f['refPath']:P(f,['FixtureID'])['FixtureID'][:4] for f in fx}; byid={ids[f['refPath']]:f for f in fx}
    cx,cy,cz=loc(ch)
    def logs(): return sorted(ids[f['refPath']] for f in fx if P(f,['LogResult'])['LogResult'])
    def clear():
        for f in fx: m.tool(OT,'set_properties',{'instance':f,'values':json.dumps({'LogResult':0})})
    far=(9000,9000,400)
    for f in fx: mv(f,far)
    def case(label,placements,expect):
        got={k:mv(byid[k],(cx,cy+d,cz)) for k,d in placements.items()}
        clear(); time.sleep(1.0); res=logs(); print(f'{label:18s} expect {str(expect):10s} logged {res} {"OK" if res==expect else "MISMATCH"}')
        for k in placements: mv(byid[k],far)
    case('near C-03,far C-02',{'C-02':300,'C-03':110},['C-03']); case('near C-02,far C-03',{'C-03':300,'C-02':110},['C-02'])
finally:
    m.tool(EA,'StopPIE',{})
    m.tool(BP,'write_graph_dsl',{'graph':E.EG,'code':E.base_dsl(False)}); E.add_key_nodes(m)
    print('remove DebugTick',m.tool(BP,'remove_function_graph',{'blueprint':rb,'graph_name':'DebugTick'}))
    print('compile',m.tool(BP,'compile_blueprint',{'blueprint':rb}))
