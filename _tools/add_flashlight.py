"""Handheld flashlight (DESIGN.md: legibility without brightening the level). Two SpotLights tagged 'Flashlight' are
placed in L_SectorC, hidden (= off): a tight beam and a wide dim spill, like a real torch's hotspot and halo.
BP_RoundManager.AttachFlashlight (0.5 s after each StartShift) snaps them to the player camera, low and to the right like
a hand-held torch, and starts FlashlightSway, which eases their rotation toward the view so the beam lags when you turn.
L toggles it (ToggleFlashlight, key node built with create_node since the
DSL can't make key events). Starts off; keeps its state across shifts.
Usage: python _tools/add_flashlight.py   (PIE stopped), then save L_SectorC + BP_RoundManager."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
M.init()
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
G = {'refPath': RM + ':EventGraph'}
call = lambda tool, args: json.loads(M.bp(tool, args))['returnValue']
read = lambda g: json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': g}})).get('returnValue', '')
WARM = {'r': 1.0, 'g': 0.93, 'b': 0.82, 'a': 1.0}
LIGHTS = {  # label: properties; re-running re-applies them
    # tuned in a packaged Development build (auto-exposure there is far brighter than PIE); 1500 cd bloomed over the
    # terminal when a wall was close, so 1000
    # fog scattering fills the view with a white cone
    'Flashlight': {'Intensity': 1000.0, 'IntensityUnits': 'Candelas', 'AttenuationRadius': 3000.0, 'InnerConeAngle': 5.0,
                   'OuterConeAngle': 16.0, 'LightColor': WARM, 'VolumetricScatteringIntensity': 0.0, 'CastShadows': True,
                   'IESTexture': {'refPath': '/Engine/EngineLightProfiles/NarrowComplex_IES.NarrowComplex_IES'}, 'bUseIESBrightness': False},
    'FlashlightSpill': {'Intensity': 200.0, 'IntensityUnits': 'Candelas', 'AttenuationRadius': 1500.0, 'InnerConeAngle': 14.0,
                        'OuterConeAngle': 48.0, 'LightColor': WARM, 'VolumetricScatteringIntensity': 0.0, 'CastShadows': False}}
TERMINAL = '/Game/Substrate/Maps/L_SectorC.L_SectorC:PersistentLevel.BP_Terminal_C_0'
HAND = (40.0, 10.0, -6.0)   # camera-relative: forward, right, down; any closer and the first-person arms shade the beam out

def write(g, code):
    before = read(RM + ':' + g)
    print(g, '->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':' + g}, 'code': code})[:300])
    print(''.join(difflib.unified_diff(before.splitlines(True), read(RM + ':' + g).splitlines(True), 'before', 'after')))

def place():
    for label, props in LIGHTS.items():
        found = json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'find_actors', 'arguments': {'name': label, 'tag': 'Flashlight', 'collision_channels': []}})).get('returnValue') or []
        found = [a['refPath'] for a in found if M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'get_label', 'arguments': {'actor': {'refPath': a['refPath']}}}).find('"' + label + '"') >= 0]
        if found: ref = found[0]
        else:
            ref = json.loads(M.call('call_tool', {'toolset_name': M.SCN, 'tool_name': 'add_to_scene_from_class', 'arguments': {
                'actor_type': {'refPath': '/Script/Engine.SpotLight'}, 'name': label,
                'xform': {'location': {'x': 0.0, 'y': 1400.0, 'z': 400.0}, 'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0}, 'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}}}))['returnValue']['refPath']
            M.call('call_tool', {'toolset_name': M.ACT, 'tool_name': 'add_tag', 'arguments': {'actor': {'refPath': ref}, 'tag': 'Flashlight'}})
            M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': ref}, 'values': json.dumps({'bHidden': True})}})
        lc = ref + '.LightComponent0'
        print(label, ref.split('.')[-1], M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': lc}, 'values': json.dumps(dict(props, Mobility='Movable'))}})[:100])
    # the torch sits behind the raised terminal and blew it out to glare: move the terminal to lighting channel 1 only
    # (string form: the dict form clears every channel)
    for c in ('Body', 'Screen'):
        print(c, M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': TERMINAL + '.' + c}, 'values': json.dumps({'LightingChannels': '(bChannel0=False,bChannel1=True,bChannel2=False)'})}})[:100])

CODE = {
    'AttachFlashlight': '''(fn AttachFlashlight ()
  (bind _cam (Actor|GetComponentByClass :self (Game|GetPlayerPawn 0) :ComponentClass "/Script/Engine.CameraComponent"))
  (for f (Actor|GetAllActorsWithTag "Flashlight")
    (Transformation|AttachActorToComponent :self f :Parent _cam :SocketName "None" :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
    (Transformation|SetActorRelativeLocation :self f :NewRelativeLocation (Math|Vector|MakeVector %s %s %s))
    (Rendering|SetActorHiddenInGame :self f :bNewHidden (not (Variables|Default|GetFlashlightOn))))
  (Variables|Default|SetLagRot (Pawn|GetControlRotation :self (Game|GetPlayerController 0)))
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "FlashlightSway" :Time 0.016 :bLooping true))
''' % HAND,
    'FlashlightSway': '''(fn FlashlightSway ()
  (bind _r (Math|Interpolation|RInterpTo :Current (Variables|Default|GetLagRot) :Target (Pawn|GetControlRotation :self (Game|GetPlayerController 0)) :DeltaTime (Utilities|Time|GetWorldDeltaSeconds) :InterpSpeed 12.0))
  (Variables|Default|SetLagRot _r)
  (for f (Actor|GetAllActorsWithTag "Flashlight")
    (Transformation|SetActorRotation :self f :NewRotation _r :bTeleportPhysics false)))
''',
    'ToggleFlashlight': '''(fn ToggleFlashlight ()
  (Variables|Default|SetFlashlightOn (not (Variables|Default|GetFlashlightOn)))
  (for f (Actor|GetAllActorsWithTag "Flashlight")
    (Rendering|SetActorHiddenInGame :self f :bNewHidden (not (Variables|Default|GetFlashlightOn))))
  (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Click_on_Button.Click_on_Button" 0.5 (select (Variables|Default|GetFlashlightOn) 1.3 1.1)))
'''}

def bp():
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    have = [v['name'] if isinstance(v, dict) else v for v in call('list_variables', {'blueprint': {'refPath': RM}})]
    if 'FlashlightOn' not in have: B.add_var(RM, 'FlashlightOn', 'bool')
    if 'LagRot' not in have: print('LagRot ->', M.bp('add_struct_variable', {'blueprint': {'refPath': RM}, 'name': 'LagRot', 'struct_type': {'refPath': '/Script/CoreUObject.Rotator'}})[:100])
    for g in CODE:
        try: M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': g})
        except Exception: pass
    B.compile_bp(RM)
    for g, c in CODE.items(): write(g, c)
    s = read(RM + ':StartShift')
    if 'AttachFlashlight' not in s:
        old = '  (Utilities|Time|SetTimerbyFunctionName _self "ShowFTip" 1.0)\n'
        assert s.count(old) == 1
        write('StartShift', s.replace(old, old + '  (Utilities|Time|SetTimerbyFunctionName :Object _self :FunctionName "AttachFlashlight" :Time 0.5)\n'))
    # L key -> ToggleFlashlight
    for k in call('find_nodes', {'graph': G, 'title': '', 'node_class': {'refPath': '/Script/BlueprintGraph.K2Node_InputKey'}}):
        if call('get_node_infos', {'nodes': [k]})[0].get('type_id') == 'Input|KeyboardEvents|L':
            print('L key already wired'); break
    else:
        mk = lambda t, x, y: (lambda n: n if 'refPath' in n else n['node'])(call('create_node', {'graph': G, 'type_id': t, 'pos': {'x': x, 'y': y}}))
        key, fn = mk('Input|KeyboardEvents|L', 0, 2800), mk('CallFunction|ToggleFlashlight', 300, 2800)
        pins = lambda n: {(p['pin_id']['direction'], p['name']): p['pin_id'] for i in [call('get_node_infos', {'nodes': [n]})[0]] for p in i.get('input_pins', []) + i.get('output_pins', [])}
        pk, pf = pins(key), pins(fn)
        print('L ->', M.bp('connect_pins', {'output_pin': pk[('EGPD_Output', 'Pressed')], 'input_pin': pf[('EGPD_Input', 'execute')]})[:120])
    B.compile_bp(RM)

if __name__ == '__main__':
    place(); bp()
