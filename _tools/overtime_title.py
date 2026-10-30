"""Title on the terminal, and Overtime made reachable.
Overtime (anomaly types 10-13, OvertimeShift, HighestOvertimeShift, StartOvertime, the save fields) existed but nothing
unlocked or started it. Now:
- EventBeginPlay shows the title instead of starting a shift: the terminal comes up in the dome with
  E START SHIFT 00N (continue), Q NEW GAME FROM SHIFT 001, C OVERTIME (best shift, or LOCKED). TitleMode routes the
  E / Q / C handlers (OnEKey, OnQKey, TakePhoto) to TitleContinue / TitleNew / TitleOvertime until a choice is made.
- EndDemo sets OvertimeUnlocked and CompletedSectorD and calls SaveFreshStart (save slot = shift 1 + the unlock), and
  RestartDemo just reopens the level, which lands on the title with Overtime open. NEW GAME keeps the unlock.
Usage: python _tools/overtime_title.py   (PIE stopped), then save BP_RoundManager."""
import sys, json, difflib
sys.path.insert(0, '_tools')
import mcpx as M
import anomaly_build as B
RM = '/Game/Substrate/Core/BP_RoundManager.BP_RoundManager'
SAVE = '/Game/Substrate/Core/BP_SubstrateSave.BP_SubstrateSave_C'
read = lambda g: json.loads(M.bp('read_graph_dsl', {'graph': {'refPath': RM + ':' + g}})).get('returnValue', '')
NL = '(Variables|Default|GetNL)'
SHIFT_NO = '(Utilities|String|Append (select (< (+ (Variables|Default|GetCurrentRound) 1) 10) "00" "0") (Utilities|String|ToString(Integer) (+ (Variables|Default|GetCurrentRound) 1)))'
TITLE_LINES = f'''(Utilities|String|Append (Utilities|String|Append "E   START SHIFT " {SHIFT_NO})
        (Utilities|String|Append {NL} (Utilities|String|Append "Q   NEW GAME FROM SHIFT 001"
        (Utilities|String|Append {NL} (select (Variables|Default|GetOvertimeUnlocked)
          (Utilities|String|Append "C   OVERTIME - BEST SHIFT " (Utilities|String|ToString(Integer) (Variables|Default|GetHighestOvertimeShift)))
          "C   OVERTIME (LOCKED)")))))'''
FUNCS = {
    'ShowTitle': f'''(fn ShowTitle ()
  (Variables|Default|SetTitleMode true)
  (CallFunction|FindTerminal)
  (CallFunction|PushTerminal :Header "SUBSTRATE" :Names
      {TITLE_LINES}
    :States "" :Footer "DEMO 0.9 - ESC: SETTINGS")
  (CallFunction|RaiseTerminal))
''',
    'SaveFreshStart': f'''(fn SaveFreshStart ()
  (bind _s (Utilities|Casting|CastToBP_SubstrateSave (SaveGame|CreateSaveGameObject "{SAVE}")))
  (Class|BPSubstrateSave|ApplySaveData _s 1)
  (Class|BPSubstrateSave|SetOvertimeUnlocked (Variables|Default|GetOvertimeUnlocked) _s)
  (Class|BPSubstrateSave|SetCompletedSectorD (Variables|Default|GetCompletedSectorD) _s)
  (Class|BPSubstrateSave|SetHighestOvertimeShift (Variables|Default|GetHighestOvertimeShift) _s)
  (SaveGame|SaveGameToSlot :SaveGameObject _s :SlotName "Substrate_0" :UserIndex 0))
''',
    'TitleContinue': '''(fn TitleContinue ()
  (Variables|Default|SetTitleMode false)
  (CallFunction|StartShift))
''',
    'TitleNew': '''(fn TitleNew ()
  (Variables|Default|SetTitleMode false)
  (Variables|Default|SetCurrentRound 0)
  (Variables|Default|SetIsOvertime false)
  (Variables|Default|SetOvertimeShift 0)
  (Variables|Default|SetContamination 0)
  (CallFunction|SaveFreshStart)
  (CallFunction|StartShift))
''',
    'TitleOvertime': '''(fn TitleOvertime ()
  (if (Variables|Default|GetOvertimeUnlocked)
    (Variables|Default|SetTitleMode false)
    (CallFunction|StartOvertime)
    (else
      (Audio|PlaySound2D "/Engine/VREditor/Sounds/UI/Invalid_Action.Invalid_Action" 0.6 1.0))))
'''}
BEGINPLAY = '''(event EventBeginPlay
  (bind _self self)
  (CallFunction|LoadShiftState)
  (CallFunction|ShowTitle)
  (Input|EnableInput :self _self :PlayerController (Game|GetPlayerController 0))
  (Utilities|Time|SetTimerbyFunctionName :Object _self :FunctionName "CheckFootstep" :Time 0.05 :bLooping true))
'''

def write(g, code):
    before = read(g)
    print(g, '->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':' + g}, 'code': code})[:200])
    print(''.join(difflib.unified_diff(before.splitlines(True), read(g).splitlines(True), 'before', 'after')))

def photo():
    # C: the photo logic moves to PhotoShot and TakePhoto only routes. Wrapping TakePhoto's own body does not work: it
    # starts with an `if`, and an else whose first statement is an if is read back as elif, which drags the trailing
    # UpdateWayfinding into one branch.
    import add_inspection_camera as CAM
    try: M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': 'PhotoShot'})
    except Exception as e: print('PhotoShot exists:', str(e)[:50])
    B.compile_bp(RM)
    write('PhotoShot', CAM.TAKE.replace('(fn TakePhoto ()', '(fn PhotoShot ()').rstrip()[:-1] + '\n  (CallFunction|UpdateWayfinding))\n')
    B.compile_bp(RM)
    write('TakePhoto', '''(fn TakePhoto ()
  (if (Variables|Default|GetTitleMode)
    (CallFunction|TitleOvertime)
    (else
      (CallFunction|PhotoShot))))
''')

def wrap(g, choice):
    """route a key handler to a title choice while the title is up"""
    s = read(g)
    if 'GetTitleMode' in s: print(g, 'already wraps the title'); return
    # read-back is positional, which would feed the hint text into ShowHint's hidden self pin
    s = s.replace('(CallFunction|ShowHint "', '(CallFunction|ShowHint :Text "').replace('(CallFunction|ShowHint (', '(CallFunction|ShowHint :Text (')
    head, body = s.split('\n', 1)
    body = body.rstrip()
    assert body.endswith(')'), g
    write(g, f'{head}\n  (if (Variables|Default|GetTitleMode)\n    (CallFunction|{choice})\n    (else\n{body[:-1]})))\n')

if __name__ == '__main__':
    M.init()
    assert 'false' in M.app('IsPIERunning', {}), 'stop PIE first'
    have = [v['name'] if isinstance(v, dict) else v for v in json.loads(M.bp('list_variables', {'blueprint': {'refPath': RM}}))['returnValue']]
    if 'TitleMode' not in have: B.add_var(RM, 'TitleMode', 'bool')
    for g in FUNCS:
        try: M.bp('add_function_graph', {'blueprint': {'refPath': RM}, 'graph_name': g})
        except Exception as e: print(g, 'exists:', str(e)[:50])
    B.compile_bp(RM)
    for g, c in FUNCS.items(): write(g, c)
    B.compile_bp(RM)
    wrap('OnEKey', 'TitleContinue'); wrap('OnQKey', 'TitleNew')
    photo()
    print('BeginPlay ->', M.bp('write_graph_dsl', {'graph': {'refPath': RM + ':EventGraph'}, 'code': BEGINPLAY})[:200])
    B.compile_bp(RM)
