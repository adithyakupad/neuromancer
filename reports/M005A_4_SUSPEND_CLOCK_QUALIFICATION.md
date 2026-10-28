# M005A.4 — Suspend-aware deadline qualification

Date: 2026-10-28. Engineering **PASS within the documented platform-evidence scope**. Controlled physical sleep/resume **NOT RUN**. No neural acquisition, confirmation branches, controller selection or scientific gates were executed. M005A.3 remains PARTIAL; scientific qualification remains NOT ESTABLISHED; M005B remains HOLD.

## Revision and preservation

Starting branch `research/m005a-3-pi-qualification`, exact clean HEAD `e91ac866e21ab88bc028410c402f367fcab98f05`; review branch `research/m005a-4-suspend-clock`. Final revision is the commit containing this report (obtain with `git rev-parse HEAD`; a self-referential commit hash cannot be embedded in its own contents). The final response records that exact hash. No merge or release.

The preservation inventory independently verifies 6,902 historical files unchanged. Four historical engineering files intentionally change: supervisor, acquisition clock plumbing and two engineering test fixtures. Neural dynamics, PI equations, Kp=10/Ki=5, target construction, constraints, protocols and historical evidence are unchanged. The selected controller artifact remains SHA256 `076604e732e1f97d02195c6d3798f0fba1998f4e9605c9492480cf51f794da36`, frozen at revision `604302e9eecc491b8855a6ccbcaf4e195cb2adb2` before confirmation.

## Historical clock diagnosis

The old supervisor compared an absolute Python `time.monotonic_ns()` deadline, backed by `mach_absolute_time()` on this macOS host. Investigation compared elapsed `time.time()` calendar time (CLOCK_REALTIME) with `monotonic`/`perf_counter` elapsed uptime. These are different time domains: calendar time is adjustable and includes sleep; Mach absolute uptime excludes system sleep.

The archived run lasted 542.862513065 seconds by calendar time and 508.844052250 seconds by uptime, both below its 5,400-second cap. The investigation separately recorded a 33.865678995-second discrepancy. The largest sampled calendar-minus-uptime offset step was 34.013493666 seconds. OS logs record clamshell sleep at 00:40:53 and wake at 00:41:32, with rounded timestamps. That interval and the offset step corroborate different suspend semantics. Initial epoch timing was captured after setup, so the raw offset is not an exact sleep-duration estimator.

| Explanation | Evidence-based classification |
|---|---|
| Genuine exceeded suspend-inclusive deadline | Not supported by the recorded durations; neither measured elapsed duration approaches 5,400 seconds. Historical continuous time was not recorded. |
| Different suspend semantics | Primary supported explanation: documented APIs plus temporally matching power log and sampled offset change. |
| Incorrect deadline arithmetic | No observed arithmetic reset/backward uptime. The old active-machine deadline was unsuitable for a suspend-inclusive budget. |
| Clock jump or measurement error | No observed uptime reversal. Minor calendar correction or sampling skew cannot be excluded; the available logs cannot separate these exactly. |

The original stop was correct under its prospectively committed clock-discrepancy rule and remains preserved. It was a manual interruption, recorded as SUPERVISOR_FAILURE/KeyboardInterrupt; three active workers were terminated/reaped in 0.237636375 seconds. It is not retrospectively relabeled successful or over-budget.

## Platform evidence and implementation

Apple documents `mach_continuous_time` as monotonic across system sleep, unlike `mach_absolute_time`. The installed SDK independently declares the API and its macOS 10.12 availability. Conversion uses integer `ticks*numer//denom`; measured timebase is 125/3 ns per tick. Sources accessed 2026-10-28: [Apple Kernel API](https://developer.apple.com/documentation/kernel/1646199-mach_continuous_time), [Apple public header](https://github.com/apple/darwin-xnu/blob/main/osfmk/mach/mach_time.h). Local SDK paths/hashes are in `platform_headers.json`.

An isolated [DriverKit uptime page](https://developer.apple.com/documentation/driverkit/kiotimerclockuptimeraw) gives a conflicting raw-clock mapping. This implementation relies on direct Mach APIs, installed header constants and executed native equivalence measurements, rather than that isolated mapping. CLOCK_MONOTONIC_RAW=4 brackets continuous time on this SDK; CLOCK_UPTIME_RAW=8 corresponds to absolute uptime in the native probe.

Added `neuromancer.clocks` behind the supervisor interface. A read brackets `clock_gettime_nsec_np(4)` with direct Mach continuous reads, checks quantization-aware agreement and nondecreasing elapsed clocks, and permits expected growth in continuous-minus-uptime offset. A missing API, invalid timebase, missing boot identity or inconsistency quarantines the clock and fails closed. Wall time is diagnostic only. This checks kernel API consistency, not an independent oscillator or all common-mode kernel faults.

Deadlines require an integer end and a boot-scoped clock ID; foreign boots, legacy bare uptime deadlines and mismatched worker environments reject. Nested acquisition inherits the exact qualified deadline and cannot reset the budget. Work and terminal publication use the qualified clock. Performance metadata labels uptime-based worker measurements separately.

During physical sleep user-space cannot signal workers. On the first scheduled check after resume, the original end remains authoritative: expired work cannot resume or succeed. Normal cleanup reserves .2 seconds cooperative, .2 TERM and .4 final cleanup inside the budget. Expiry during suspension skips cooperative grace and immediately requests TERM; a separately labeled at-most .8-second cleanup-only allowance after detection permits KILL/reaping and failure persistence. This is not extra scientific execution time. Clock failure uses labeled uptime solely for bounded emergency cleanup, with untrusted experiment timestamps null. Failure to verify process absence remains CLEANUP_FAILURE. Publication-time expiry or clock failure cannot leave a successful terminal record.

Detailed contract: `docs/architecture/006_SUSPEND_AWARE_DEADLINES.md`. Linux CLOCK_BOOTTIME support follows [kernel documentation](https://kernel.org/doc/html/next/core-api/timekeeping.html) but was not locally qualified. POSIX group ownership does not contain deliberately detached hostile descendants or guarantee interruption of uninterruptible kernel operations.

## Executed verification

Environment: macOS 26.5.2 arm64, Python 3.12.15, Brian2 2.10.1, NumPy 2.5.4. Thread-count environment variables were set for tests; no claim of verified standardized BLAS thread behavior is made. No system power or calendar-clock setting was changed.

1. Native C probe compiled with Xcode clang: 20 uninterrupted samples comparing Mach APIs with raw-clock APIs. Python probe: 1,000 native samples plus a fresh child sharing the same boot clock domain. Measured Python clock-read median 2,042 ns, p95 2,625 ns, maximum 785,625 ns in that bounded sample. These are actual local measurements, not throughput forecasts. Process sleeps in probes are not system suspension.
2. Final non-neural regression command:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/neuromancer-m005a-mpl /tmp/neuromancer-m004-venv/bin/python -m pytest -q --ignore=tests/test_substrate.py -k 'not neural_tick_replay_isolation_and_receipts and not origin_checkpoint_replay_and_receipt_timing' --basetemp=reports/evidence/m005a_4/verified_trials --junitxml=reports/evidence/m005a_4/verified_tests.xml
```

Result: **104 passed, 2 deselected in 28.84 seconds**. The substrate suite and two fixtures that advance neural dynamics were deliberately excluded to honor this mission's no-neural-experiment boundary; this is not a claim of a newly executed full neural regression suite. Earlier engineering runs and raw fixtures are retained.

Tests cover normal completion, exceptions/unexpected exit, shutdown blocking, ignoring cooperative/TERM requests, actual KILL escalation, spawned descendants, partial writes/write failures, boundary races, deadline and boot-domain rejection, inherited budget, wall-clock adjustments, injected suspend/expiry, resume cancellation, latched API failure and final-publication failures. Real synthetic worker tests have independent outer watchdogs. Deterministic clock injection simulates suspension; it does not establish physical suspend behavior. Saved resume cases verify cancellation within 100 ms of the first injected resume check, not a hardware real-time wake guarantee. Partial checkpoint text survives; repeat cleanup of gone groups is harmless.

3. Independent archive verification commands:

```sh
/tmp/neuromancer-m004-venv/bin/python reports/evidence/m005a_4/audit_confirmation.py reports/evidence/m005a_3
/tmp/neuromancer-m004-venv/bin/python reports/evidence/m005a_4/verify_engineering.py
```

Historical audit took 12.011741333 seconds. Engineering verifier independently read 20 saved real-process records, verified reaped parents/group absence and non-success after expiry/failure. Expected statuses: 2 COMPLETED, 11 DEADLINE_EXCEEDED, 4 WORKER_FAILURE, 1 CLOCK_FAILURE, 1 SUPERVISOR_FAILURE and 1 deliberately injected CLEANUP_FAILURE. These injected failures are successful test outcomes, not failed scientific trials. An initial verifier draft incorrectly compared emergency uptime cleanup with continuous deadline values; it rejected that comparison and was corrected to compare only matching clock domains before the passing verification. No supervisor failure was hidden.

**Controlled physical suspend/resume was not feasible with assured machine ownership and independent wake/watchdog control, so it was not attempted.** Engineering PASS rests on authoritative platform semantics, executed native compatibility checks, deterministic boundary tests and real process cleanup. It does not assert an executed physical-sleep test.

## Historical confirmation integrity

The independent audit reconstructs recorded spike counts, causal rate statistics, calibration, PI decisions, current/slew/exposure accounting and 120 numerical metric rows. It validates 27 archive hashes, all 83 matched noise block hashes per branch with selected blocks regenerated, fixed network parameters, disjoint channel membership, exact timestamps, STATIC/LOSS agreement before change and ZERO agreement throughout. Source hashes match the historical acquisition revision rather than today's engineering changes. All 119 files in the M005A.3 inventory remain intact. No neural trajectory was advanced; this is archive analysis and deterministic random-array regeneration, not a cold neural replay.

| Network | Noise | Prefixes / branches | Classification |
|---:|---:|---:|---|
| 0 | 41 | 1 / 8 | REUSABLE, subject to prospective continuation amendment |
| 0 | 42 | 1 / 8 | REUSABLE, subject to prospective continuation amendment |
| 1 | 41 | 1 / 8 | REUSABLE, subject to prospective continuation amendment |

All outcomes, including unfavorable ones, remain in the evidence. Total complete evidence is 921 simulated seconds, 46,050 observation bins, three prefixes and 24 branches. No complete artifact exists for interrupted pairs (1,42), (2,41), (2,42); their in-flight unflushed computation cannot be recovered or inferred. Networks 3–9 × noise41,42 were not started. Missing: **17 trials, 136 branches**. No subset confidence interval or 8/10 gate substitutes for the missing cohort.

## Continuation decision and limitations

The original amendment010 required stop/HOLD on clock discrepancy and prohibited scientific retry. It does not authorize automatic restart. A separately committed prospective amendment is required before any acquisition: explicitly accept the three audited complete trials, enumerate exactly the 17 missing pairs, retain the frozen PI10/5, seeds, all scientific definitions and thresholds, and declare a new execution budget/clock/cleanup contract. Original resource failure and stop remain immutable. This report does not authorize or run that continuation and does not extend the old deadline.

Engineering decision: **PASS for the scoped suspend-aware supervisor implementation**; physical-sleep execution evidence remains absent. Scientific decision: **NOT EVALUATED in M005A.4**; M005A.3 remains PARTIAL and M005B HOLD. Next falsifiable step is a prospective continuation amendment followed by the original missing confirmation trials under the qualified deadline contract, not new target engineering or adaptive control.

Evidence directory: `reports/evidence/m005a_4`; native sources/headers, historical reconstruction, saved process terminal records, test XML/logs, preservation hashes, independent numerical outputs and final verification inventory are retained. No locked network was opened.
