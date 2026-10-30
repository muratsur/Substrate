"""Settings in the pause menu: look sensitivity, invert Y, master volume, brightness. Stored in their own save slot
(Substrate_Settings, on BP_SubstrateSave) so NEW GAME and the demo ending never reset them.
- BP_FirstPersonCharacter.Aim multiplies look input by LookSens (0 is read as 1, the unset default) and flips pitch
  when InvertY.
- BP_RoundManager: LoadPlayerSettings / SavePlayerSettings / ApplyPlayerSettings. ApplyPlayerSettings sets the master submix output volume,
  runs the `gamma` console command (1.6..3.0, 2.2 default) and pushes sens + invert to the pawn
  (the cast's branches end the flow, so it goes last).
  Runs from EventBeginPlay (0.3 s timer, so the pawn exists).
- WBP_Pause: a SETTINGS block under the buttons (three sliders and a checkbox). Each change writes the manager's value,
  applies and saves.
Usage: python _tools/settings_menu.py   (PIE stopped), then save BP_SubstrateSave, BP_FirstPersonCharacter,
BP_RoundManager, WBP_Pause."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
CH = '/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter.BP_FirstPersonCharacter'
SV = '/Game/Substrate/Core/BP_SubstrateSave.BP_SubstrateSave'
WP = '/Game/Substrate/UI/WBP_Pause.WBP_Pause'
U = 'UMGToolSet.UMGToolSet'
SLOT = 'Substrate_Settings'
SUBMIX = '/Engine/EngineSounds/Submixes/MasterSubmixDefault.MasterSubmixDefault'
FIELDS = (('LookSens', 'float'), ('InvertY', 'bool'), ('MasterVolume', 'float'), ('Brightness', 'float'))

def read(bp, g): return json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': bp + ':' + g}})).get('returnValue', '')
def write(bp, g, code):
    before = read(bp, g)
    print(g, '->', M.bp('write_graph_dsl', {'graph': {'refPath': bp + ':' + g}, 'code': code})[:250])
    print(''.join(difflib.unified_diff(before.splitlines(True), read(bp, g).splitlines(True), 'before', 'after')))
def vars_of(bp): return [v['name'] if isinstance(v, dict) else v for v in json.loads(M.bp('list_variables', {'blueprint': {'refPath': bp}}))['returnValue']]
def ensure_vars(bp, fields):
    have = vars_of(bp)
    for n, t in fields:
        if n not in have: B.add_var(bp, n, t)
def fn(bp, name, code):
    try: M.bp('add_function_graph', {'blueprint': {'refPath': bp}, 'graph_name': name})
    except Exception as e: print(name, 'exists:', str(e)[:40])
    B.compile_bp(bp)
    write(bp, name, code)

SENS = '(select (> (Variables|Default|GetLookSens) 0.0) (Variables|Default|GetLookSens) 1.0)'
AIM = f'''(fn Aim (Yaw Pitch)
  (Pawn|Input|AddControllerYawInput :Val (* Yaw {SENS}))
  (Pawn|Input|AddControllerPitchInput :Val (* (* Pitch {SENS}) (select (Variables|Default|GetInvertY) -1.0 1.0))))
'''
RM_FUNCS = {
    'LoadPlayerSettings': f'''(fn LoadPlayerSettings ()
  (Variables|Default|SetLookSens 1.0)
  (Variables|Default|SetInvertY false)
  (Variables|Default|SetMasterVolume 1.0)
  (Variables|Default|SetBrightness 2.2)
  (if (SaveGame|DoesSaveGameExist :SlotName "{SLOT}" :UserIndex 0)
    (bind _s (Utilities|Casting|CastToBP_SubstrateSave (SaveGame|LoadGameFromSlot :SlotName "{SLOT}" :UserIndex 0)))
    (Variables|Default|SetLookSens (Class|BPSubstrateSave|GetLookSens _s))
    (Variables|Default|SetInvertY (Class|BPSubstrateSave|GetInvertY _s))
    (Variables|Default|SetMasterVolume (Class|BPSubstrateSave|GetMasterVolume _s))
    (Variables|Default|SetBrightness (Class|BPSubstrateSave|GetBrightness _s))))
''',
    'SavePlayerSettings': f'''(fn SavePlayerSettings ()
  (bind _s (Utilities|Casting|CastToBP_SubstrateSave (SaveGame|CreateSaveGameObject "{SV}_C")))
  (Class|BPSubstrateSave|SetLookSens (Variables|Default|GetLookSens) _s)
  (Class|BPSubstrateSave|SetInvertY (Variables|Default|GetInvertY) _s)
  (Class|BPSubstrateSave|SetMasterVolume (Variables|Default|GetMasterVolume) _s)
  (Class|BPSubstrateSave|SetBrightness (Variables|Default|GetBrightness) _s)
  (SaveGame|SaveGameToSlot :SaveGameObject _s :SlotName "{SLOT}" :UserIndex 0))
''',
    'ApplyPlayerSettings': f'''(fn ApplyPlayerSettings ()
  (Audio|SetSubmixOutputVolume(lineargain) :self "{SUBMIX}" :InOutputVolume (Variables|Default|GetMasterVolume))
  (Development|ExecuteConsoleCommand :Command (Utilities|String|Append "gamma " (Utilities|String|ToString(Float) (Variables|Default|GetBrightness))))
  (bind _p (Utilities|Casting|CastToBP_FirstPersonCharacter (Game|GetPlayerPawn 0))
    (:then
      (Class|BPFirstPersonCharacter|SetLookSens (Variables|Default|GetLookSens) _p)
      (Class|BPFirstPersonCharacter|SetInvertY (Variables|Default|GetInvertY) _p))
    (:CastFailed)))
'''}

def clear_old():
    # the first version named these LoadSettings / SaveSettings / ApplySettings, and CallFunction|LoadSettings resolved to
    # the engine's GameUserSettings::LoadSettings; the graphs cannot be deleted through the toolset, so they are emptied
    for g in ('LoadSettings', 'SaveSettings', 'ApplySettings'):
        if g in [x['refPath'].split(':')[-1] for x in json.loads(M.bp('list_graphs', {'blueprint': {'refPath': RM}}))['returnValue']]:
            M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':' + g}, 'code': f'(fn {g} ())\n'})

def blueprints():
    ensure_vars(SV, FIELDS); B.compile_bp(SV)
    ensure_vars(CH, (('LookSens', 'float'), ('InvertY', 'bool'))); B.compile_bp(CH)
    write(CH, 'Aim', AIM); B.compile_bp(CH)
    ensure_vars(RM, FIELDS); B.compile_bp(RM)
    for name, code in RM_FUNCS.items(): fn(RM, name, code)
    B.compile_bp(RM)
    s = read(RM, 'EventGraph')
    if 'LoadPlayerSettings' not in s or 'Settings|LoadSettings' in s:
        import overtime_title as O
        begin = O.BEGINPLAY.replace('  (CallFunction|ShowTitle)\n', '  (CallFunction|ShowTitle)\n  (CallFunction|LoadPlayerSettings)\n'
            '  (Utilities|Time|SetTimerbyFunctionName :Object _self :FunctionName "ApplyPlayerSettings" :Time 0.3)\n')
        print('BeginPlay ->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':EventGraph'}, 'code': begin})[:200])
    B.compile_bp(RM)

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    clear_old(); blueprints()

# ---- pause menu widgets -------------------------------------------------------------------------------------------
ROWS = (('SldSens', 'LOOK SENSITIVITY', '/Script/UMG.Slider', 0.2, 3.0),
        ('SldVolume', 'VOLUME', '/Script/UMG.Slider', 0.0, 1.0),
        ('SldBright', 'BRIGHTNESS', '/Script/UMG.Slider', 1.6, 3.0),
        ('ChkInvert', 'INVERT LOOK Y', '/Script/UMG.CheckBox', None, None))
WT = WP + ':WidgetTree.'

def u(tool, args):
    r = M.call('call_tool', {'toolset_name': U, 'tool_name': tool, 'arguments': args})
    try: return json.loads(r).get('returnValue')
    except ValueError: raise RuntimeError(f'{tool}: {r[:300]}')

def setp(ref, vals):
    return M.call('call_tool', {'toolset_name': M.OBJ, 'tool_name': 'set_properties', 'arguments': {'instance': {'refPath': ref}, 'values': json.dumps(vals)}})[:80]

def widgets():
    names = [w['widgetName'] for w in u('GetWidgets', {'widgetBlueprint': {'refPath': WP}})['widgets']]
    add = lambda cls, name, parent: u('AddWidget', {'widgetBlueprint': {'refPath': WP}, 'widgetClass': {'refPath': cls}, 'widgetDisplayName': name, 'parentWidget': {'refPath': parent}})
    if 'TxtSettings' not in names:
        w = add('/Script/UMG.TextBlock', 'TxtSettings', WT + 'MenuBox')
        print('header', setp(w['widget']['refPath'], {'Text': 'SETTINGS', 'Font': {'Size': 18}}))
    for var, label, cls, lo, hi in ROWS:
        if var in names: print(var, 'exists'); continue
        row = add('/Script/UMG.HorizontalBox', 'Row_' + var, WT + 'MenuBox')
        t = add('/Script/UMG.TextBlock', 'Lbl_' + var, row['widget']['refPath'])
        setp(t['widget']['refPath'], {'Text': label, 'MinDesiredWidth': 260.0, 'Font': {'Size': 14}})
        c = add(cls, var, row['widget']['refPath'])
        u('ToggleWidgetAsVariable', {'widgetBlueprint': {'refPath': WP}, 'widget': c['widget'], 'bIsVariable': True})
        if lo is not None:
            print(var, setp(c['widget']['refPath'], {'MinValue': lo, 'MaxValue': hi, 'Value': lo}),
                  setp(c['slot']['refPath'], {'Size': {'SizeRule': 'Fill', 'Value': 1.0}}))
    r = M.call('call_tool', {'toolset_name': U, 'tool_name': 'CompileWidgetBlueprint', 'arguments': {'widgetBlueprint': {'refPath': WP}}})
    print('compile', r[:200])

RMC = RM + '_C'
CAST_RM = f'(Utilities|Casting|CastToBP_RoundManager (Actor|GetActorOfClass "{RMC}"))'
def handler(event, setter, value):
    return f'''(event {event}
  (bind _rm {CAST_RM}
    (:then
      (Class|BPRoundManager|{setter} {value} _rm)
      (Class|BPRoundManager|ApplyPlayerSettings :self _rm)
      (Class|BPRoundManager|SavePlayerSettings :self _rm))
    (:CastFailed)))
'''
EVENTS = [handler('OnValueChanged(SldSens) (Value)', 'SetLookSens', 'Value'),
          handler('OnValueChanged(SldVolume) (Value)', 'SetMasterVolume', 'Value'),
          handler('OnValueChanged(SldBright) (Value)', 'SetBrightness', 'Value'),
          handler('OnCheckStateChanged(ChkInvert) (bIsChecked)', 'SetInvertY', 'bIsChecked'),
          # Construct also shows the stored values (its first three lines are the menu's original body)
          f'''(event UserInterface|EventConstruct
  (Variables|Default|SetConfirmRestart false)
  (Variables|Default|SetConfirmQuit false)
  (Widget|SetText(Text) (Variables|WBP_Pause|GetTxtConfirm) (Utilities|Text|ToText(String) ""))
  (bind _rm {CAST_RM}
    (:then
      (Class|Slider|SetValue :self (Variables|WBP_Pause|GetSldSens) :Value (Class|BPRoundManager|GetLookSens _rm))
      (Class|Slider|SetValue :self (Variables|WBP_Pause|GetSldVolume) :Value (Class|BPRoundManager|GetMasterVolume _rm))
      (Class|Slider|SetValue :self (Variables|WBP_Pause|GetSldBright) :Value (Class|BPRoundManager|GetBrightness _rm))
      (Widget|SetIsChecked :self (Variables|WBP_Pause|GetChkInvert) :InIsChecked (Class|BPRoundManager|GetInvertY _rm)))
    (:CastFailed)))
''']

def events():
    for code in EVENTS:
        print(code.split('\n')[0], '->', M.bp('write_graph_dsl', {'graph': {'refPath': WP + ':EventGraph'}, 'code': code})[:250])
    print('compile', M.call('call_tool', {'toolset_name': U, 'tool_name': 'CompileWidgetBlueprint', 'arguments': {'widgetBlueprint': {'refPath': WP}}})[:200])
