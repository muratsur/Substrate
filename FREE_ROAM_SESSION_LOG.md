# Session log — invisible wall fix & saves (2026-10-14)

## Diary of incidents

1. **West seam wall (y≈8409)** — caused by `StaticMeshActor_3643` (`SM_double_bridge`,
   x[-2443..-1685], chest height z 288–464). Parked under the floor at z=-3000
   in edit mode, map saved (`L_SectorC.umap`). Verified clear by walk-probe to x=-1975.
   `StaticMeshActor_2678` (`SM_entrance`) was parked the same way earlier.
2. **"Wall" north of spawn = the canal gap + rescue.** Floor-trace grid proved no
   ground between y=1750 and y≈5000 on lanes x=-1500..700 — that is the canal.
   `BP_CanalRescue` teleports the pawn to (0, 1400, 400) on canal overlap — by design.
   The real route north is the airlock at (300, 1400).
3. **The actual bug today: the airlock never transited.** `BP_Airlock.EventGraph`
   had an empty `EventTick`, and nothing else called `TryTransit` — so `GateOK`
   stayed false forever and the gate silently refused. Both gate instances, both
   directions. Fix: wired `EventTick → TryTransit` in the EventGraph
   (the Disarm/InsideOK flag logic already prevents ping-ponging), compiled,
   saved, restarted PIE.

## Verified this session

- `test_airlock_gate.py log 0` → **PASS**: pawn entered gate 0 (300, 1400),
  transited to gate 1 (8560, 4520).
- `test_airlock_gate.py log 1` → **PASS**: reverse direction transit works.
- West seam walk-probe → clear all the way to x=-1975.
- Read-back of `BP_Airlock.EventGraph` DSL shows `EventTick → TryTransit` persisted.
- Asset saves all returned `true`; no open/dirty assets left in the editor.
- Disk-write proof: a controlled write+save moved `BP_Airlock.uasset` from
  343864→352312 bytes (mtime 10:36→10:57 local); a graph write alone never touches
  disk, so the earlier serializations had been flushed by `save_assets` correctly.

## Saved to disk today

| File | Note |
|---|---|
| `Content/Substrate/Core/BP_Airlock.uasset` | Tick→TryTransit wiring (the fix) |
| `Content/Substrate/Core/BP_CanalRescue.uasset` | re-saved unchanged |
| `Content/Substrate/Maps/L_SectorC.umap` | unchanged since 2026-10-13 23:00 save (parked meshes live here) |
| `_tools/*.py` | all diagnostic/fix scripts (see below) |

## Current state (not bugs)

- **Free-roam patch active**: `GateOpen` always sets `GateOK=true`, so E/Q fixture
  logging is not required to open the gates right now.
- **Parked off-stage meshes** (restorable from the outliner):
  `StaticMeshActor_2678` (SM_entrance), `3643` (SM_double_bridge), `BlockingVolume_2` at y=30000.
- Fixture `LogResult` values written by the livetests exist only in the PIE session
  that ran them; they reset on the next PIE start.
- PIE was stopped at the end of the session, then the editor stayed open with all
  changes saved; the packaged build (`Packaged/Windows/Substrate.exe`) is **not**
  rebuilt — it still predates the airlock fix.

## Key scripts in `_tools/` (scratch, safe to delete)

- `test_airlock_gate.py` — A/B gate transit test (`python _tools/test_airlock_gate.py log|control 0|1`)
- `fix_airlock_tick2.py` — applied the EventTick→TryTransit graph patch
- `floormap.py` / `floorprobe.py` — floor-trace grid used to map the canal gap
- `west_seam_check.py` — walk-probe of the west corridor
- `mcpx.py` / `ue_mcp.py` — MCP over HTTP helpers for the editor toolsets
