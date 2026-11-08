# M005A.1 — resource recovery and PI qualification

**Resource qualification FAIL; mission execution PARTIAL; scientific qualification NOT ESTABLISHED; M005B HOLD.** No new scientific trajectories, PI selection or reserved confirmation were executed. The mandatory resource-control stop condition was triggered by real worker-process evidence. Historical M005A remains PARTIAL.

## Revision and preservation

Starting revision `1332733349cc65b5bbae659fc44f04b4b5999099`, clean branch `research/m005a-closed-loop-foundation`; review branch `research/m005a-1-qualification` created at that revision. The publication commit containing this report is the final review revision (its exact hash accompanies the mission return; a document cannot contain its own Git commit hash).

Audit covered the complete M005A report and frozen protocol009, control/acquisition implementations and tests, resource deviation, original clock evidence, tuning completion records, failure history and verification inventory. [Audit](evidence/m005a_1/audit.json) records SHA256 for all 4,140 starting tracked paths. All 251 entries in the previous evidence inventory matched. Original protocol, report, source, numerical archives, negative findings and failed attempts are unchanged. No historical branch was merged.

## Overrun diagnosis and reuse decision

Corrected historical TUNE has all ten network/noise40 records and 120 completed branches, 4,350 simulated seconds. Prior independent reconstruction remains preserved. The acquisition's elapsed counter reported 2,491.556301083 seconds, while recorded original artifact epochs span 5,089.5899538993835 seconds, above the frozen 3,600-second stage cap. The downstream absolute-time guard blocked scoring and confirmation. The 9,189-second later inspection interval includes idle time and is not acquisition runtime.

The established engineering defect was inconsistent clock semantics between acquisition and downstream qualification. The physical explanation for the large write gap remains unknown; machine sleep is not established. First-attempt floating-point slew failures, the corrected restart and incomplete in-flight durability remain disclosed in M005A.

Completed tuning archives are structurally complete and potentially reusable as development data under an explicit prospective continuation authorization; they cannot retrospectively make the over-budget stage PASS. No incomplete or favorable subset was used. The original stage budget is already exceeded, even though its confirmation allocation of 90 minutes remains unused. A fresh versioned execution authorization must specify whether those complete archives are accepted for selection. This mission does not silently restore the exhausted TUNE allowance.

## Real resource-control qualification

[Executable probe](evidence/m005a_1/resource_probe.py) imports the **unchanged production runner** and replaces only its trial callable with non-neural fixtures. It uses the production spawn executor, polling, resource-stop persistence and termination path. The parent's calendar clock is deliberately advanced after two monotonic seconds to enter the one-hour deadline path without a long experiment. Workers do not receive a simulated neural model. An independent eight-second external watchdog bounds the probe itself.

| Fixture | Observed process runtime | Outcome |
|---|---:|---|
| Cooperative workers, one quick completion and sleeping workers | 2.254156125 s | Parent exits nonzero; partial resource record and progress retained; no complete summary |
| Workers ignoring SIGTERM | 8.006444667 s | Production parent hangs during executor cleanup; external watchdog must SIGKILL the entire fixture process group |
| Restart into existing evidence directory | bounded subprocess | FileExistsError; prior records not overwritten |
| Backward epoch counterexample | analytical injected clock | `check_deadline(100,99)` accepts; elapsed/monotonic deadline is absent |

[Raw results](evidence/m005a_1/probe/result.json) include worker PIDs, exit codes, saved resource records and durations; stdout logs and durable fixture checkpoints are retained. Each timeout saved three worker checkpoints and the one completed result. No timeout produced `summary.json` or exit success. Subsequent process-table inspection found no remaining probe/spawn workers after external cleanup. This demonstrates the failure on actual processes, rather than inferring termination from a unit test. It does not establish that Brian workers normally ignore SIGTERM; the point is that bounded termination is not guaranteed when a worker does.

The production guard uses adjustable `time.time()` only. `perf_counter_ns()` is used for reporting, not a second deadline. A backward wall-clock change can extend execution; monotonic enforcement is therefore unqualified. Parent and workers share an epoch deadline, but independent worker monotonic enforcement is absent. The parent polls every second; worker imports and the full 51-second neural calibration have no internal deadline polling. Final result serialization and executor cleanup can extend past the last check. Worker termination has no bounded join/kill escalation. Branch buffers can be lost on forced termination; fixture checkpoint survival is not proof of neural buffer durability.

The cooperative probe's 2.254-second runtime includes startup, polling, serialization and cleanup around a synthetic two-second expiry trigger. This is a bounded observed overhead measurement, not isolated overhead or a neural-throughput benchmark. The resistant probe establishes a lower bound on the unbounded-cleanup defect. Restart is fail-closed, not resumable: a new directory is required; this prevents overwrite but supplies no validated resume/deduplication semantics.

Requested BLAS thread environment was set to one for the probes and regressions. [NumPy configuration](evidence/m005a_1/blas.txt) records the backend; `threadpoolctl` was unavailable, so actual thread counts remain unverified. No standard single-thread performance claim is made.

**Decision: stop before scientific execution.** The existing guard remains unreliable. No production code was changed: numerical controller/model behavior is therefore unchanged, and no new guard is represented as qualified. Further resource repair belongs to a separately versioned recovery preflight; changing deadline engineering must not change scientific equations or acceptance rules.

## Tests, commands and evidence boundaries

Executed from the repository with `/tmp/neuromancer-m004-venv/bin/python`:

```text
python reports/evidence/m005a_1/resource_probe.py reports/evidence/m005a_1/probe
python -m pytest -q --junitxml=reports/evidence/m005a_1/tests.xml
```

Both commands used `VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`; tests additionally set `MPLCONFIGDIR=/tmp/neuromancer-m005a-mpl`. The fixture command completed its assertions, including the expected guard failure. It is not a passing resource qualification.

**103 regression tests passed, 25 warnings, 36.13 seconds**, with [text](evidence/m005a_1/tests.txt) and [JUnit](evidence/m005a_1/tests.xml) retained. These include original causality, arbitrary feasible transitions, anti-windup/fallback, delayed/missing observations, replay, controller isolation, calibration and network-level gate mathematics. The existing short neural replay test ran only as an instrument regression, not a new scientific acquisition or reserved evaluation. No full tuning numerical rescore was performed after the stop condition; historical independent verification is preserved, not relabeled as a newly executed audit.

No selected PI exists. No reserved noise41/42 was opened. Complete scientific baseline comparisons and exposure histories remain in M005A's immutable descriptive evidence; there are no new confirmation comparisons, confidence intervals or scientific PASS decisions to report. The original target, gain grid, controller equations, selection rule, seeds, neural dynamics and acceptance thresholds are unchanged.

## Minimal versioned continuation proposal — NOT executed

Create a separate recovery protocol before any further scientific acquisition:

1. Retain M005A's resource failure; explicitly accept all 120 corrected tuning branches for selection under the new execution authorization, without changing their numerical outcomes or scientific interpretation. Independently reconstruct every original selection metric, apply the exact frozen global rule, and commit selection before confirmation.
2. Replace calendar-only deadlines with both monotonic elapsed and calendar deadlines, fail when either expires, define suspend behavior explicitly, and retain both clocks in provenance. Check before/after expensive work and before terminal success publication. Use atomic terminal status and durable branch checkpoints.
3. Make parent cancellation bounded: stop queued jobs, terminate, bounded join, kill survivors, bounded final join and verify no live descendants. Test cooperative, resistant and crashing workers, backward/forward clocks, write failure, restart and partial preservation using real processes. Budget parent setup, collection and cleanup within the cap, reserving a prespecified cleanup margin.
4. Keep original confirmation identities41/42, all20 prefixes/160 branches/6,140 simulated seconds, original 90-minute confirmation cap, three-worker maximum, 2GiB worker monitoring and 500MiB evidence ceiling. No replacement, selective resume or gain retuning. Authorize no fresh TUNE neural run unless separately budgeted prospectively.
5. Use the historical internal throughput only as a rough planning estimate: 6,140/4,350 times 2,491.556 is about3,517 seconds, leaving about1,883 seconds within90 minutes. The historical absolute-clock gap makes this estimate insufficient to authorize execution. Establish reliable timing/cleanup first; abort rather than extend if the cap is reached. Retain the original separate20-minute analysis/verification limits and commit gates before confirmation.

This proposal changes only execution provenance and resource qualification. It is not permission to weaken the scientific requirements or reclassify the original run. No selection, confirmation or M005B work follows this report.

## Remaining limitations and next falsifiable test

Highest-priority blocker: real-process cancellation can hang beyond the deadline. Next: missing monotonic enforcement and incomplete in-flight neural persistence. Third: uncertain ability to finish confirmation within90 actual minutes. Actual Accelerate thread count and the historical timestamp-gap cause remain unresolved. Scientific controller efficacy remains unqualified independently of the passing infrastructure tests.

Next falsifiable experiment is a non-neural resource preflight: a resistant worker must be forcibly stopped, all descendants gone, partial records durable and terminal status non-success, within a prospectively fixed deadline plus an explicitly budgeted cleanup interval. Only after that and a committed full-data PI selection may the original reserved scientific confirmation be considered.
