# V1.1 P0 preregistration

Baseline scientific implementation: `abd811a053e10ad7ee5126efbc95fefd73e55c8d`.
No production code changed in P0. Fixed manifest: `benchmarks/v1_1_manifest.json`.
Run with pinned Python 3.12 stack and `PYTHONPATH=src python benchmarks/v1_1.py --output FRESH`.
900-second suspend-inclusive shared supervisor deadline per stage, 4 GiB per-worker RSS gate,
maximum three variants; no reserved or locked networks. Measurements and profile attribution
precede changes. Targets: 2x workflow and neural throughput; 30% planner p95 reduction.
Exact numerical equivalence is mandatory; unattained speed targets remain failures.
OS cache is not flushed: first subprocess import is process-cold, not disk-cold.
Profiler/tracemalloc runs include instrumentation overhead; comparisons use identical harness.
