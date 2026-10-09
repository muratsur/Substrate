# SUBSTRATE — Design Document

**Working title.** *Substrate* = the material something grows on. Sounds like a facility designation, ominous without being cheesy. Search Steam and the USPTO before committing — a name collision is cheap to fix now and expensive after the store page is live.

**Genre:** Single-player atmospheric horror
**Engine:** Unreal Engine 5.8
**Platform:** Steam (PC)
**Art:** Laya Design kits (Humble Massive Unreal Engine Bundle, Fab Professional licenses)
**Target:** 2–3 hours, $9.99

---

## 1. Premise

You are a maintenance technician on an isolated research facility. Your job is the **round**: walk a fixed route, check a fixed list of fixtures, log their status, close the shift. Then do it again.

Something is growing in the facility. It grows when you aren't looking.

**The antagonist is the level geometry.** There is no monster to model, no AI to write, no animation to author. Every scare in this game is a mesh state change, a light change, a door state, or a sound.

---

## 2. The core loop — and the one idea the game is built on

Each shift, a handheld terminal gives you a checklist: *Sector B, junction 4 — verify seal integrity. Sector C, filtration — verify pressure.* You walk the route, look at each fixture, log PASS or FLAG, and close the shift.

**The checklist is the horror delivery mechanism.**

The game explicitly tells you what to look at. So when something is wrong that *isn't on the list*, you notice immediately — and there is no field to report it in. The terminal has no category for "the corridor is longer than yesterday." You can see it, you cannot log it, and the shift will not close until every listed item is signed off.

That tension — a bureaucratic form that refuses to acknowledge what you're seeing — is the game. Everything else serves it.

---

## 3. Failure model

**There is no death screen.** Failure is *the round not closing.*

Log something incorrectly, or miss a required check, and the shift stays open. You walk the route again — and the growth has advanced in the meantime. The punishment for failure is more exposure, not less. Tension escalates on failure instead of resetting, which is the opposite of how most horror games handle it and the reason this one can work without a threat that can kill you.

**Optional harder rule for later rounds:** unreported anomalies accumulate. Past a threshold, route segments start closing behind you.

---

## 4. The growth system

Biomass advances **only while unobserved, and at most once per round.** Both halves matter — see the pacing note below. Implementation is a visibility check, not AI:

- `BP_GrowthNode` polls `WasActorRecentlyRendered` on a 0.2s timer. That built-in is false when the actor is off-screen *or* occluded, which is exactly the test we want and is far cheaper than a manual frustum + line trace.
- If unobserved continuously for `SecondsToAdvance`, advance one stage: swap the mesh from `GrowthStages` and the scale from `GrowthScales`.
- On advance, the node clears its own `EligibleThisRound` latch. `BP_RoundManager.StartShift` re-arms every tagged growth node at the top of each round.

Cost: one timer, one mesh swap, one scale set. No components, no skeletal meshes, no animation blueprints, no navmesh, no behavior trees.

**Why the once-per-round latch — learned by building it without one.** Unlatched, a growth node runs its whole ladder in about fifteen real seconds of not being looked at. That makes growth a *wall-clock* effect: it happens because time passed, not because a round passed. Two things break. Progression stops being authorable — you can't say "by round 8 Sector C should look like this" when the outcome depends on how long the player idled. And the player learns the wrong lesson: that growth is a timer to be waited out rather than a consequence of completing shifts.

Latched, it reads correctly: **each shift permits exactly one advance, and the advance still happens only when you look away.** The player keeps the paranoia — stare at it and it will not move, turn around and it has — while the game keeps control of the curve.

The player will *test* this. That's intended, and the latch makes the test more interesting: after a node has advanced this round, staring or not staring changes nothing, so the tell is inconsistent between rounds in a way that resists being reduced to a rule.

**Growth is scaled, not just swapped.** `GrowthScales` runs the ladder from ~0.1 to 1.0 alongside the mesh. The Laya `Alien_organism` meshes are hero pieces — at full size, stage 1 is a two-metre tentacle, which is a jump scare rather than a deniable anomaly. Scaled down, early stages read as a stain on the floor. The step is guarded by `IsValidIndex`, because Unreal's `Array Get` returns 0 for a float out of range and a short `GrowthScales` array would otherwise scale growth silently to nothing.

---

## 5. Anomaly taxonomy

Data-driven via `DA_Anomaly` assets. Each defines a target actor, a type, the earliest round it can fire, and a severity weight.

| # | Type | Example | Cost |
|---|---|---|---|
| 1 | **Growth** | Biomass advances a stage in a location | Low |
| 2 | **Absence** | A fixture, crate, or sign is simply gone | Low |
| 3 | **Addition** | Something present that has never been there | Low |
| 4 | **Displacement** | An object has moved a few meters | Low |
| 5 | **Geometry** | Corridor longer, doorway shifted, room proportions off | Medium |
| 6 | **Light** | Bulb dead, color temperature wrong, flicker pattern changed | Low |
| 7 | **Shadow** | A shadow that doesn't match its caster | Low — very effective |
| 8 | **Audio** | A sound with no source; or an expected sound absent | Low |
| 9 | **Checklist corruption** | Terminal lists a fixture that doesn't exist, or renames one you know | Medium |
| 10 | **Repetition** | You walk into a room you just left | Medium |

Types 7, 9, and 10 are the ones players will talk about. Prioritize them over volume of type 1.

---

## 6. Escalation structure

| Rounds | What happens | Purpose |
|---|---|---|
| **1–2** | Everything normal. Route taught, checklist taught. | Establish the baseline. **The horror is entirely dependent on the player knowing the geometry cold.** |
| **3–7** | First anomalies. Type 1, 2, 6. Small, deniable. | Player starts doubting their memory rather than the facility. |
| **8–14** | Route mutates. New rooms. Types 5, 9, 10 enter. | The facility stops pretending. |
| **15+** | The route no longer resolves. Checklist items reference sectors that don't exist. | The facility *is* the growth. |

**Critical tuning note:** instinct says keep rounds 1–3 pristine. Don't. If nothing happens for three full circuits, players quit before the game starts. **Land the first anomaly in round 2**, small and deniable — a single dead bulb.

---

## 7. Level structure — kits mapped to sectors

| Sector | Kit | Role |
|---|---|---|
| **A — Habitation / Control** | Science Fiction Hideout | Round start and end. The "safe" room. Must feel lived-in. |
| **B — Transit** | Sci-Fi Snow Station | Corridors with exterior windows. Establishes isolation and cold. |
| **C — Filtration** | Sewers Modular Kit | The underbelly. **First growth appears here.** |
| **D — Research** | ALIEN BIOMASS Research Facility | The source. Locked until mid-game. |
| **E — Structure** | Asteroid Base / MEGASTRUCTURE | Scale shift. The facility is bigger than you were told. |
| **F — Beneath** | Crystal Cave | Endgame. The facility was built on top of something. |

**The route itself is the progression.** Early rounds: A → B → C → B → A. Later rounds append D, then E, then F. The player doesn't unlock areas by finding keys — the checklist simply starts listing them, with no explanation.

All six kits are Laya Design, so they share a material system and texel density. Sectors will read as one facility rather than a stitched-together asset dump. That coherence is what the $30 actually bought.

---

## 8. Art & lighting direction

**Mandatory, not optional:** these kits ship bright, clean, and cinematic. Horror needs dark, grimy, and specific. Budget real time for:

- A global post-process pass: crushed blacks, desaturation, heavy vignette, film grain
- Killing most of the kits' default lighting and replacing it with sparse, motivated practical lights
- Wet/grime decal layer over floors and lower walls
- Volumetric fog per sector, tuned individually

Rule: **the player should never see more than ~15m of corridor at once.** Kits designed for wide cinematic vistas have to be broken up with fog, darkness, and geometry blocking.

### The legibility constraint — discovered during the Sector C lighting pass

**This game cannot go as dark as a normal horror game, and the reason is mechanical.** The core loop is spot-the-difference. If the player cannot resolve detail, they cannot notice that a fixture moved, a light changed colour, or growth advanced a stage — and an anomaly that can't be perceived reads as an unfair loss, not as dread. Darkness in most horror games hides a threat that will announce itself. Here, darkness hides *the thing the player is scored on noticing*.

So the target is **dark but legible**: crushed blacks in the negative space, but every fixture on the checklist and every anomaly site sitting inside a pool of motivated light. Contrast does the atmospheric work, not overall dimness. If a first pass looks moody but you can't read the room, it's wrong for this game even though it would be right for another one.

Practical consequence: light placement is not decoration, it is **level design**. Each checklist fixture needs its own practical. The route should read as a chain of lit islands connected by dark.

### Baseline values applied to L_SectorC (2026-07-28)

The Sewers showcase map ships tuned for bright cinematic presentation and has to be re-graded:

| Setting | Showcase default | Substrate |
|---|---|---|
| SkyLight intensity | 5.0 | 0.45 |
| DirectionalLight intensity | 9.0 (white) | 0.5 (cold blue 0.62/0.78/1.0) |
| Fog density | 0.20 | 0.28 |
| Fog inscattering | 0.106/0.177/0.157 (bright green) | 0.011/0.017/0.021 |
| Volumetric fog albedo | ~white | 0.42/0.48/0.55 |
| Auto-exposure | enabled | **locked** (min=max=0.55) |
| Saturation / vignette | — | 0.8 / 0.55 |

**Locking auto-exposure is the load-bearing one.** With adaptation on, every attempt to darken the scene is silently undone — the eye adapts and you end up back where you started. Fix exposure first, then light.

---

## 9. Audio — the highest-risk system

This genre lives or dies here, and it is the one thing the bundle gives you nothing for.

- **Room tone per sector**, distinct enough to identify blind. Players should know they're in Sector C with their eyes closed.
- **Footsteps** with correct surface variation. Non-negotiable.
- **The terminal**: key clicks, confirmation chime, error tone. Make the error tone unpleasant.
- **Absence as a cue**: the scariest anomaly type is a room tone that stops.
- No jump-scare stingers. The moment you use one, you've told the player what kind of game this is and the dread deflates.

Budget: buy a sound library, or hire out. Do not attempt this with free-tier assets.

---

## 10. Technical build list

| System | Form | Difficulty |
|---|---|---|
| `BP_FirstPersonPawn` | UE FP template, weapon stripped. Walk ~250 u/s, no sprint, head bob. No player mesh. | Low |
| `BP_Fixture` | Checkable object. States: nominal / degraded / absent. Interaction prompt. | Low |
| `DA_Anomaly` | Data asset: target, type, min round, severity. | Low |
| `BP_AnomalyDirector` | Per round: rolls how many anomalies, picks from valid pool, applies them. | Medium |
| `BP_ObserverComponent` | Frustum + line-trace visibility test driving growth advance. | Medium |
| `BP_RoundManager` | Round counter, checklist generation, completion validation, escalation gating. | Medium |
| `WBP_Terminal` | Diegetic handheld UI. Rendered in world on a held mesh, not a screen overlay. | Medium |
| Persistence | Round state, growth states, flagged/missed anomalies across sessions. | Medium |
| Audio | MetaSounds for room tone and procedural variation. | High |

Nothing here needs an animation blueprint, navmesh, behavior tree, or skeletal mesh.

---

## 11. Scope & milestones

| Milestone | Content | Estimate |
|---|---|---|
| **Vertical slice** | Sector A+B only. 3 rounds. 5 anomalies. No audio pass. Proves the loop is scary. | 2–3 weeks |
| **Steam demo** | Sectors A–C. 8 rounds. Full audio and lighting pass on those sectors. Ends on a hard hook. | ~2 months |
| **Full release** | All 6 sectors. ~20 rounds. 2–3 hours. | ~6 months |

**Gate:** if the vertical slice isn't unsettling with placeholder audio, the design is wrong and no amount of polish saves it. Kill or rework at that point, not at month five.

> **GATE VERDICT — 2026-07-29, PASSED.** First full playtest (testbed route in Sector C, no audio, debug text on screen, dev teleports mid-run): when the round-2 Absence anomaly hid a lamp, Murat's reported experience was, verbatim, *"i felt exactly 'wait, where is it?'"* — from the person who built the system and knew the trick. The core loop produces the intended feeling under worst-case presentation. The design is validated; proceed to content and polish.

---

## 12. Steam plan

This section matters more than everything above it. **Games with under 5,000 followers have a ~98% chance of earning below the ~$250 median.**

1. **Store page live immediately** — before the vertical slice exists. Target nine months of runway.
2. **The hook line for every trailer, screenshot, and post:** *"The checklist has no field for what you're seeing."* Lead with the idea, not the monster — there isn't one.
3. **Screenshots are your advantage.** These kits are genuinely beautiful and most horror indies look cheap. Lean hard on visual quality in the capsule and gallery.
4. **Demo built as a marketing asset**, targeted at a Next Fest. Not a test build.
5. **Discord over broadcast.** 200 engaged members beats 20,000 passive followers.
6. **Price $9.99.** Two to three hours of atmospheric horror supports it. Do not price at $3–5 — that signals "asset flip" and invites the comparison you're trying to escape.

---

## 13. Risks

- **Audio is the single point of failure.** Visuals are handled; audio isn't, and it's what makes this genre work.
- **Rounds 1–2 are a churn risk.** Repetition is both the mechanic and the danger. Front-load the first anomaly.
- **The kits fight the tone.** Bright cinematic sci-fi has to be dragged into horror through lighting and post. This is real work, not a slider.
- **Perf:** Nanite plus many local lights plus volumetric fog in enclosed spaces will need profiling. Dark scenes are not automatically cheap.
- **Two projects at once.** Inspection Station shares this game's core systems — inspection state, checklist UI, a defect data model, "did the player actually notice this" logic. Build those systems so they transfer, and the split costs far less than it looks like.

---

## 14. Open questions

- Is the player character voiced, or silent? (Recommend: silent, with terminal text as the only narration.)
- Does the facility have other staff — referenced but never seen? (Recommend: yes. Absence is cheaper and scarier than presence.)
- Does the game have an ending, or a terminal loop? (Recommend: a real ending. Ambiguous non-endings read as unfinished.)
- Name check: is "Substrate" clear on Steam and USPTO?
