# Third-party audio

| Asset | Source | Licence |
|---|---|---|
| `Content/Substrate/Audio/FS_Concrete_01`–`05` | Kenney, *Impact Sounds* 1.0 (`footstep_concrete_000`–`004`), https://kenney.nl/assets/impact-sounds, downloaded 2026-10-25 | CC0 1.0 (public domain). Credit not required. |

The files were converted with `_tools/convert_kenney_footsteps.py` (mono, leading silence trimmed, peak-normalized to −6 dBFS).

Everything else in `Content/Substrate/Audio/` is generated in-house: `AMB_RoomTone_Hum` by `_tools/generate_room_tone.py` and `FS_Soft_*` by `_tools/generate_footsteps.py`. The older `AMB_*_Loop` and `FS_Sewer/River/WetConcrete` files come from earlier sessions.
