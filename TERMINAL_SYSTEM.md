# Terminal (T1.4) — the checklist you carry

Built 2026-10-13 against `L_SectorC`, verified in Play-in-Editor. This is
`TECHNICAL_PLAN.txt` section 5.9. It is the only place the player can read what
the shift expects, which makes it the hinge of the whole loop: without it the
player is guessing, with it the game is "read the list, walk the route, notice
what changed".

## Pieces

| Asset | What it is |
|---|---|
| `Content/Substrate/UI/WBP_Terminal` | The screen. `Bg` (near-black panel) > `Layout` (VerticalBox) > `TxtHeader`, `RowBox` (`TxtNames` + `TxtStates`), `TxtFooter`. Display only. |
| `Content/Substrate/Core/BP_Terminal` | The device actor. Placeholder slab mesh + a `WidgetComponent` (`Screen`, world space, 900x660 draw size). Attaches itself to the player camera, stows, and toggles on `F`. |
| `BP_RoundManager.RefreshTerminal` | Builds the two columns from the placed fixtures and pushes them. Called from `StartShift` and from `LogLookedAtFixture`. |
| `BP_RoundManager.FindTerminal` | Finds the placed terminal and calls `AttachToPlayer` on it (so ordering problems in `BeginPlay` cannot leave the terminal unattached). |
| `BP_RoundManager.AddRowIfMatch` | For one fixture row: appends its name, its state marker, and counts it if it is still wrong. |
| `BP_RoundManager.PushTerminal` | `IsValid` guard, then `BP_Terminal.ShowChecklist(Header, Names, States, Footer)`. |

New instance-editable variables on `BP_RoundManager`: `DebugTerminal` (prints the
built checklist to the log) and `NL` (the newline used to join rows — see tooling
notes for why it is a variable).

## Data flow

```
StartShift / LogFixture
      -> RefreshTerminal
           for row in 0 .. RequiredRowMax:        (0..7 today)
             for each BP_Fixture in the level:
               if fixture.RowOrder == row:
                 names  += FixtureID + NL
                 states += "[ ]" / "[PASS]" / "[FLAG]" + NL
                 if not IsLoggedCorrectly: remaining += 1
           header = "SHIFT 0<round>"    footer = "CLOSE SHIFT: READY"
                                                or "BLOCKED (<n> left)"
      -> PushTerminal -> BP_Terminal.ShowChecklist -> WBP_Terminal.SetChecklist
```

The terminal never reads the world itself and never logs anything; logging stays
in `BP_RoundManager.LogLookedAtFixture` (plan 5.3). Two columns instead of one
multi-line string is deliberate: names and states are separate `TextBlock`s in a
`HorizontalBox`, both monospaced, so the columns line up without sorting code and
without one widget per row.

`C-06 RELIEF VALVE` has `RowOrder 20` (was 8 until Sector A's rows 9-11 arrived and
`RequiredRowMax` went to 11), above `RequiredRowMax`, so it is not on the
terminal and logging it does not move the count — that is the phantom row from
`TEST_ME.md`, and it is what I used to prove the required-rows rule.

## Hints (2026-10-26)

Shipping builds strip `PrintString`, so player hints go through `BP_RoundManager.ShowHint(Text)` instead. It puts
the text in the footer's last-action slot, raises the terminal, and clears the hint after 4 s (`ClearHint`). It is used
for: airlock locked, nothing in range, west gate open, and the F tip on shift 1. Sector D and the demo end raise the
terminal with their own text. Debug prints are unchanged. Built by `_tools/hints_on_terminal.py`.

## Dispatcher (2026-10-28)

`BP_RoundManager.ShowDispatch` pushes an `INCOMING DISPATCH` message over the checklist at shift start (1.5 s; 10 s on
shift 1, after the key and route tips), raises the terminal, plays a radio blip, and restores the checklist after 9 s
(any log restores it sooner). One message per shift for rounds 1-8; Overtime (9+) gets "THIS CHANNEL IS NOT IN USE."
The lines live in `_tools/dispatcher.py` (`LINES`, max 28 characters per line, joined with `NL`). Checked in a
Development build: shift 1 shows the message, then the checklist returns.

## Wayfinding (2026-10-28)

`BP_RoundManager.UpdateWayfinding` runs after every log and photo, and 0.5 s after `StartShift`. It counts the rows
still open in the sewer gate (0-4) and the transit gate (5-7) with the gate's own test (logged correctly or
photographed), turns the lamps over those airlocks (`WayLampC` at the Dock, `WayLampB` at the Transit end) red or
green, and shows "SEWER LOGGED - TRANSIT AIRLOCK OPEN" / "TRANSIT LOGGED - AIRLOCK BACK TO DOCK" once per shift.
`OpenWestGate`'s all-logged hint now reads "ALL LOGGED - CLOSE SHIFT AT DOME CONSOLE". `BP_Airlock.GateOpen` counts a
photographed fixture as done, as the audit does. Built by `_tools/wayfinding.py`.

## Inspection camera (2026-10-27)

`C` calls `BP_RoundManager.TakePhoto`: the same 4 m view test as E/Q picks a fixture, and one of 3 film shots per shift
(`FilmLeft`, reset in `StartShift`) files it. A photographed fixture shows `[PHOTO]` and counts as reported in both
`AddRowIfMatch` (remaining count) and `TryCloseShift` (audit), whatever its state, so a photo is a safe hedge that
reveals nothing. Photographing the same fixture again costs no film. IDs are kept as `|ID|` in the `PhotoIDs` string.
Built by `_tools/add_inspection_camera.py`.

## Tuning

| Property | On | Meaning |
|---|---|---|
| `UpOffset` | placed `BP_Terminal` | camera-relative offset when raised (default `48, 10, -12`) |
| `StowOffset` | placed `BP_Terminal` | camera-relative offset when stowed (default `30, 4, -34`) |
| `ScreenYaw` | placed `BP_Terminal` | yaw of the screen relative to the camera — `180` today (see below) |
| `Screen` / draw size | `BP_Terminal` | 900x660 slate units on a 30x22 cm panel |
| `RequiredRowMax` | placed `BP_RoundManager` | highest `RowOrder` the shift needs (7) |
| `DebugTerminal` | placed `BP_RoundManager` | prints the built checklist to the log |

To add a checklist row: place another `BP_Fixture`, give it a `FixtureID` and the
next `RowOrder`, and raise `RequiredRowMax` if the row should be required. Nothing
else needs editing.

To debug the terminal without eyes: set `DebugTerminal` on the placed manager and
read `Saved/Logs/Substrate.log`; the names column, the states column and the
footer are printed on every refresh.

## Verified in Play-in-Editor

| Check | Result |
|---|---|
| Rows match the level's fixtures, in `RowOrder`, `SHIFT 001` at the top | **pass** — log shows `C-01 INLET VALVE` … `B-03 CONDENSER COIL`, 8 rows |
| One state marker per row | **pass** — 8 x `[ ]` |
| Footer before any logging | **pass** — `CLOSE SHIFT: BLOCKED (8 left)` |
| Logging a fixture updates the terminal live | **pass** — logging every fixture flips the column to `[PASS]` and the footer to `CLOSE SHIFT: READY` (driven by a temporary timer hook calling `LogLookedAtFixture`/`LogFixture`, since automation cannot send key presses) |
| Phantom row `C-06` is excluded and does not move the count | **pass** — `C-06 RELIEF VALVE: PASS` leaves `(8 left)` |
| Both blueprint chains compile with no errors | **pass** — `compile_blueprint` / `CompileWidgetBlueprint` clean |
| The panel renders correctly on screen, right way round | **not verified — needs your eyes.** See below. |
| Raising/lowering with a real `F` key press | **not verified** — this is the same limitation as plan defect D7 (no synthetic keyboard input) |
| Greyed rows for locked sectors, per-row colours, key/confirm sounds | not implemented (see deviations) |

### The one thing you should look at

Automation in this project cannot screenshot the game (the editor window is hidden,
and world-space widgets do not render in the editor viewport) so I could not see
the panel. It is built and it receives data, but two things are down to taste:

1. **Is the text readable and the right way round?** The screen faces the camera
   along the camera's forward axis; `ScreenYaw = 180` is the conventional value.
   If the text reads mirrored in game, set `ScreenYaw` to `0` on `Terminal_01`
   and re-run — one number, no graph editing (a two-sided widget shows its back
   face mirrored rather than disappearing, so mirrored text is the failure mode).
2. **Size and position.** With the terminal raised, `UpOffset` `48, 10, -12` puts
   the panel ~0.5 m in front, slightly right and below the reticle. `X` is
   distance, `Y` is right, `Z` is up.

## The device must never collide (2026-10-13)

The first play test failed with "cannot move forward". Cause: the placeholder
slab is attached to the camera, so its collision box sits inside the player
capsule and travels with it — an invisible wall glued to your face, and the
player is blocked in the look direction. Fixed twice over, on purpose:

* the `Body` component's collision profile is now `NoCollision`
  (`bodyInstance.collisionEnabled` = `NoCollision`), and
* `ApplyRaised` starts with `SetActorEnableCollision(self, false)`, so the device
  is collision-free even if the component profile is ever reset.

The five `BP_AnomalySocket` markers had the same defect (`BeginPlay` hid them but
left collision on, so they were invisible obstacles in the corridors). Their
`BeginPlay` now also calls `SetActorEnableCollision(self, false)`.

Rule for anything cosmetic you attach to the camera, or hide in game: turn its
collision off in the same breath. `SetActorHiddenInGame` does **not** do that.

## Deviations from `TECHNICAL_PLAN.txt` 5.9

1. **No handheld mesh.** There is no `SM_Terminal` in the project (see
   `MISSING_ASSETS.txt`), so the "device" is a placeholder slab
   (`/Engine/BasicShapes/Cube`, dark, 2x30x22 cm) with the screen on it. Swapping
   the mesh later is a one-property change on the `Body` component.
2. **Raise is a toggle on `F`, not a hold.** Hold-to-raise needs an `InputAction`
   with a triggered/completed pair (Enhanced Input), which this toolset cannot
   author together with the existing raw `E`/`Q` key nodes. `F` toggles; the
   design's "hold to raise" is a small follow-up (plan D-INPUT).
3. **No scroll.** Eight rows fit; the plan's wheel-scroll is only needed when
   sectors A/D/E/F raise the row count.
4. **No greyed locked-sector rows, no per-row colour, no terminal sounds.** Rows
   carry no state other than their marker; the plan's font/colour pass and
   `WBP_Terminal`'s key/chime/error sounds are still open.
5. **The checklist is still "every fixture with `RowOrder <= RequiredRowMax`"**,
   not `DT_Checklist`. That is plan 5.2 (checklist generation) and T1.3; this
   terminal binds to whatever the manager says, so it does not have to change when
   5.2 lands.

## Tooling notes (important for the next agent)

* `set_properties` takes `values` as a **JSON string**, not an object, and object
  arguments are `{"refPath": "..."}`. `list_properties` / `get_properties` want an
  `instance` key, not `object`.
* Pin names differ from the editor's labels: `SetActorHiddenInGame` uses
  `bNewHidden`, `SetActorRelativeLocation` uses `NewRelativeLocation`.
* **Do not name a function `Set<Something>` when `<Something>` is a variable.**
  `CallFunction|SetRaised` silently resolved to the *variable setter* for `Raised`
  and produced a wrong graph with no error. The terminal's function is called
  `ApplyRaised` for exactly this reason.
* A local call node only knows its parameter pins after the blueprint has been
  compiled once, so add parameters, compile, then write the calling graph.
* `write_graph_dsl` refuses statements after a node that terminates the flow
  (`Utilities|IsValid`, a cast with `:CastThen`, …): "Unreachable code after
  branch/return". Put your statements before those blocks.
* Re-writing a **function** graph replaces it (verified with a scratch function);
  the older graphs still carry dead copies from the earlier append behaviour, and
  `write_graph_dsl` also cannot express a literal newline. Rows are joined with a
  `String` member variable (`NL`) whose value was set through JSON, which is the
  one place escapes are reliable.
* `AssetTools.save_assets` saves the level too: pass
  `"/Game/Substrate/Maps/L_SectorC"`. `SceneTools.save_actor` only works for
  external actor assets.
* Scripts: `_tools/terminal_build.py` (widget tree + styling),
  `terminal_widget.py` / `terminal_widget2.py` / `terminal_widget3.py`
  (`SetChecklist`), `terminal_actor.py` / `terminal_actor2.py` / `terminal_fix*.py`
  (`BP_Terminal`), `terminal_manager.py` (the manager side), `terminal_place.py`
  (placement), `terminal_pie.py` (PIE harness), `terminal_livetest.py` (the
  temporary timer hook, removed), `terminal_capture.py` / `terminal_shot.py`
  (viewport/app captures, useful for the level viewport only).
