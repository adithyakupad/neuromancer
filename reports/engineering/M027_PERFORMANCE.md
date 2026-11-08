# M027 certificate performance

## Measurement boundary

Measurements concern verification code only. Production FIR/RLS, PI/MPC, neural simulation and their performance claims do not change. The original 240-second absolute archive-stage budget remains unchanged. No 2x neural throughput or 30% controller-latency goal is declared fulfilled.

Source lineage and mathematical assumptions are in `M027_NUMERICAL_CERTIFICATE.md`. The finite plan preceded execution. All four development batches, the initial hosted attempt and final guard attempt are retained. No unchanged source was rerun for a favorable sample.

Local platform: macOS arm64, pinned Python 3.12 core environment, NumPy 2.5.4, SciPy 1.18.0, Brian2 2.10.1. Hosted platforms use their recorded setup-python builds and numerical-runtime reports. Thread environment requests are recorded; `threadpoolctl` is absent in the observed Linux report, so actual BLAS pool behavior is **not verified**. Requested one-thread settings are not presented as standardized thread behavior.

## Baseline profile

One supervised process profiled the original 256-update prerequisite and first full saved branch. Workload reduction selected only the specified first job/branch in the profiler's JSON reader; archives and algorithms were not edited. Its original archive result correctly reports one of forty completed, not a qualified complete study.

Total worker wall time was 13.5254 s, CPU 13.1396 s, supervisor elapsed 13.6246 s. The first branch accounted for 12.976 s in cProfile. Peak RSS was 105,119,744 bytes. The following component times include instrumentation overhead; nested categories must not be added as independent costs.

| Component | Calls | Measured seconds | Share of profile wall |
| --- | ---: | ---: | ---: |
| Full candidate interval planner | 64 | 7.3768 | 54.5% |
| Recursive interval RLS | 3,456 | 5.0725 | 37.5% |
| Native RLS update | 3,456 | 0.1529 | 1.1% |
| Archive opening | 66 | 0.1380 | 1.0% |
| Choice certificate | 64 | 0.00485 | 0.04% |

Outward-rounding `upward` accumulated 6.045 s over 279,872 calls across the interval work. It overlaps the planner and RLS categories. Positivity/domain checks, temporary arrays and repeated outward rounding dominate; archive parsing is not the principal bottleneck. No allocation-volume measurement is claimed.

The original measured first-branch extrapolation is approximately 519 s for forty branches. This is a forecast, not a completed experiment. It excludes variation among branches and hosts.

## Proposed-method measurements

The first residual branch was also profiled, on the same local host with the same requested thread environment. It took 6.9428 s including initialization. The original first branch took 12.976 s inside its profiler: an observed approximately 1.87x reduction. This is one profiled process comparison, not a latency distribution or standardized cross-platform benchmark.

The planner enclosure averaged 18.88 ms per decision versus 115.26 ms for the original, approximately 6.11x in those profiles. Native planner evaluation averaged about 5.17 ms and remained unchanged. Verification latency improvement is not improved control performance.

The new information update and state residual together cost about 1.51 ms/update in the profiled first branch, versus 1.47 ms for the original recursive interval step across its profile workload. The gain is mainly removing candidate-array interval work and controlling dependency growth; it is not a demonstrated faster per-update RLS kernel.

The formerly rejected n5/r47 LOSS branch completed unprofiled in 4.8645 s, CPU 4.6716 s. Comparing its unprofiled time directly with the profiled original branch would be misleading.

## Complete local predecessor replay

All forty branches completed in 204.5757 s worker wall time, 199.3472 s CPU, 204.6683 s supervised elapsed, with verified cleanup and no outer watchdog intervention. Peak RSS was 64,880,640 bytes. The final source subsequently added exact fixed-objective and 100 Hz expression-envelope guards; its offline audit passed without rerunning the complete development replay. Final-head hosted results determine release qualification.

| Component | Calls | Seconds | Per call | Share of worker wall |
| --- | ---: | ---: | ---: | ---: |
| Information recurrence | 128,000 | 57.9133 | 0.452 ms | 28.3% |
| State residual/inverse bound | 128,000 | 69.3669 | 0.542 ms | 33.9% |
| Planner certificate | 2,560 | 34.8679 | 13.620 ms | 17.0% |
| Unchanged native planner | 2,560 | 12.4285 | 4.855 ms | 6.1% |
| Atomic progress publication | 2,560 | 17.5825 | 6.868 ms | 8.6% |
| Plan archive loading | 2,560 | 3.8534 | 1.505 ms | 1.9% |
| Native model update | 128,000 | 3.8417 | 0.030 ms | 1.9% |
| Model digest | 128,000 | 0.9825 | 0.0077 ms | 0.5% |
| Branch archive loading | 40 | 0.1993 | 4.982 ms | 0.1% |

Progress writes serialize the growing checkpoint list, so later writes cost more than those in the first branch. The measurements include JSON generation, atomic write and durability, not isolated filesystem service time. No durability step was removed. Supervisor elapsed minus worker elapsed is about 0.093 s in this execution; it includes launch/observation overhead and is not an isolated IPC benchmark.

The local run certified approximately 625.7 updates/s or 12.51 planner checkpoints/s. These are verifier-throughput measurements, not simulated biological seconds per second.

Baseline peak RSS includes the prerequisite plus original planner and profiler, whereas the residual-first process has a different retained object set. The smaller observed peaks are reported but are not a controlled memory-saving claim. Full replay memory was within the existing environment's supported resources; hosted interrupted-stage peak RSS may be unavailable.

## Hosted budget and optimization ceiling

The initial Linux attempt passed prerequisites but stopped at the original cutoff after sixteen complete branches and 51,200 updates. Its first and dependency branches took 14.6298 s and 14.5289 s. Extrapolating those complete branch measurements gives about 581–585 s for forty, not an actually executed full runtime.

That interrupted prefix recorded 73.75 s information-update work and 91.17 s state-residual work, versus 7.21 s progress publication, 1.68 s plan loading and 1.76 s digests. These are retained prefix totals, not complete-study totals. No complete certificate exists for that run. Verified cutoff cleanup is not scientific or numerical success.

The implementation therefore fits the local reference host but does not fit the mandated hosted environments in these executions. Final-source completion counts, exact statuses and cleanup records are below.

### Final-source hosted measurements

| Metric | Linux | macOS Intel |
| --- | ---: | ---: |
| First full branch | 15.1365 s | 39.1277 s |
| Dependency-growth branch | 15.3582 s | 32.3022 s |
| Full-stage retained updates | 49,300 | 29,250 |
| Complete branches / prescribed | 15 / 40 | 9 / 40 |
| Supervisor elapsed | 239.4204 s | 239.5442 s |
| Information-update prefix work | 79.1440 s | 79.3091 s |
| State-residual prefix work | 87.9087 s | 88.5958 s |
| Planner-certificate prefix work | 42.2922 s | 42.3818 s |
| Progress-publication prefix work | 7.1025 s | 5.1956 s |
| Cleanup verified / watchdog intervention | Yes / none | Yes / none |

Both stages returned DEADLINE_EXCEEDED. The checkpoints precede some additional work before TERM; unretained last operations are not counted as certified completion. Full-stage CPU and peak RSS were not published before termination and remain unavailable. Resource figures from completed prerequisite branches are not substituted as full-stage maxima.

Throughput-based extrapolation from the final retained prefixes is about 622 s on Linux and 1,048 s on macOS for forty branches. These are forecasts under similar work rates, not completed measurements or guaranteed runtimes. They imply approximately 2.59x and 4.37x further improvement to fit 240 s. The earlier initial-source failures, sixteen and seven complete branches respectively, remain in evidence; no unfavorable sample is excluded.

The expensive information/state checks account for about 167 s of each final prefix. Removing the roughly 5–7 s of progress writes would not close that gap. The measured current implementation does not satisfy the hosted budget. A stronger universal optimization ceiling is not established by these samples.

Logging alone is not enough: in the complete local measurement, eliminating all progress-writing time would yield at most about 1.09x under the fixed-work Amdahl assumption. Eliminating both logging and planner-certificate work would yield at most about 1.34x. Those ceilings concern these specific removed costs, not every possible future implementation. Information/state checking remains the main work. No universal impossibility or optimized lower bound is claimed.

The smallest promising unexecuted approach is batched residual verification over fixed blocks, while retaining sequential native updates and continuous information-error propagation. It would need a sound block-rounding derivation, exact boundary/action checks and new independent tests. Simply checking fewer states, changing checkpoint frequency, dropping durability or raising the 240-second budget is not qualified. No such additional development loop was started.

## Execution records

Four bounded arithmetic batches passed 13, 14, 21 and 22 tests respectively. The final batch also audited all 2,560 fixed objective tables in 2.922 s. Every local stage returned verified cleanup; no independent watchdog intervened. The remaining local exact-evidence stage completed in 91.5009 s. The initial full local regression passed 274 tests in 53.44 s; final guard source passed 275 tests with 46 warnings in 53.99 s.

Raw cProfile files/text, per-component counters, all checkpoint radii, source/environment records, supervised status files, original archived failures, wheel/CLI audit and hosted artifacts are retained with this report. No favorable samples were selected from repeated unchanged-source runs. Tail-latency distributions were not collected for the complete verifier, so no p95/p99 or hard-real-time claim is made.
