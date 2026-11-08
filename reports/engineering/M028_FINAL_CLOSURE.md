# M028 final numerical closure

**NEUROMANCER V2 CORE RELEASE HOLD.** The optimized certificate completed locally and on hosted Linux, but the final macOS Intel execution exhausted its unchanged 240-second budget. No merge, tag, release or public-asset installation was performed. The optional SDK and personal-style branches remain outside this work.

## Identity and decisions

Starting evidence: `2c2811145ba8d20960fb5e0dbf9710270d3d2513`. Original M027 implementation: `88b6e94d7e5db572ddc8a954f46e1dec7f9b3d4f`. Final tested M028 implementation: **`e2836b355950c62e5dac6f69abee92e2476fe92c`**, branch `codex/m028-numerical-closure`. The closing report and artifacts are on a separate evidence branch; they are not represented as another tested implementation. The immutable plan is `reports/engineering/M028_PLAN.md`.

Final remote inspection still found main at `db4485613cba8128ee643159b25ef29523ca6c95` and no GitHub releases/tags. Publication authorization was conditional on passing all mandatory gates; its condition is unmet.

| Boundary | Decision | Executed evidence |
| --- | --- | --- |
| Numerical certificate | **HOLD** | Linux 40/40; macOS 29/40 plus partial branch, then DEADLINE_EXCEEDED |
| Core regression | **PASS** | 292 tests on each hosted platform, zero failures/errors/skips |
| Cleanup behavior exercised here | **PASS** | Cutoff worker reaped, cleanup verified, no outer watchdog; original process/clock tests enabled |
| Fresh three-round A1 confirmation | Local PASS; hosted NOT RUN as a separate repeat stage | Local 18 checks; hosted full regression includes the phase tests, but does not substitute for a fresh three-round hosted campaign |
| Historical protection | **PASS** | 38,721 paths, original manifest unchanged; no new exemptions |
| Remaining numerical evidence | Local PASS for specified existing stages; cross-platform **INCOMPLETE** | Local exact 102-array replay, V1, M013/M014; no universal portable coverage asserted |
| Review wheel installation | **PASS** | Fresh pinned environment, pip check, installed imports/CLI outside checkout |
| Core release readiness | **HOLD** | macOS resource gate and remaining cross-platform obligations unmet |
| Full SDK reliability / optional style | **HOLD / excluded** | Neither limitation repaired by this campaign |
| Biological validation / hardware | **NOT RUN / NONE** | No biological or physical device operation |

## Changes and mathematical boundary

Production `src/neuromancer/`, dependency pins, original verifiers, scientific archives, protocols, controller parameters, supervisor and clock implementations are unchanged. The complete changed-file inventory is in the retained source record. New implementation files are:

- `tools/m028_arithmetic.pyx`: verification-only compiled enclosure and residual kernels.
- `tools/m028_build.py`: bounded, explicitly flagged compiler invocation with source/generated-C/binary hashes.
- `tools/m028_backend.py`: isolated verifier namespace, immutable query caching and explicit positive-denominator checks.
- `tools/m028_io.py`: append-only durable checkpoint ledger and checked reconstruction.
- `tools/m028_verify.py`: fixed paired measurements and staged use of the original M027 archive driver.
- `tests/test_m028_arithmetic.py`, `tests/test_m028_io.py`: 17 additional tests.
- `.github/workflows/m028-kernels.yml`: finite Linux/macOS compiled-verifier qualification. Original core, substrate and experimental SDK workflows remain enabled.

The existing operation-derived portability contract is unchanged. All original native RLS updates, state checks, planner decisions and tie semantics remain present. The implementation does **not** use block-endpoint-only checks. Variant C fused the same per-step scalar operation tree instead of introducing an unnecessary block error model. No information radius is reset to a saved state.

With standardized input `z` and centered observed output `v`, the continuously enclosed information equations remain

```
S[k] = lambda*S[k-1] + z*z.T
h[k] = lambda*h[k-1] + z*v.T
```

Initial `S=P0^-1` is certified by a Neumann residual; `h=S*theta0`. Here `z` has 41 entries, `theta` and `h` have shape `(41,4)`, and `S`, covariance and their radii have shape `(41,41)`. The compiled implementation keeps NumPy center matrix products and their order. It fuses only the surrounding scalar validation, outward rounding and radius operations, and avoids products with provably zero radii. The subsequent outward-addition order is retained. Bounds for the finite test fixtures match the original M027 center/radius bytes; this is stronger evidence than matching selected actions alone, but not a proof for arbitrary machines or unsupported arithmetic domains.

For a candidate inverse `B`, the original residual argument remains:

```
eta = ||I-S*B||_inf < 1
||S^-1||_inf <= ||B||_inf/(1-eta)
||theta-S^-1*h||_inf <= ||S^-1||_inf * ||h-S*theta||_inf
||B-S^-1||_inf <= ||S^-1||_inf * eta
```

Every residual and norm in these formulas includes its enclosure and reduction rounding. Native and saved dense states are bounded against the **same continuously accumulated** ideal equations, not against reinitialized reference checkpoints. Directional prediction queries retain the original nullspace cancellation and feed the original objective enclosure and `certify_choice` implementation. The gamma bound `gamma(n)=n*u/(1-n*u)` and outward `nextafter` operations are unchanged. A radius that cannot be justified is rejected, not replaced by a tolerance.

The additional explicit denominator guard encloses `lambda + z.T*P*z`, including two dot products and their addition. The previous certified covariance-norm error is conservatively propagated through `||z||_1^2`; the lower endpoint must remain positive. The initial shared covariance has zero comparison error, while every later covariance is associated with its preceding residual certificate. Object identity plus an independent snapshot guards against mutation/reuse. This does not reset uncertainty or modify production RLS. All 128,000 updates on each complete trajectory set satisfied this guard; minimum lower bound was 0.999650317138373 locally and 0.9996503171440128 on the retained macOS prefix.

Required arithmetic assumptions are finite normal IEEE binary64, round-to-nearest, and supported finite reductions. Builds use `-O3 -fno-fast-math -ffp-contract=off -frounding-math`, pinned Cython 3.1.3, and a checked eight-byte double/rounding mode. Unsupported subnormal inputs, multiplication/division underflow, overflow, nonfinite values and nonpositive denominator bounds fail closed. Fast-math and FMA contraction are not enabled. Binary hashes, generated C and build logs are retained per host; byte-identical compiler output across platforms or build paths is **not** claimed. The extension is built outside the package and is absent from the research wheel.

Immutable query reuse keys on exact normalization/history bytes and array shape/dtype. A cache hit additionally verifies the candidate-bank bits, including signed zero. Cached arrays are read-only; changed banks under an identical key are rejected. It does not cache model-dependent answers, labels or simulator state. The local full stage recorded 2,545 hits and 15 misses.

Checkpoint publication still occurs at the original cadence. Newly appended JSONL rows are flushed/fsynced before the original atomic pointer publication. The pointer records a committed byte offset, count and SHA-256 chain; reconstruction validates all three. An interrupted pointer write retains an uncommitted tail and refuses reuse of that stage directory. No checkpoint, intermediate update or final full certificate is dropped. Production persistence is untouched. Neither the old writer nor this adapter establishes a new directory-fsync/power-loss guarantee.

## Finite search and rejected attempts

The benchmark-optimization-loop skill was used: measured baseline, declared limits, one-hypothesis variants, independent correctness gates, paired samples, and no unchanged-source retry after a failed full stage. Six development batches and two distinct-source hosted kernel matrices were used; the third allowed matrix was not consumed after the mandatory final cutoff failure.

| Variant | Observation | Disposition |
| --- | --- | --- |
| A0 | Cython negative-index/wraparound defect caused a contained SIGSEGV in a matrix-product fixture | **Rejected**; generated C, binary/build hashes, crash and supervisor failure retained |
| A1 | Checked indexing, fatal Cython warnings; seven focused tests passed; local paired kernel gain about 1.9–2.1x | Soundness-qualified limited prototype; insufficient performance alone |
| B | Exact-zero product and scalar metadata elision; seven focused tests passed; local gain about 2.2x | Retained in C; no looser numerical bound |
| C | Fused identical per-step information/residual kernels; immutable query reuse; streamed durable checkpoint publication | Best measured qualified kernel; full cross-platform runtime gate still fails |

Subsequent batches extended independent soundness checks to 12, then 16 tests; the final focused qualification ran all 17 new tests. Final hosted kernel-only soundness ran 14 arithmetic cases per host; the complete 292-test core suite also ran the three I/O cases. Deterministic 90-digit Decimal tests cover gain, covariance, coefficients, prediction, objective and an independently calculated candidate. Original M027 near-tie, ill-conditioned, invalid-domain, clock and exact-action tests remain enabled. Sixty-five sequential updates compare continuous information centers/radii to M027; there is no intermediate reference reset. Passing these fixtures is not presented as an exhaustive proof of every possible floating-point computation.

## Performance measurements

Kernel samples each contain 256 sequential 41-dimensional updates and all corresponding native/state checks. Three process-local pairs use counterbalanced original/compiled order. Every raw latency, CPU sample and digest is retained; no adverse sample is excluded. Startup, compilation and acquisition are separate from timed kernels. The paired output digests of information centers/radii and final coefficient bound agree exactly.

| Hosted sample | Original seconds | Compiled seconds | Ratio |
| --- | ---: | ---: | ---: |
| Linux pair 1 | 0.925145 | 0.166477 | 5.557x |
| Linux pair 2 | 0.927315 | 0.166538 | 5.568x |
| Linux pair 3 | 0.978708 | 0.176647 | 5.540x |
| macOS Intel pair 1 | 2.867579 | 0.763209 | 3.757x |
| macOS Intel pair 2 | 2.434774 | 0.577558 | 4.216x |
| macOS Intel pair 3 | 3.001089 | 0.721889 | 4.157x |

Compiled per-update p95 ranges were 0.692–0.727 ms on Linux and 2.771–5.880 ms on macOS; all p50/p95/p99/max samples are in `benchmark.json`. These are verifier workloads, not production controller latency improvements, and three pairs do not establish a population timing distribution or hard-real-time behavior. The broad macOS sample variation is visible, not averaged away.

| Stage | Local arm64 | Linux | macOS Intel |
| --- | ---: | ---: | ---: |
| 256-update prerequisite, s | 0.143 | 0.318 | 0.814 |
| First complete branch, s | 1.328 | 3.866 | 13.792 |
| Former n5/r47 LOSS dependency case, s | 1.341 | 3.860 | 10.335 |
| First four branches, s | 5.417 | 15.040 | 39.164 |
| Full stage complete branches | 40/40 | 40/40 | **29/40** plus partial thirtieth |
| Retained updates | 128,000 | 128,000 | 93,000 |
| Completed certified planner decisions | 2,560 | 2,560 | 1,861 |
| Worker full-stage wall time, s | 54.782 | 148.735 | unavailable: terminated |
| Supervisor elapsed, s | 54.869 | 148.922 | **239.489** |
| Final status | COMPLETED | COMPLETED | **DEADLINE_EXCEEDED** |

The four-branch component returns a component PASS only; its original incomplete global-study result is retained. Local completion improved from the reported M027 predecessor's 204.58 s to 54.78 s, about 3.73x; these are different executions, not a paired confidence interval. M027 hosted complete-runtime figures were forecasts, so no measured end-to-end speedup versus a completed M027 hosted run is invented.

Linux full-stage CPU time was 146.647 s; measured peak RSS was 87,852 KiB (about 85.8 MiB). Local CPU was 53.029 s and peak RSS 86,065,152 bytes (about 82.1 MiB). macOS full-stage CPU and peak RSS were not published before termination and remain **unavailable**; its completed kernel benchmark peak is not substituted for a full-stage maximum. Local hardware was Mac17,2, 16 GiB, 10 reported CPUs. NumPy configuration/runtime reports and exact pinned dependency/build records are retained. Requested one-thread environment settings are not a claim that every BLAS thread pool was independently observed.

Final component totals, seconds:

| Component | Linux complete | macOS retained prefix |
| --- | ---: | ---: |
| Information recurrence | 30.346 | 48.966 |
| State residual/inverse bounds | 38.648 | 65.663 |
| Native RLS update | 19.840 | 28.093 |
| Native planner | 27.417 | 44.602 |
| Planner certificate | 14.879 | 25.332 |
| Archive + plan loading | 4.940 | 5.892 |
| Durable progress writes | 3.573 | 4.754 |
| Digests | 2.640 | 5.812 |

These counters do not independently separate every allocation, outward-rounding primitive or BLAS call. Such work remains included in its enclosing component; no invented subcomponent attribution is supplied. On the macOS retained prefix, information and state checks still cost about 114.63 s; native update and planner cost another 72.69 s. Eliminating the measured 4.75 s logging alone cannot close the gap. Under unchanged-prefix throughput, 128,000 updates would take approximately **329.6 s**, requiring about **1.37x further total improvement** to fit 240 s. That is an extrapolation, not a completed runtime or a proof that another sound implementation is impossible. The present finite search does not meet the mandatory cap and stops here.

## Numerical outcomes and failure boundary

Local maximum coefficient radius over all updates: 6.3200e-09; covariance radius: 1.0750e-08; checkpoint cost radius: 1.8910e-08. Linux complete maxima: 6.2941e-09, 1.0707e-08 and 1.8829e-08 respectively. macOS **checkpoint-only prefix** maxima: 6.2862e-09, 1.0162e-08 and 1.8831e-08; unretained per-update/final maxima are not known.

For complete local/Linux trajectories, all 2,560 original exact chosen actions and delivered policies passed. The macOS prefix passed its retained 1,861 planner certificates. The smallest archived non-tie cost gap among these plans was 2.2465998319e-06. The supplementary archive-gap-minus-four-radii statistic remained above 2.1960e-06. This statistic does not replace the actual certificate's original near-tie/tie-break checks. No tie threshold was changed.

Local state digest differences were zero. Linux had 128,000 differing floating state digests; macOS had 93,000 in its retained prefix. These differences remain recorded. They are not accepted merely because nominal actions match: continuous residual bounds, dense saved-state comparisons, objective enclosures and exact decision checks are required. Passing this RLS subset is not universal certification of the other floating families.

The final macOS retained location was network **7**, replicate **47**, `LOSS_RLS-MPC`, step **200**. The work cutoff was 992514370682 ns, the absolute deadline 993314370682 ns in its boot-scoped continuous-clock domain. STOP_REQUESTED occurred at 992533092415, TERM at 992745293276, and reaping at 992793426378. Final publication was at 992803685496 ns. Returned status is DEADLINE_EXCEEDED, worker terminal is FORCED_TERMINATION, return code -15, parent reaped, cleanup verified, no persistence errors, no outer watchdog intervention. No complete final certificate exists for this stage. Missing work is not counted successful.

## Core, cleanup, scientific evidence and remaining obligations

The exact-source hosted core suite passed **292 tests and 46 warnings** per platform: Linux JUnit 102.505 s, macOS 272.271 s. All 260 original tests, 15 M027 tests and 17 M028 tests remain enabled. The existing warnings are retained Brian2/pyparsing deprecations; no test failure or skip was hidden. The core workflow also ran the existing M008 process diagnostics, built/installed the wheel, pip check and CLI smoke. The same-source substrate workflow passed.

One local full-suite attempt was interrupted by uncontrolled clamshell sleep after 187 completed tests. Its unchanged 180-second continuous-clock deadline was already exceeded when the machine next scheduled the supervisor; it retained DEADLINE_EXCEEDED, elapsed 4,824.124 s and verified cleanup. Worker log time, OS power events and the terminal clock timeline support suspension as the cause. This was not a controlled sleep test or a passing local regression. It was not retried. Subsequent focused qualification used an idle-sleep assertion, which does not prevent clamshell sleep and does not alter clock semantics. The hosted full-suite passes are independent executions, not a relabeling of this failure.

Local A1 confirmation ran a fixed three rounds of six tests under a separate 180-second supervisor: **18/18**, no skips or errors. Running-phase successful cleanup and cancellation-phase expected resource failure remain distinct; no CLEANUP_FAILURE was classified as success. Hosted full regression includes the original A1 tests, but the separately repeated hosted A1 confirmation was not launched after the mandatory numerical cutoff failed. Historical M027 hosted confirmation remains historical evidence only.

The separately budgeted existing local remaining stage completed in **101.235 s** under its original 240-second contract, with verified cleanup and no watchdog:

1. Fixed ridge coefficients/inverse residuals and structural C02 rank/SVD checks passed. Coefficient comparison radius was 6.4245e-12; initial inverse contraction 6.0615e-11; reduced minimum singular-value lower bound 23.869. All ten M013 probe-condition bounds passed.
2. Original strict neural/golden replay reproduced **102 arrays**, including exact dtype, shape and values, and the original records on this reference host. This was engineering replay, not new scientific acquisition.
3. Original V1 saved-evidence reproduction passed, including exact canonical four tables/summary and all four figure bytes. The original model-state, event, action, statistical and constraint checks were not suppressed.
4. Original strict M013/M014 analyses reproduced from copies, with scientific summaries unchanged.

**These local results do not complete the cross-platform acceptance contract.** The M028 hosted kernel workflow does not claim to execute remaining golden/ARX/fitting/archive families after the RLS matrix. The prior known strict-byte portability failures remain preserved. A universal operation-derived certificate for all those families was not implemented or asserted. Fresh M015 reduced-simulator and M016 SDK archive numerical replay was not run in this campaign; their protected data/source hashes were verified. Their historical qualifications remain unchanged, not newly promoted. The stop rule forbids release while these mandatory obligations or the full macOS stage are incomplete.

Historical preservation verified all **38,721** paths with the unchanged baseline manifest SHA-256 `f88c41d51355e115863fd1a12dee6901aa4034ac7bf68f86c0c64e622e1719b1`. The four existing exact-hash active-file authorizations are unchanged. No source-directory/test-directory exemptions or additional replacements were introduced. No locked network was opened.

## Hosted evidence

Final implementation `e2836b355950c62e5dac6f69abee92e2476fe92c`:

- [Compiled verification matrix — Linux PASS, macOS deadline FAIL](https://github.com/adithyakupad/neuromancer/actions/runs/42495842007).
- [Core package/regression — both PASS, 292 tests each](https://github.com/adithyakupad/neuromancer/actions/runs/42495842099).
- [Substrate — PASS](https://github.com/adithyakupad/neuromancer/actions/runs/42495842095).
- [Incidental unchanged SDK matrix — executed PASS](https://github.com/adithyakupad/neuromancer/actions/runs/42495841982). This is not evidence of a scheduling repair.

Earlier A1 implementation `1368a7aec23c3d7372f39dc4adebdff664253356`:

- [Limited kernel/prerequisite matrix — PASS](https://github.com/adithyakupad/neuromancer/actions/runs/42450473090); it did not run the final full forty-branch matrix.
- [Core — PASS](https://github.com/adithyakupad/neuromancer/actions/runs/42450473092), [substrate — PASS](https://github.com/adithyakupad/neuromancer/actions/runs/42450474340).
- [Incidental SDK failure retained](https://github.com/adithyakupad/neuromancer/actions/runs/42450473091). No SDK diagnosis/repair or unlimited retry was performed. Later success does not erase this failure or the M019 producer-boundary limitation.

## Package and provenance

Review artifact **`neuromancer-2.0.0rc1-py3-none-any.whl`**, 95,561 bytes, SHA-256:

```
6207aad869792e3ac74c9e3dbfe9a489d09bfadc282110ba2ffb9ea377244683
```

A fresh environment installed the unchanged pinned dependencies and this wheel. `pip check` reported no broken requirements; imports resolved to fresh site-packages. Installed CLI smoke ran from `/tmp`, outside the checkout, under the original 120-second supervisor and returned COMPLETED with verified cleanup. All 36 packaged Python modules match tested source bytes; MIT license matches; there are no NPZ/NPY/HDF5 scientific archives or compiled M028 verifier in the wheel. Python requirement remains `>=3.12,<3.13`; package version remains `2.0.0rc1`. ZIP build timestamps can change wheel bytes; no claim of byte-identical wheel builds is made. The wheel is a review artifact, not a published release asset.

Raw attempts, generated compiler sources/binaries, crash evidence, every benchmark sample, partial/full certificates, ledger chains, local suspension evidence, hosted artifacts/logs, cleanup reports, wheel and install records are under `reports/engineering/evidence/m028_final_closure`. `artifact-manifest.json` hashes the retained archive and wheel. The raw bundle excludes only the disposable fresh virtual environment and Python bytecode; dependency install/freeze/import records are retained. Failed and partial attempts are not excluded. `summary.json` preserves machine-readable measured results; `raw-attempts.tar.gz` contains the underlying records.

## Scientific findings preserved

- V1 PI **11.46875**, adaptive RLS-MPC **13.12921875**, fixed MPC **18.9778125 Hz·s**. Adaptive superiority over PI remains **FAIL**.
- M013 reward-modulated superiority and M014 recurrence-specific memory superiority remain **INCONCLUSIVE**; confirmations **NOT RUN**.
- M015 cue access remains **FAIL**; retention **NOT RUN**; historical reduced scalar LIF verification remains qualified.
- M016 simulator causality remains demonstrated only on executed synthetic workloads. PI MAE remains **1.50** versus no-pulse **1.00 spikes/bin**; control improvement remains **FAIL**.
- Earlier V0.1/V0.2, model-superiority and short-horizon recovery failures remain untouched. No new scientific cohort, biological validation or physical hardware execution occurred.

## Reproduction and final boundary

From the tested implementation, in the pinned core environment:

```sh
PYTHONPATH=.:src python scripts/m014_supervise.py runs/m028-build-guard 120 python tools/m028_build.py runs/m028-build
export M028_KERNEL_DIR="$PWD/runs/m028-build/lib"
python -m pytest -q tests/test_m028_arithmetic.py tests/test_m028_io.py
PYTHONPATH=.:src python scripts/m014_supervise.py runs/m028-kernel-guard 180 python tools/m028_verify.py runs/m028-kernel --stage kernel
# Execute in order: 256, first, dependency, multi; each has its declared 180-second guard.
PYTHONPATH=.:src python scripts/m014_supervise.py runs/m028-all-guard 240 python tools/m028_verify.py runs/m028-all --stage all
# Separately budgeted original remaining stage; local success is not cross-platform proof.
PYTHONPATH=.:src python scripts/m014_supervise.py runs/m028-remaining-guard 240 python tools/m027_remaining.py runs/m028-remaining
```

Use fresh output paths; never truncate/reuse a failed ledger. The exact hosted workflow retains failures and always uploads artifacts. A failure stops promotion, not artifact collection.

The achieved kernel improvement is real, but it does not satisfy the full macOS cap. A future sound implementation would need at least the remaining measured throughput improvement and complete portable coverage of the remaining numerical families, followed by exact-source mandatory qualification. No larger timeout, missing state, blanket tolerance, changed tie rule or nominal-only action comparison is approved here. This campaign stops with evidence-complete HOLD rather than starting another optimization/research mission.

**NEUROMANCER V2 CORE RELEASE HOLD.**
