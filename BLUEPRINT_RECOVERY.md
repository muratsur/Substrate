# Blueprint recovery notes (extracted from L_SectorC.umap)

The four Blueprint classes below were lost; the map still stores the data of
every placed instance. Everything here was read from the recovered
`Content/Substrate/Maps/L_SectorC.umap` (see `_tools/umap_inventory.py`).
Behaviour comes from `DESIGN.md`; **variables, tags and placement are as found
in the map**. Inferred items are marked (inferred).

Class paths the map expects (must match exactly or references stay broken):

    /Game/Substrate/Core/BP_Fixture       (-> BP_Fixture_C)
    /Game/Substrate/Core/BP_GrowthNode    (-> BP_GrowthNode_C)
    /Game/Substrate/Core/BP_RoundManager  (-> BP_RoundManager_C)
    /Game/Substrate/Core/BP_Airlock       (-> BP_Airlock_C)

## BP_Fixture   (9 placed)
Root: `StaticMeshComponent`. Parent class: Actor.

| Variable | Type | Notes |
|---|---|---|
| `FixtureID` | Name | The checklist label, e.g. `C-01 INLET VALVE` |
| `RowOrder` | Integer | Checklist row, 0-based. Default 0 is not serialised |

Tags on instances: `FixtureB`, `FixtureD` (Sector C fixtures carry none).
States per DESIGN.md section 10: nominal / degraded / absent, plus interaction prompt.

| Instance label | FixtureID | RowOrder | Tag | Location (X,Y,Z) |
|---|---|---|---|---|
| Fixture_C1 | C-01 INLET VALVE | 0 | - | 1469, 4342, 430 |
| Fixture_C2 | C-02 FILTRATION SEAL | 1 | - | 3060, 6170, 430 |
| Fixture_C3 | C-03 PRESSURE GAUGE | 2 | - | -2480, 7212, 420 |
| Fixture_C4 | C-04 OVERFLOW LAMP | 3 | - | -1516, 8349, 420 |
| Fixture_C5 | C-05 OUTFALL GRATE | 4 | - | -2543, 10200, 430 |
| Fix_B01 | B-01 COOLANT PUMP | 5 | FixtureB | 8560, 2500, 460 |
| Fix_B02 | B-02 HEAT EXCHANGER | 6 | FixtureB | 8560, 3250, 460 |
| Fix_B03 | B-03 CONDENSER COIL | 7 | FixtureB | 8560, 4100, 460 |
| Fix_D06 | C-06 RELIEF VALVE | 8 | FixtureD | -660, -6230, 455 |

C-06 is the phantom row: Sector D, the demo ending (press E or Q).

## BP_GrowthNode   (3 placed)
Root: `StaticMeshComponent`. Tag on every instance: `Growth`.
Variables (names from DESIGN.md section 4; none were overridden per-instance in
the map, so defaults lived in the Blueprint and are not recoverable):
`GrowthStages` (StaticMesh[]), `GrowthScales` (float[], about 0.1 to 1.0),
`SecondsToAdvance` (float), `EligibleThisRound` (bool latch), stage index.
Logic: 0.2 s timer on `WasActorRecentlyRendered`; advance one stage when
unobserved for `SecondsToAdvance` and latch set; swap mesh + scale; clear latch;
`IsValidIndex` guard on `GrowthScales`.
Meshes: `SM_alien_organism` .. `_09` from Alien_Biomass are referenced by the map.

| Instance label | Location |
|---|---|
| Growth_Early | 2200, 5200, 290 |
| Growth_Late | -2100, 7800, 283 |
| GrowthNode_Transit | 8560, 3600, 315 |

## BP_RoundManager   (1 placed)
Label `RouteEnd_ShiftTrigger`, tag `RoundManager`, at 0, 1260, 420.
Variable found: **`RouteStart` (Vector) = (0, 1400, 360)**.
Components: `CollisionComponent` (box trigger), `SpriteComponent`, root.
Logic (DESIGN.md sections 3, 6, 10, TEST_ME.md): round counter (persisted),
`StartShift` re-arms every actor tagged `Growth`, checklist generated from the
`BP_Fixture` rows ordered by `RowOrder`, shift closes only when all rows are
signed off, round 8 close opens Sector D, 15 min fallback timer ends the demo.
The overlap/trigger at the route end starts the shift-close check (inferred).

## BP_Airlock   (2 placed)
Root component plus an audio component icon; no variables serialised.
A matched pair, which suggests a teleport/transition between sectors (inferred):

| Instance label | Location |
|---|---|
| Airlock_DockToTransit | 300, 1400, 400 (next to RouteStart) |
| Airlock_TransitToDock | 8560, 4520, 420 (end of the B-fixture corridor) |

Related lights in the level: `AirlockLight_Dock`, `AirlockLight_Transit`.
Because no variables survived, the destination is probably found by label or
a tag/soft reference set in the Blueprint (inferred). Wire it as: overlap at
one airlock moves the player to the other.

## Still unrecoverable
Graph logic, default values (Growth arrays/timings, the checklist UI), and the
8 `MI_*` material instances plus 2 ambience assets listed in MISSING_ASSETS.txt.

## Status: rebuilt (2026-10-11)
All four classes were recreated at the paths above via the editor MCP server
(see `_tools/ue_mcp.py`) and verified in Play-in-Editor on L_SectorC:
instance counts and FixtureID/RowOrder values match the map; growth timer,
once-per-round advance, RoundManager.StartShift and the airlock pair work.
Since added and verified in PIE:
- BP_Fixture: `FixtureState` (0 nominal, 1 degraded, 2 absent -> hidden, no
  collision), `LogResult` (0 unlogged, 1 PASS, 2 FLAG), `LogFixture`,
  `ResetLog`, `IsLoggedCorrectly` (nominal expects PASS, degraded/absent FLAG).
- BP_RoundManager: touching the route-end trigger runs `TryCloseShift`; if every
  fixture is logged correctly the next round starts (`StartShift`: round + 1,
  logs reset, `Growth`-tagged nodes re-armed), otherwise the shift stays open
  and growth is re-armed (the exposure penalty from DESIGN.md section 3).

Still to do: growth defaults (arrays/timings), a terminal UI / interaction that
calls `LogFixture`, degraded-state visuals, Sector D ending, persistence.
Note: `GrowthNode_Transit` has no `Growth` tag in the map, so it is not re-armed.
