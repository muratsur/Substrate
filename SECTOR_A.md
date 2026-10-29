# Sector A: Habitation / Control

Built 2026-10-27/28 in `L_SectorC` (DESIGN.md section 7: the lived-in room where shifts start and end).

## What it is

The `Scifi_Hideout` kit is a desert outpost, not modular corridors, so Sector A is its stone dome hut (`SM_house`,
11 m across, 6.9 m ceiling) furnished as a crew bunker: console and control desk (cold screen light), table with jug
and tray, stools, shelf, crates, generator, warm lamp over the table. It sits in empty space at (16000, 12000, 1000),
clear of the canal water plane (y < 2910) and above the canal rescue volume (z < -400). Outliner folder:
`Substrate/SectorA`.

## How it joins the loop

| Piece | Where | What it does |
|---|---|---|
| `PlayerStart_0` | in the dome, by the table | shifts start in A |
| `BP_RoundManager_C_1` (`RouteEnd_ShiftTrigger`) | at the tall console | walking into it runs the audit (`TryCloseShift`) |
| `Airlock_AToDock` | dome's +Y doorway | to the sewer, always open |
| `Airlock_DockToA` | sewer, (-300, 1400) | back to A, always open (gate rows 100..100 match no fixture) |
| `A_DoorBack`, `A_DoorOuter` | -Y doorway, behind the airlock | close the dome |

`Airlock_DockToA` is not at the old spawn (0, 1400) because `BP_CanalRescue` drops fallers there.

`BP_Airlock` now has an instance-editable `Partner`; `Transit` goes to it. Before, it went to "every other airlock",
which only worked with exactly two. The original pair (`Airlock_DockToTransit` / `Airlock_TransitToDock`) are each
other's partners.

## Signposting (2026-10-28)

The first playtest found the airlock unreadable: the doorway looked shut and the jump felt like a glitch. Now:
`Transit` plays a hiss and fades in from black; a green lamp hangs over each always-open airlock
(`A_AirlockLampA`, `A_AirlockLampDock`); crates (`A_BackCrates`) block the back door so it reads as storage; and on
shift 1, `ShowRouteTip` (5.5 s, after the key tip clears) says "GREEN DOOR: AIRLOCK   CONSOLE: CLOSE SHIFT".

## Verified in Play-in-Editor (2026-10-28)

The player is dropped into each trigger from above (spawning inside a trigger does not count as entering it):
A airlock lands at (-300, 1400); the sewer airlock lands back in A; the old Dock airlock stays locked with its rows
unlogged; the console trigger fails the audit and keeps the shift open. Not exercised: a full shift closed in A.

## Not done yet

Sector A's own checklist fixtures and anomaly sites, and room tone.

Scripts: `_tools/build_sector_a.py` (room), `_tools/wire_sector_a.py` (spawn, trigger, airlocks, doors).
