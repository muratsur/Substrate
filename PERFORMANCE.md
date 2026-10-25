# Performance check (2026-10-25)

This was measured on the dev PC with a Development build (`Windows_DevPerf_20261025_181505`), windowed, VSync off and no frame cap.

**Method:** `_tools/perf_route.py` teleports the player to each spot (`BugItGo`) and records 1800 frames with the CSV profiler. It summarises the last 300, after loading has settled.

| Spot | 1920 × 1080 avg / p95 | fps | 2560 × 1440 avg / p95 | fps |
|---|---|---|---|---|
| Dock (spawn) | 8.8 / 9.8 ms | 113 | 10.0 / 11.0 ms | 100 |
| West corridor | 9.3 / 10.2 ms | 107 | – | – |
| Canal arch | 9.8 / 10.7 ms | 102 | – | – |
| East bank | 9.4 / 10.4 ms | 106 | – | – |
| Transit B | 9.0 / 9.8 ms | 111 | 10.2 / 11.1 ms | 98 |
| Sector D | 10.0 / 10.9 ms | 100 | 11.8 / 12.8 ms | 85 |

## Findings

- **No hotspot.** The slowest frame anywhere was 14 ms (1440p, Sector D).
- **GPU-bound.** The render thread mostly waits on the GPU (GPU 7.4–10.7 ms). Draw calls range from 364 to 3,368 per spot with little effect on frame time, so batching or merging the rubble would not pay off.
- **Not covered:** hitches while walking or streaming between areas (each spot was measured after teleporting and settling), and other GPUs.

Rerun with `python _tools/perf_route.py <DevPerf build dir> [spots] [--1440] [--shot]`.
