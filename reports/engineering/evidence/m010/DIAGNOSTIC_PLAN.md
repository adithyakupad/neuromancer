# M010 prospective diagnostic and qualification plan

2026-11-04; before fixture changes or new probes. Start72824e6cb48e714e11a398f2787146099daec397,
clean refactor/personal-code-style; engineering/m010-write-failure-qualification.
All historical files are immutable. Production supervisor/clocks and four style
modules remain byte-identical unless an independently demonstrated supervisor
violation requires a separately justified repair. No scientific acquisition.

## Questions and prior evidence

Original run41895058114:199passed/1failed; write_failure still running at work
cutoff, TERM then returncode-15, cleanup verified. Python traceback began but did
not finish; no atexit event. That proves neither prompt exception termination
nor a specific OS/filesystem delay. Later green72824CI does not explain it.
Assess A failure-operation delay, B exception display/shutdown delay, C delayed
parent observation, D unjustified prompt-exit fixture assumption, E supervisor
contract defect. Treat unidentifiable historical subcauses as unidentifiable.

## Fixed diagnostic bank (25 subprocess trials, sequential)

1. Five original untouched write_failure workers first.
2. Five instrumented filesystem errors with uncaught exception display.
3. Three instrumented pure-Python errors without filesystem failure.
4. Three caught filesystem errors, bounded failure record and explicit nonzero exit.
5. Two filesystem errors with controlled1.2s traceback-stage delay.
6. Three normal interpreter-exit controls.
7. Two controlled1.2s delays before filesystem failure operation.
8. Two filesystem failures with controlled1.2s interpreter-shutdown delay.

No replacements or exclusions. All25retained, including unexpected failures.
Unmodified operation/uncaught timings are descriptive; they may end either
WORKER_FAILURE or DEADLINE_EXCEEDED, never a successful trial. Normal controls
must be COMPLETED. Controlled late cases must fail closed. Explicit failure
exit must be nonzero, with evidence of actual ENOTDIR, partial checkpoint,
and first observed exit before cutoff to qualify as a timely failure.
Instrumentation changes exception-display handling and cannot retrospectively
identify the exact syscall or scheduling stall in the old hosted episode.

## Timing and containment

Each trial retains original Deadline.after(1.8), work cutoff end-0.8s, and
cooperative/TERM/reap0.2/0.2/0.4s. Deadline creation remains before launch.
No allowance is enlarged. Diagnostic batch240s absolute suspend-inclusive
clock; outer fixture watchdog6s; owned process-group cleanup on intervention.
One trial at a time; per-process CPU20s/file output16MiB limits, final high-water
RSS<=1GiB check (measurement, not kernel allocation containment). No deliberate
machine load or physical sleep. Stop on watchdog/cleanup failure, persist partials.

Same qualified clock domain in parent and worker. Record entry/imports, operation
begin, exception caught/propagating, hook begin/end, formatting begin/end, stderr
write/flush, atexit begin/end; supervisor poll/cutoff/TERM/reaping/publication.
Record actual process exit separately from intent and report markers.

## Repair gate and prespecified qualification

If supervisor contract is respected and prompt implicit Python failure exit is
not bounded, retain original worker in Git and as diagnostic prior art. Correct
write_failure with a ready/release/failure-report/nonzero-exit fixture, while
still requiring parent-observed actual exit/group cleanup before original cutoff.
The intended filesystem error and surviving checkpoint must be independently
asserted. A separate recorded-failure-but-delayed-exit test must remain DEADLINE_
EXCEEDED; a failure record must never create trial success. No assertion is
relaxed to accept a late exit as a timely failure.

After justified repair:20corrected immediate-failure and5late-failure probes,
fixed in advance, same clocks/budgets and independent watchdog. Add analytical
record/causal assertions; keep all existing cancellation/boundary/group tests.
Full local regressions, exact91-array style golden comparison, preserved-source
hash audit, evidence-only tables/figures reproduction, pinned imports/pip check.
Performance: repeat three ABBA cycles of the same style probe against independent
unchanged source trees,54samples/source/workload, no exclusions; retain existing
<=10%median/<=20%p95 and<=10%peak-RSS regression limits. No performance optimization.
Qualification batch1200s; paired batch600s; installed-wheel checks use remaining
qualification deadline. No resource deadline reset inside a batch.

Hosted Linux/macOS and legacy workflows must pass on final revision, all tests
enabled. Record arm64 runner availability separately from local Apple Silicon
and hosted Intel macOS. No rerun-until-green qualification. If another mandatory
failure appears, preserve it and retain HOLD pending evidence-backed disposition.
No merge, tag, publication, controller/scientific tuning or locked-network access.
