# M022 personal-style performance qualification

**Engineering PARTIAL · Scientific NOT RUN · Style release HOLD.**

Tested M017 baseline `4ec262486ab953591b90c860dd3515ce531789b7` and
style `f5703ce048c30ac4fa050c5b5f9bde3e3b73c296`, from distinct
source archives and identically pinned environments. The harness was
frozen at `7e52251e42a1ed4b8be8878882b4e63b0bd164c2`. All twelve
pairs ran once in alternating order. Each process retained all
nine samples per original kernel, including its first sample.
Every process verified all 102 arrays by dtype, shape and bytes
and all deterministic records against the original M017 reference.
The 24 NPZ containers and JSON records also share identical file
hashes. One copy of each is retained alongside the 24 hashes.
The complete raw timings, load samples, CPU times, logs, RSS and
BLAS inspection results are archived.

| Workload | p50 ratio | Baseline → style p95 (ms) | p95 ratio and paired 95% interval | Wall gate |
|---|---:|---:|---|---|
| FIR ×1000 | 0.991 | 10.934 → 11.415 | 1.044 [0.915, 1.463] | HOLD |
| RLS ×100 | 0.991 | 4.572 → 4.824 | 1.055 [0.977, 1.150] | PASS |
| Planner 625 candidates | 0.987 | 9.920 → 9.746 | 0.983 [0.759, 1.008] | PASS |
| PI ×1000 | 0.990 | 9.296 → 6.041 | 0.650 [0.617, 0.974] | PASS |
| ARX fit | 0.990 | 4.218 → 4.335 | 1.028 [0.961, 1.491] | HOLD |
| Plasticity ×100 | 1.006 | 1.920 → 1.948 | 1.015 [0.951, 1.123] | PASS |
| MEA ×100 | 1.008 | 4.032 → 5.491 | 1.362 [1.048, 1.592] | FAIL |
| Reservoir ×100 | 1.015 | 0.713 → 0.915 | 1.284 [0.987, 1.395] | FAIL |

Wall ceilings were 1.10 median and 1.20 p95. Whole-pair percentile
bootstrap used seed 18017 and 10,000 draws. The evidence table retains
CPU, p99, per-pair and per-order results. Peak RSS was 994,459,648 vs
990,134,272 bytes, ratio 0.996 [0.992, 1.004], below the 1.10 ceiling.
Median process wall time was 10.441 vs 10.491 s and median process
CPU 10.265 vs 10.274 s. One-minute load at process entry spanned
2.38–3.33 and 2.39–3.30 respectively. NumPy reported an Accelerate
build. The processes requested one-thread settings, and threadpoolctl
reported no observable pools on this build. Actual thread counts
inside Accelerate remain unverified. The supervisor completed in
276.924 s with verified cleanup, within the 1800 s/2 GiB budgets.

Planner and PI met the prospective gate here. The original one-pair
M017 failures remain in the record. Both MEA and reservoir files,
as well as the planner file, have exact Python AST equality to
baseline after ignoring positions. The affected files therefore
show no additional source-level calculations or changed branch
structure. This does not identify the source of the tail variation.
The jointly benchmarked branch cannot establish independent
qualification for a cherry-picked subset. Preserve all style
improvements in the review branch, including named RLS residual
and PI proportional and integral intermediates. Integrate none
of the 18 files in this sprint. No new performance threshold was
introduced after outcomes.
[Raw evidence](evidence/m022)
