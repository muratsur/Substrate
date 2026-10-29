# Sector D: Research (the ending)

Built 2026-10-29 in `L_SectorC` by `_tools/build_sector_d.py` (DESIGN.md section 7: "the source").

Closing shift 8 (`EnterSectorD`) teleports you to the arrival tube at (-660, -8500). From there:

| Beat | Where | What |
|---|---|---|
| Tube | y -10701..-5671 | the original `SectorD_Tube_*` corridor, unchanged |
| Lab | x -1078..202, y -5671..-4031 | Alien_Biomass kit room: benches with monitors, a clean table with beakers, a chair pushed back, filing shelves, cold ceiling lights that flicker, growth leaking in beside the back door, and a wall screen: "ROUTE COMPLETE. / THANK YOU, TECHNICIAN. / PROCEED TO RELIEF VALVE." |
| Chamber | y -4031..-2391 | red-lit, organism clusters on every wall, tendrils hanging along the walls, and `C-06 RELIEF VALVE` (`Fix_D06`, its pipe and light) in the middle at (-440, -3150) |

Logging C-06 (row 20) still calls `EndDemo`: terminal "SUBSTRATE DEMO COMPLETE", 3 s fade, quit at 5 s.

Details:
* Rooms are kit wall modules (320 x 120 x 380), 640 x 820 floor tiles and 320 x 820 ceiling panels; every piece is
  placed by label (`D_*`), outliner folder `Substrate/SectorD`, so re-running the script moves rather than duplicates.
* Tendrils run ~8 m along their local +Y, so they hang along the walls; the first layout put two across the walk to the
  valve and their collision could not be switched off through the toolset.
* `SectorD_PostProcess` was stretched to y -2200 to cover the chamber.
* Flicker: `BP_RoundManager.FlickerDLab`, a 0.15 s looping timer from `StartShift`; lights tagged `DLabLight` drop to
  2 cd 12% of ticks.

Verified 2026-10-29: traces clear on every leg (arrival, tube mouth, lab, door, valve); a playtest in the editor logged
C-06 in the chamber and the demo ended; the lab lights' intensity alternates 30 / 2 in PIE.
