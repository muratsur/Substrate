# SUBSTRATE

> *"The checklist has no field for what you're seeing."*

**SUBSTRATE** is a single-player first-person atmospheric horror game built in **Unreal Engine 5.8**. You are a maintenance technician on an isolated research facility. Each shift, your handheld terminal gives you a fixed route and a checklist of fixtures to inspect. You look at each fixture, log **PASS (`E`)** or **FLAG (`Q`)**, and close the shift.

Something is growing in the facility. It advances only while you aren't looking, and at most once per round. There is no monster, no AI, and no death screen: **the level geometry is the antagonist**, and failure means the shift refuses to close—forcing you to walk the route again while the facility mutates around you.

---

## Current Project Status (Post-PR #3 — October 2026)

The core playable loop, diegetic terminal, 10-type anomaly engine, persistence, audio feedback, and standalone Windows build (`Packaged\Windows\Substrate.exe`) are complete and verified in `L_SectorC`:

| System | Asset(s) | Status |
|---|---|---|
| **Fixture Inspection & Logging** | `/Game/Substrate/Core/BP_Fixture` | **Done** — `E` (PASS) / `Q` (FLAG) within 4m view cone, nominal/degraded/absent states, on-screen + audio feedback |
| **Round & Shift State Machine** | `/Game/Substrate/Core/BP_RoundManager` | **Done** — Shift progression, checklist evaluation, exposure penalty on failed close, Round 5 phantom row (`C-06`), Round 8 Sector D transition & `EndDemo` |
| **Diegetic Handheld Terminal** | `/Game/Substrate/Core/BP_Terminal`, `WBP_Terminal` | **Done** — Camera-attached world-space checklist (`F` to raise/stow), live status markers, mechanical click SFX |
| **Unobserved Biomass Growth** | `/Game/Substrate/Core/BP_GrowthNode` | **Done** — 0.2s `WasActorRecentlyRendered` check, once-per-round latch, 6-stage mesh + scale ladder (`0.1` to `1.0`) |
| **Anomaly Director & 10 Types** | `BP_AnomalyDirector`, `BP_AnomalySocket` | **Done** — Round-band budgets, Round 2 guaranteed Absence, `EndOfShift` revert, and integer dispatch for all 10 types (`0..9`) |
| **Gated Sector Airlocks** | `/Game/Substrate/Core/BP_Airlock` | **Done** — Checklist-gated transitions between Sewer (`Sector C`) and Transit (`Sector B`), arrival facing fix, Type 9 loopback support |
| **Persistence** | `/Game/Substrate/Core/BP_SubstrateSave` | **Done** — Autosaves/loads `SavedRound` and growth stages across sessions (`SaveShiftState` / `LoadShiftState`) |
| **Audio & Footsteps** | `/Game/Substrate/Audio/*` | **Done** — Velocity-driven footstep timer with pitch variation (`0.92..1.08`), terminal raise/stow click, PASS chime, and FLAG error buzz |
| **Lighting & Post-Process** | `L_SectorC` (`PostProcessVolume_1`) | **Done** — Locked exposure (`Min=Max=0.55`, bias `-1.5`), Lumen GI, Volumetric Fog, tuned Transit corridor practicals (`120 cd` / `90 cd`) |

---

## Controls

| Key | Action |
|---|---|
| `W` `A` `S` `D` | Move |
| `Mouse` | Look |
| `F` | Raise / Stow Handheld Terminal |
| `E` | Log looked-at fixture as **PASS** (within 4m) |
| `Q` | Log looked-at fixture as **FLAG** (within 4m) |

---

## Quick Start

### 1. Play the Standalone Build (No Editor Needed)
Run the packaged executable directly:
```powershell
.\Packaged\Windows\Substrate.exe
```

### 2. Open in Unreal Engine 5.8
1. Install **Unreal Engine 5.8** via the Epic Games Launcher (Blueprint-only project; Visual Studio is not required).
2. Ensure the required Fab art packs (Laya Design bundle) are installed under `Content/`:
   * `Modular_Sewer_Kit` (Sector C — Filtration)
   * `Ice_Station` (Sector B — Transit)
   * `Alien_Biomass` (Growth stages & Sector D)
   * `Scifi_Hideout` (Sector A — Habitation, planned)
   * `Asteroid_base` (Sector E — Structure, planned)
3. Open `Substrate.uproject`. The startup map `/Game/Substrate/Maps/L_SectorC` loads automatically.
4. Press **`Alt + P`** to Play-in-Editor.

---

## Automation & MCP Tooling (`_tools/`)

This repository includes a Python automation suite in `_tools/` that communicates with the Unreal Editor **ModelContextProtocol (MCP)** server (`http://127.0.0.1:8000/mcp`) for Blueprint graph authoring (`write_graph_dsl`), level inspection, automated PIE regression testing, and asset serialization:

* `_tools/mcpx.py` / `_tools/ue_mcp.py` — HTTP MCP client helpers
* `_tools/test_airlock_gate.py` — Automated A/B airlock gate and checklist verification
* `_tools/test_anomaly_loop.py` — Multi-round anomaly application and `EndOfShift` revert verification
* `_tools/place_anomalies.py` — Declarative `BP_AnomalySocket` placement table
* `_tools/rebuild.py` — Full Blueprint graph reconstruction script

---

## Repository Documentation Index

* **[`DESIGN.md`](DESIGN.md)** — Core design pillars, failure model, growth mechanics, escalation bands, and lighting/legibility rules.
* **[`TECHNICAL_PLAN.txt`](TECHNICAL_PLAN.txt)** — Full system architecture, data models, round state machine, performance budgets, and milestone roadmap.
* **[`IMPLEMENTATION_GUIDE.txt`](IMPLEMENTATION_GUIDE.txt)** — Exact node-by-node Blueprint specifications, level coordinates, lighting values, and Git workflow rules.
* **[`ANOMALY_SYSTEM.md`](ANOMALY_SYSTEM.md)** — How `BP_AnomalyDirector` and `BP_AnomalySocket` roll, apply, and revert anomalies.
* **[`TERMINAL_SYSTEM.md`](TERMINAL_SYSTEM.md)** — Architecture and tuning guide for the diegetic `BP_Terminal` and `WBP_Terminal` UI.
* **[`BLUEPRINT_RECOVERY.md`](BLUEPRINT_RECOVERY.md)** — Recovery inventory extracted from `L_SectorC.umap`.
* **[`FREE_ROAM_SESSION_LOG.md`](FREE_ROAM_SESSION_LOG.md)** — Session log covering geometry cleanup and `BP_Airlock` tick/transit verification.
* **[`TEST_ME.md`](TEST_ME.md)** — Playtest brief for evaluating the Round 8 Sector D corridor and `C-06 RELIEF VALVE` ending.
* **[`STEAM_PAGE.md`](STEAM_PAGE.md)** — Store page copy, tag hierarchy, capsule concept, and 6-screenshot capture plan.