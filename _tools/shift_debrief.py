"""Add the successful-shift debrief Blueprint flow.

With L_SectorC open in Unreal and PIE stopped, run:
    python _tools/shift_debrief.py
Only writes the debrief, its continuation, and the success transition in TryCloseShift.
Aborts on failed graph writes or mismatched readback; review the Blueprint Compiler Results.
"""
import json
import sys

sys.path.insert(0, "_tools")
import mcpx as M

RM = "/Game/Substrate/Core/BP_RoundManager.BP_RoundManager"
RECORD_MARKER = "(CallFunction|RecordDiscoveredAnomalies)"
FAILURE_MARKER = "(CallFunction|OnShiftAuditFailed)"

SHOW_DEBRIEF = '''(fn ShowShiftDebrief ()
  (Variables|Default|SetShiftOpen false)
  (bind _debrief_round (Variables|Default|GetCurrentRound))
  (bind _debrief_round_text (Utilities|String|ToString(Integer) _debrief_round))
  (bind _debrief_round_padded (Utilities|String|Append (select (< _debrief_round 10) "00" (select (< _debrief_round 100) "0" "")) _debrief_round_text))
  (bind _debrief_catalog_count (Utilities|String|ToString(Integer) (Variables|Default|GetDiscoveredCount)))
  (bind _debrief_contamination (Variables|Default|GetContamination))
  (bind _debrief_contamination_text (Utilities|String|ToString(Integer) _debrief_contamination))
  (bind _debrief_route_status (select (>= _debrief_contamination 4) "WEST + EAST CROSSINGS AT RISK" (select (>= _debrief_contamination 2) "WEST CROSSING AT RISK" "ROUTES STABLE")))
  (bind _debrief_line1 (Utilities|String|Append (Utilities|String|Append "SHIFT " _debrief_round_padded) (Variables|Default|GetNL)))
  (bind _debrief_line2 (Utilities|String|Append _debrief_line1 "AUDIT: ALL REQUIRED FIXTURES VERIFIED"))
  (bind _debrief_line3 (Utilities|String|Append _debrief_line2 (Variables|Default|GetNL)))
  (bind _debrief_line4 (Utilities|String|Append _debrief_line3 (Utilities|String|Append (Utilities|String|Append "ANOMALIES CATALOGUED: " _debrief_catalog_count) " / 14")))
  (bind _debrief_line5 (Utilities|String|Append _debrief_line4 (Variables|Default|GetNL)))
  (bind _debrief_lines (Utilities|String|Append _debrief_line5 (Utilities|String|Append "CONTAMINATION CARRIED FORWARD: " _debrief_contamination_text)))
  (bind _debrief_footer (Utilities|String|Append "NEXT SHIFT: " _debrief_route_status))
  (CallFunction|PushTerminal "SHIFT DEBRIEF" _debrief_lines "" _debrief_footer)
  (CallFunction|RaiseTerminal)
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ContinueAfterDebrief" :Time 7.0 :bLooping false))
'''

CONTINUE = '''(fn ContinueAfterDebrief ()
  (bind _debrief_overtime_shift (Variables|Default|GetOvertimeShift))
  (if (Variables|Default|GetIsOvertime)
    (if (> _debrief_overtime_shift (Variables|Default|GetHighestOvertimeShift))
      (Variables|Default|SetHighestOvertimeShift _debrief_overtime_shift))
    (Variables|Default|SetOvertimeShift (+ _debrief_overtime_shift 1))
    (CallFunction|StartShift)
    (elif (>= (Variables|Default|GetCurrentRound) 8)
      (CallFunction|EnterSectorD)
      (else
        (CallFunction|StartShift)))))
'''


def check_response(response, action):
    text = str(response)
    bad = ("assertionerror", "could not be created", "does not exist", "cannot rebind", "expects only", "traceback")
    if any(marker in text.lower() for marker in bad):
        raise RuntimeError(f"{action} failed; stop here and do not save:\n{text[:1500]}")
    try:
        parsed = json.loads(response)
    except (TypeError, json.JSONDecodeError):
        return
    if isinstance(parsed, dict) and (parsed.get("isError") or parsed.get("error")):
        raise RuntimeError(f"{action} failed; stop here and do not save:\n{text[:1500]}")


def read_graph(graph):
    response = M.bp("read_graph_dsl", {"graph": {"refPath": f"{RM}:{graph}"}})
    check_response(response, f"Read {graph}")
    try:
        value = json.loads(response).get("returnValue", "")
    except (TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read {graph}: {response[:500]}") from exc
    if not value:
        raise RuntimeError(f"{graph} read back empty; stopping without saving.")
    return value


def ensure_function(name):
    response = M.bp("list_graphs", {"blueprint": {"refPath": RM}})
    check_response(response, "List Round Manager graphs")
    names = {item["refPath"].split(":")[-1] for item in json.loads(response).get("returnValue", [])}
    if name not in names:
        response = M.bp("add_function_graph", {"blueprint": {"refPath": RM}, "graph_name": name})
        check_response(response, f"Create {name}")


def expression_end(text, start):
    depth = 0
    quoted = escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\" and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return index + 1
    raise RuntimeError("Could not find the end of TryCloseShift's routing expression.")


def build_close_graph(source):
    record_at = source.find(RECORD_MARKER)
    failure_at = source.find(FAILURE_MARKER)
    if record_at < 0 or failure_at <= record_at:
        raise RuntimeError("TryCloseShift does not match the expected audit structure; no changes made.")
    if "ShowShiftDebrief" in source:
        raise RuntimeError("TryCloseShift already calls the debrief; no changes made.")
    advance_at = -1
    for marker in ("(if (|GetbIsOvertime)", "(if (Variables|Default|GetIsOvertime)", "(if (GetIsOvertime)"):
        advance_at = source.find(marker, record_at + len(RECORD_MARKER), failure_at)
        if advance_at >= 0:
            break
    if advance_at < 0:
        raise RuntimeError("Could not locate the clean-audit shift transition; no changes made.")
    end = expression_end(source, advance_at)
    if end > failure_at:
        raise RuntimeError("Shift-transition expression overlaps the audit-failure branch; no changes made.")
    return source[:advance_at] + "(CallFunction|ShowShiftDebrief)" + source[end:]


def main():
    M.init()
    if "true" in M.app("IsPIERunning", {}):
        raise SystemExit("Stop PIE before applying the debrief graphs.")
    manager = M.call("call_tool", {"toolset_name": M.SCN, "tool_name": "find_actors", "arguments": {
        "name": "", "tag": "", "collision_channels": [], "actor_type": {"refPath": RM + "_C"}}})
    check_response(manager, "Find Round Manager actor")
    if not json.loads(manager).get("returnValue"):
        raise SystemExit("Round Manager not found; open L_SectorC in Unreal and retry.")

    updated_close = build_close_graph(read_graph("TryCloseShift"))
    ensure_function("ShowShiftDebrief")
    ensure_function("ContinueAfterDebrief")

    for name, code, expected in (
        ("ShowShiftDebrief", SHOW_DEBRIEF, ("SHIFT DEBRIEF", "ContinueAfterDebrief", "GetContamination")),
        ("ContinueAfterDebrief", CONTINUE, ("GetIsOvertime", "StartShift", "EnterSectorD")),
        ("TryCloseShift", updated_close, ("ShowShiftDebrief", "OnShiftAuditFailed")),
    ):
        response = M.bp("write_graph_dsl", {"graph": {"refPath": f"{RM}:{name}"}, "code": code})
        check_response(response, f"Write {name}")
        actual = read_graph(name)
        missing = [part for part in expected if part not in actual]
        if missing:
            raise RuntimeError(f"{name} readback missing {missing}; stopping without saving.")
        print(f"{name}: write/readback verified")

    compile_response = M.bp("compile_blueprint", {"blueprint": {"refPath": RM}})
    check_response(compile_response, "Compile Round Manager")
    print("Compile response:", compile_response[:1000])
    try:
        compile_json = json.loads(compile_response)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Compiler response was unreadable; not saving.") from exc
    if compile_json.get("isError") or compile_json.get("error") or compile_json.get("returnValue") is None:
        print("Compiler returned no explicit status. Check the editor's Blueprint Compiler Results; the script will not save automatically.")
        return

    save_response = M.call("call_tool", {"toolset_name": M.AT, "tool_name": "save_assets", "arguments": {"asset_paths": [RM]}})
    check_response(save_response, "Save Round Manager")
    print("Graphs saved. Check Unreal's Blueprint Compiler Results for a successful compile, then run the PIE acceptance checklist.")


if __name__ == "__main__":
    main()
