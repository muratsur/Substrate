# Anomaly system (T1.1) — what exists, how to author with it

Built 2026-10-12 against `L_SectorC`, verified in Play-in-Editor. This is the
"scare engine" from `TECHNICAL_PLAN.txt` section 5.6, implemented as far as the
editor tooling (MCP) allowed. Deviations are listed at the bottom — read them
before extending it.

## Pieces

| Asset | What it is |
|---|---|
| `Content/Substrate/Anomalies/BP_AnomalySocket` | An **anomaly site**. Placed actor; describes one anomaly and knows how to apply and revert it. Its marker mesh hides itself *and disables its own collision* in `BeginPlay` (a hidden-but-colliding marker is an invisible wall — see TERMINAL_SYSTEM.md). |
| `Content/Substrate/Anomalies/BP_AnomalyDirector` | The director. Rolls the round's anomaly budget, picks sites, applies and reverts. Placed at `(0, 1600, 500)` in `L_SectorC` as `AnomalyDirector`. |
| `BP_GrowthNode.ForceAdvance()` / `RevertGrowth()` | New. Force a growth stage up/down from outside, used by the Growth anomaly. |
| `BP_RoundManager` | New `AnomalyDirector` object variable; `CacheDirector` function; `StartShift` now rolls anomalies; `E`/`Q` logging unchanged. |

No monster, no AI, no animation — every anomaly is a mesh/light/transform state
change, as the design demands (C2).

## Authoring an anomaly in five minutes

1. In `L_SectorC`, place a `BP_AnomalySocket` near where the player should
   notice it (put it in the outliner folder `Substrate/Anomalies`). Its little
   cube is only an editor marker — it hides itself in game.
2. Set its instance properties:

| Property | Meaning |
|---|---|
| `AnomalyType` | `0` Absence, `1` Light, `2` Growth, `3` Displacement |
| `TargetActor` | the actor to act on (leave empty and set `TargetTag` instead if you prefer tag lookup) |
| `MinRound` / `MaxRound` | round window; `MaxRound = 0` means no limit |
| `CooldownRounds` | rounds before this site may fire again (also stops it firing twice in one round) |
| `RevertRule` | `0` EndOfShift, `1` Never (growth: accumulates on purpose) |
| `Offset` | Displacement vector (e.g. `0, 120, 0` = 1.2 m) |
| `LightIntensity` | Light anomaly target intensity; `0` = dead bulb |
| `Note` | free text; the director prints it on screen when the anomaly fires |
| `Severity` | reserved for weighting (not used yet — see deviations) |

3. Play in editor. Nothing is guaranteed on round 1 (budget 0); round 2 always
   fires exactly one Absence (the design's "small and deniable" first scare).

## What each type does

| Code | Type | Apply | Revert |
|---|---|---|---|
| 0 | Absence | `BP_Fixture.ApplyFixtureState(2)` (hidden, no collision, still loggable as FLAG) — or, for a non-fixture target, hide + disable collision. Caches the previous fixture state. | restore the cached state / unhide |
| 1 | Light | `LightComponent.SetIntensity(LightIntensity)` — caches the old intensity first | restore intensity |
| 2 | Growth | `BP_GrowthNode.ForceAdvance()` (mesh + scale ladder, clears the once-per-round latch) | `RevertGrowth()`; normally `RevertRule = 1`, so it stays |
| 3 | Displacement | move the actor by `Offset` (transform cached first) | restore the transform |

## Round bands (what the director rolls)

| Round | Budget | Types (cumulative probability) |
|---|---|---|
| 1 | 0 | — pristine baseline |
| 2 | 1 | Absence 100% |
| 3–7 | 1–2 | Absence .40 / Light .40 / Growth .20 |
| 8–14 | 2–3 | Absence .30 / Light .25 / Growth .20 / Displacement .25 |
| 15+ | 3–5 | same as 8–14 |

If the picked type has no eligible site, the director falls back to one Absence,
so a round still lands an anomaly. Round 2 also has a hard guarantee: exactly
one Absence, even if the roll produced nothing.

Implemented as `GetBudgetMin` / `GetBudgetMax` / `PickType` on the director
(small select-chains). Tune them there.

## Verified in Play-in-Editor

| Check | Result |
|---|---|
| Director finds the sites (`AnomalyDirector: anomaly sockets = 5`) | pass |
| Round 1 rolls nothing — `SHIFT 1 anomalies applied: 0 of budget 0` | pass |
| Round 2 forced Absence — `SHIFT 2 anomalies applied: 1 of budget 1` + fixture hidden via the `BP_Fixture` path (not the generic hide) | pass |
| Round 3 — `SHIFT 3 anomalies applied: 1 of budget 1`, Light anomaly applied and reported by name | pass |
| Revert at the start of the next shift | **not exercised** — needs a real play loop (log every fixture, close the shift twice); code path compiles and is reachable |

## Deviations from `TECHNICAL_PLAN.txt` 5.6 (and why)

1. **No `BPI_Anomalous` interface, no `DA_Anomaly` assets, no `DT_RoundBands`.**
   The editor toolset can create Blueprints, Data Assets, Strings and Materials,
   but not user-defined **structs**, **enums**, or DataTables over them, and it
   cannot run arbitrary Python in the editor. Section 5.6's data model needs all
   three. Anomalies are therefore **placed actors** (`BP_AnomalySocket`) whose
   instance properties are the data, and the band table is three small functions.
   This is arguably closer to 5.6.15's intent ("tag a target, add a definition,
   run R3") and can be migrated to DataTables the day struct creation is possible.
2. **Type is an int code, not a `Name`/enum switch.** This toolset cannot create
   `Switch on Name` nodes (their case pins must be named, and the case-value pins
   are not writable) and `String` equality nodes cannot be created either. Int
   codes dispatch through plain `if` chains.
3. **Dispatch lives in the socket, not in the director.** Each site applies
   itself; the director only budgets, picks and calls `Apply`/`Revert`. Keeps the
   director short and makes a site self-contained.
4. **`SeverityWeight` is not used yet.** The weighting in 5.6.1 multiplies type
   weight by severity; only type weighting exists so far. `Severity` is on the
   socket, ready for it.
5. **Nothing is persisted.** Round state, applied anomalies and growth stages are
   still in-memory (T1.6).

Not implemented yet: Geometry, Shadow, Audio, Addition, Repetition,
ChecklistCorruption anomaly types, the "harder rule", and cooldown-aware
per-target exclusion beyond `CooldownRounds`.

See also `TERMINAL_SYSTEM.md` (T1.4): the checklist the player carries, and the
second user of the same DSL.

## Tooling notes (important for the next agent)

* `write_graph_dsl` re-writing a **function** graph replaces it (re-verified
  2026-10-13 with a two-node scratch function: still two nodes after a second
  write). It **cannot** replace an event, only add to it, and it refuses
  statements after a node that ends the flow ("Unreachable code after
  branch/return" - put your statements before the `IsValid`/cast block). Graphs
  written before that date still carry dead duplicates from the earlier append
  behaviour; they are unreachable, not harmful.
* Do **not** delete "unreachable" nodes to clean up: pin connections are only
  reported on one side, so live data nodes look unreachable. `_tools/prune.py`
  is now a report-only tool — an earlier prune silently deleted the `E`/`Q` key
  handlers. They were rebuilt (`_tools/rm_keys.py`).
* `GetLogEntries` needs `category: ""` explicitly; its default category
  (`LogsToolset`) does not exist, so it fails with an empty-looking error.
* Helper scripts: `mcpx.py` (MCP calls), `findnodes.py` / `pins.py` (node ids and
  pin names), `level.py` (level actor inspection), `place_anomalies.py`
  (the socket authoring table), `pie.py` (start/stop PIE and grep the log),
  `anomaly_build.py` (the graph DSL text + creation steps), `rebuild.py`
  (clear + write every authored graph).
