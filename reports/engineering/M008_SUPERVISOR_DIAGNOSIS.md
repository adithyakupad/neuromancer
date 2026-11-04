# M008 — supervisor timing failure diagnosis and qualification

2026-11-04. **Case B: an invalid fixture scheduling assumption, not evidence justifying a
relaxed supervisor deadline.** Engineering qualification PASS on source6e152bce after local and hosted independent
verification. Closing documentation/evidence revision must also pass exact-head CI; its
revision/check IDs are in the mission handoff. No merge,tag,publish,scientific acquisition or performance optimization follows.

## Source and preservation

Started clean at `ce147866186e8502af343157e4e0d45ac446665a`, branch
performance/v1-1-optimization. Review branch engineering/m008-supervisor-diagnosis.
Prospective plan committed `db454102`; original-source repeats precede all instrumentation.
Tracing/classification freeze `fe8f6f3c`; fixture correction `16602cb4`; provenance repair
`5cade4d0`; first full qualification `ba4d3be9`; CI parent-directory repair `12366a2c`.
The implementation/report commit is the commit containing this report; its exact final
hash and final hosted checks are supplied in the handoff (self-referential hashes cannot
be embedded in their own commits).

Independent content verification checks all35,906starting tracked paths, including symlink
contents.35,900are unchanged; six authorized engineering paths evolve:supervisor,two
supervisor fixtures,two workflows,and the historical-workflow lookup in test_calibration.
All neural equations,dt,noise streams,memberships,stimulation/observation contracts,FIR/RLS,
PI/MPC,dependencies,scientific protocols/cohorts,source snapshots,numerical archives and
historical reports remain unchanged. Original supervisor/test/worker source archived in M008.
No locked or validation network was opened. Existing neural regressions are verification,
not new scientific acquisition. Adaptive losing to PI and all earlier negative results stand.

## Historical failure and the contract

Historical final candidate f79538f1,macOS run41788028586:198passed,1failed,25warnings.
The old before fixture intended to finish near800ms after deadline creation. Work cutoff
was1000ms,global deadline1800ms,with200/200/400ms cleanup allowances reserved inside it.
It expected COMPLETED after sleep without verifying a bounded wake,interpreter exit or
parent observation delay. Those operations have no guaranteed200ms upper bound.

The old CI saved neither returned.json nor worker/supervisor timestamps,so the exact
historical event order cannot be recovered. The observed DEADLINE_EXCEEDED alone cannot
distinguish work-cutoff failure from final-publication deadline expiry. It is not retrospectively
relabelled PASS. Worker completion intent is not process termination; even an atexit callback
precedes final interpreter teardown. Success requires observed exit/group cleanup before the
work cutoff and successful publication before the original global deadline.

Python's primary [sleep documentation](https://docs.python.org/3.12/library/time.html#time.sleep)
permits additional scheduling delay; [Popen.poll documentation](https://docs.python.org/3.12/library/subprocess.html#subprocess.Popen.poll)
describes observing process termination. Neither supplies the fixture's assumed upper bound.
Accessed2026-11-04. No alternate clock or late-success policy is introduced.

## Fixed experimental design and executed evidence

[Prospective plan](evidence/m008/INVESTIGATION_PLAN.md):20unchanged local repeats first;
20instrumented ordinary repeats,3immediate controls,3each of four prespecified delays;
20corrected handshake repeats; deterministic boundaries; full regressions/platform CI.
No trial replacement or exclusion. Batch budgets900s; individual original deadlines1.8s,
external fixture watchdog6s,and diagnostic-driver outer watchdog12s. Diagnostic drivers
have CPU20s/file-size16MiB limits and1GiB completion-RSS checks. Memory is a high-water
check,not a kernel allocation limit. At most one diagnostic trial runs at a time. No physical
sleep/resume or artificial machine load was induced. Original source/seedless manifests and
all per-trial outputs are retained. Repeated process trials are not neural/network samples.

| Local series | Count | Result |
|---|---:|---|
| Original untouched fixture |20|20COMPLETED; no watchdog|
| Traced ordinary original-before behavior |20|20COMPLETED|
| Traced immediate controls |3|3COMPLETED|
| .30s extra worker wake delay |3|3DEADLINE_EXCEEDED; cleanup verified|
| .30s parent-poll stall after completion marker |3|3DEADLINE_EXCEEDED; cleanup verified|
|1.05s pre-import delay |3|3DEADLINE_EXCEEDED; cleanup verified|
|1.05s progress-persistence delay |3|3DEADLINE_EXCEEDED; cleanup verified|
| Corrected handshake |20|20COMPLETED; actual exit/group reaping before cutoff|

Original observed-reaping margin165.896–192.313ms,median180.654ms. Instrumented ordinary
exit-observation margin162.425–189.841ms,median182.502ms. Corrected handshake observed-exit
margin956.819–973.416ms,median967.909ms. These are finite responsive-host observations,
not guarantees that arbitrary scheduling stalls can never recur.

Local ordinary instrumented medians:startup18.405ms,package import27.785ms,sleep-envelope
overshoot5.080ms,atexit-to-observation upper envelope12.489ms. Largest progress-write
1.196ms,terminal publication envelope3.024ms. Parent-delay cases had atexit-to-observation
median314.057ms. Persistence-delay maximum progress envelope1055.757ms. All timing rows,
medians,p95/min/max and bounds are in independent JSON/CSV outputs,not inferred from reports.

### Natural macOS reproduction during hosted qualification

Corrected-source qualification run41793325255 also ran the unchanged-before *behavior*
with opt-in tracing as a diagnostic,not an unconditional-success test. macOS ordinary20:
18COMPLETED,2DEADLINE_EXCEEDED. Linux ordinary20:20COMPLETED. Every delayed condition
failed closed on both platforms; all35trials/platform were retained and cleaned up.
There was no replacement of the two unfavorable macOS observations.

Both natural failures,relative to their own qualified-clock deadline creation:

| Event (ms) | macOS trial11 | macOS trial17 |
|---|---:|---:|
| Earliest qualified worker entry |76.940|70.028|
| Package imports completed |167.349|148.344|
| Intended sleep target |800.000|800.000|
| Wake observed |948.719|946.800|
| Completion intent |949.325|947.716|
| atexit marker |950.605|949.048|
| Last poll returning running (result timestamp) |962.490|961.175|
| Original work cutoff |1000.000|1000.000|
| First supervisor-observed exit |1010.105|1050.697|
| Final terminal publication envelope end |1071.956|1083.218|
| Global deadline |1800.000|1800.000|

Both returned code0,overallDEADLINE_EXCEEDED,and verified cleanup. The parent correctly did
not turn late observation into success. Markers around950ms did not prove an exited process:
a subsequent poll still returned running. Exact kernel exit lies within the poll envelope;
its time relative to1000ms is not known. These traces directly demonstrate the insufficient
margin mechanism without proving which delay caused the original uninstrumented failure.
Instrumentation contributes overhead,so this is not a claim of bit-identical timing behavior.

macOS ordinary sleep-envelope p95=147.662ms;Linux=.221ms. These different hosted machines,
Python builds and loads are confounded:do not infer a macOS clock defect or causal OS effect.
No native clock-domain mismatch/backward reading was observed. Source hashes,OS,Python,
clock identities and all raw records are in platform artifacts/manifests.

## Hypothesis audit

| Hypothesis | Evidence and conclusion |
|---|---|
| H1 oversleep | Nonzero local envelopes;~147–149ms late wakes in natural hosted cases; .30s injection crosses cutoff. Supports a contributor in new reproductions,not exact historical attribution. |
| H2 late observation | Natural running-poll/exit-observation envelopes cross cutoff; controlled parent stall yields failure; deterministic known-exit/late-delivery test rejects success. Actual historical/kernel-exit timing remains unknown. |
| H3 startup/import/exit/persistence | All recorded; controlled1.05s import/persistence delays reproduce failure. Natural atexit followed by a running poll demonstrates teardown is not finished at the marker. No universal latency bound established. |
| H4 wrong supervisor classification | No violation in deterministic before/exact/after/late-observation/publication cases,real traces or both platform checks. No decision-rule repair justified. |
| H5 invalid success-fixture margin | Demonstrated. The fixture expected an upper scheduling bound neither Python nor the OS promises; hosted natural traces exhausted that margin while supervisor correctly failed closed. |
| H6 macOS clock/scheduling discrepancy | Same qualified domains and valid native readings; no clock fault observed. Greater hosted wake envelopes are descriptive,not isolated causal OS evidence. |

Classification **Case B** is scoped to the established fixture assumption defect. It does
not falsely identify the exact lost historical H1/H2/H3 event,or classify unexplained timing
as harmless. The original failure and stop decisions remain valid historical evidence.

## Instrumentation and justified correction

`supervise(...,trace=True)` adds opt-in in-memory lifecycle tracing and structured lifecycle.json.
Default false adds no diagnostic clock reads/files. Deadline representation,comparisons,
cleanup grace,reservation,signals,process-group ownership,waitpid/reaping,late-publication
checks and fail-closed return policy remain unchanged. Both trace-disabled/enabled forms
are tested at deterministic boundaries. Scientific call sites continue using default behavior.

Records cover start,work/global cutoffs,process creation,pre/post polling,first observed exit,
progress persistence,state changes,cleanup,TERM/KILL,reaping and terminal publication.
All trace records carry clock identity,integer ns and signed remaining time. Worker bootstrap
loads the exact qualified stdlib-only clock adapter before eager package imports,then records
imports,sleep/wake,intent,completion record and atexit. No global wall-clock replacement.
Actual kernel exit is interval-censored:the conservative lower bound uses the preceding
poll-BEGIN,not a later None-result timestamp. Earlier analysis outputs are preserved; final
v2 independent outputs apply that refinement. Sleep/terminal envelopes include instrumentation
work and are not isolated kernel-wakeup/fsync estimates. Raw qualified timestamps remain intact.

The before-success fixture now uses a lightweight ready/release/exit handshake and exits
immediately after release. It does not sleep toward the cutoff or need NumPy/package import.
The original before worker remains available/archived,and a separate real race case remains.
Deadlines1.8s/.8s cleanup,6s watchdog,<4s elapsed,COMPLETED,partial-output survival,parent/
descendant cleanup and reaping assertions are unchanged. New assertions require ordered
ready/release/intent/atexit and *observed* exit/group reaping before cutoff. A ready or
completion record cannot qualify success. Package-import behavior is still exercised by
other original worker cases and all diagnostic ordinary/import-delay probes.

The independent process check selects the same recorded PIDs instead of a whole-machine
table,keeping absence/zombie assertions and adding query error/timeout checks. This prevents
pytest from exposing unrelated process entries on assertion failure. No check is skipped.

## Failure-artifact preservation and cleanup verification

A fixture finalizer copies scoped test evidence on both pass and failure. A deliberately
failed nested pytest case independently proves finalizer retention after assertion failure.
Retained:returned/progress/terminal,lifecycle/worker events,PID/PGID,logs,handshake records,
watchdog status,clock/deadline/source/environment metadata and only owned process snapshots.
CI always uploads those snapshots plus raw pytest temporary fixtures,Junit,diagnostic trials,
wheel and smoke output. Both workflows explicitly create the parent runs directory.

Each qualified platform's full suite preserves20real supervisor outcomes:
2COMPLETED,11DEADLINE_EXCEEDED,4WORKER_FAILURE,1CLOCK_FAILURE,1SUPERVISOR_FAILURE and
1deliberately injected unprovableCLEANUP_FAILURE. That injected failure remains a failure
record,not successful cleanup. Independent checks found zero *unexpected* cleanup failures,
verified real descendant/orphan cleanup,and all58scope-finalizer snapshots reported passing
tests with no recorded owned PIDs left in the process table. No outer watchdog intervened.
Fake-process boundary records and nested assertion-failure sentinels are explicitly separate.

## Executed verification and honest repair history

1. Unchanged original20repeat stage:source hashes captured before edits.
2. Focused clocks/supervisor/boundaries:56passed,17.74s.
3. Final deterministic boundary/retention tests:17passed,.21s.
4. Corrected handshake20repeat stage:20passed,5.506s batch wall.
5. First full attempt:215passed,1failed,25warnings,40.67s. Historical M002.3 hash gate
   correctly rejected the edited live CI workflow. Exact original Git bytes archived as
   CI_M002_3_SNAPSHOT.yml;only that historical lookup changes. Expected original SHA256
   19d7133d22a800d812bfe3f0c3858e072a050366da52cb9e34be86529f2396e5 unchanged.
6. Repaired full suite216passed,25warnings,40.50s. After owned-PID inspection refinement,
   final local suite216passed,25warnings,40.05s. No skips or suppressed cases/warnings.
7. First hosted ba4d3be9 attempt failed setup because runs/ was absent before basetemp
   creation:legacy151passed/65errors/45.13s;matrixLinux151passed/65errors/57.53s,
   macOS151passed/65errors/54.23s. All logs preserved. Add mkdir -p runs,not retries until green.
8. Source12366a2c hosted qualification:matrix41793325255PASS,legacy41793325253PASS.
   Linux216passed/25warnings,JUnit89.014s;macOS216passed/25warnings,JUnit95.663s.
   All35diagnostic records/platform independently verified,including2natural macOS deadline
   outcomes. Complete artifacts preserved as ci_123_linux.tar.gz and ci_123_macos.tar.gz,
   with original artifact IDs/digests and portable per-file manifests. No earlier green run
   substitutes for the final source check. Final-head exact checks are recorded in handoff.

Deterministic coverage:well before,exactly at,immediately after cutoff;known early exit with
late observation;exit between work/global deadlines;running at cutoff;TERM/KILL;reaped leader
with live descendant;terminal/trace-write failure;clock discontinuity;publication expiry.
Real tests separately exercise actual process startup,cooperative stop,resistant workers,
children/orphans,exceptions,partial writes,clock/resume injection and process-table absence.
Mocked clocks do not establish physical suspend behavior; no such test was attempted.

Commands (use fresh outputs; do not overwrite curated evidence):

```text
# Original only:checkout db454102; runner rejects later modified-source mislabelling.
PYTHONPATH=src python tools/m008_original_repeats.py FRESH_ORIGINAL
PYTHONPATH=src python tools/m008_traced_repeats.py FRESH_TRACED
PYTHONPATH=src python tools/m008_handshake_repeats.py FRESH_HANDSHAKE
NEUROMANCER_TEST_ARTIFACTS=FRESH_ARTIFACTS M008_WORKER_TRACE=1 PYTHONPATH=src python benchmarks/qualify.py FRESH_SUPERVISION python -m pytest -q --basetemp=FRESH_EXISTING_PARENT/tmp --junitxml=FRESH_TESTS.xml
python tools/m008_verify.py --output FRESH_LOCAL_VERIFY.json
python tools/m008_verify.py --traced RESTORED/runs/m008-traced --output FRESH_PLATFORM_VERIFY.json
python tools/m008_verify.py --fixtures RESTORED/runs/pytest-tmp --output FRESH_FIXTURE_VERIFY.json
```

Actual executable:/tmp/neuromancer-m007-20261101/bin/python,Python3.12.15/macOS26.5.2/arm64.
Pinned numerical dependencies unchanged. Raw command arrays,Junit and logs provide actual
executions; generic fresh-path commands above are reproducibility templates. Reports remain
honest about initial verifier interval-bound refinement and missing old historical artifacts.

## Decision and residual risks

The corrected fixture and unchanged deadline decisions are locally qualified,with successful
hosted source12366a2c qualification and independent raw-artifact verification. **M008 engineering PASS on implementation6e152bce: final-source
Linux/macOS matrix41795885780 and legacy41795885783 both PASS.** The
closing handoff supplies that definitive result/revision. No lost historical timestamps are
invented. No successful process result is accepted after cutoff because it intended to finish early.

Finite repetitions do not bound arbitrary OS stalls. Python supervision is not hard real-time;
process creation/kernel/filesystem responsiveness and trusted POSIX group containment remain
assumptions. Escaped/detached/uninterruptible processes,Windows,physical suspend execution and
biological hardware are unqualified. Long-duration opt-in tracing has not been benchmarked;
normal scientific use keeps it off. Actual kernel exit times are bounds,not exact trace samples.

Once final M008 gates pass,the common fixture reliability blocker is resolved on this review
branch. V1 and V1.1 publication still require reviewed integration into their respective
release candidates,exact-source CI,and maintainer authorization. No branch is merged here.
V1.1's2x/30% performance targets remain unmet;all scientific failures/limitations remain.
Stop after M008. Next step is review/integration qualification,not performance optimization,
controller tuning,scientific acquisition,M006 or hardware work.

### Hosted artifact restoration

```text
mkdir -p /tmp/M008-RESTORE
# Run from repository root; restore each host to its original archive root directory.
tar -xzf reports/engineering/evidence/m008/ci_123_macos.tar.gz -C /tmp/M008-RESTORE
python tools/m008_verify.py --traced /tmp/M008-RESTORE/v1-qualification-macos-latest/runs/m008-traced --output /tmp/M008-RESTORE/MAC-VERIFY.json
python tools/m008_verify.py --fixtures /tmp/M008-RESTORE/v1-qualification-macos-latest/runs/pytest-tmp --output /tmp/M008-RESTORE/MAC-FIXTURES.json
```

Portable archive hashes and per-file content manifests are retained. The stored GitHub ZIP
digest metadata identifies the upstream artifacts; it is not compared to the differently
formatted local tar.gz hash. Pytest alias directories/copies are not additional trials.
All natural failures are included. This reproduces evidence verification,not a claim of
repeating the same OS scheduling history.

## Closing source qualification

Exact implementation/report source `6e152bce7756a6b1a9286c243152c291bbf8f631`:
[Linux/macOS matrix41795885780](https://github.com/adithyakupad/neuromancer/actions/runs/41795885780)
PASS;[legacy41795885783](https://github.com/adithyakupad/neuromancer/actions/runs/41795885783)PASS.
Linux216passed/25warnings/72.68s;macOS216passed/25warnings/82.88s. All35diagnostic records
per platform independently passed timing/classification verification. Full fixture audit
again verifies20real supervisor records,58finalizer snapshots,zero unexpected cleanup
failures or watchdog interventions. The deliberately injected cleanup-failure record
remains explicit. Complete closing artifacts preserved as ci_6e_linux.tar.gz and
ci_6e_macos.tar.gz; initial qualification artifacts and failures remain separate.

The closing evidence-only commit changes no package,test,clock,workflow or diagnostic
execution source. Its exact-head Linux/macOS checks must also pass; the final handoff
records them,not a substitution of the earlier green run. Publication still requires
reviewed integration and release-candidate CI; no merge/tag/publish is performed in M008.

Closing-source diagnostic ordinary cohorts remained macOS18COMPLETED/2DEADLINE_EXCEEDED,
Linux20COMPLETED. These are retained diagnostic outcomes,not unexpected failures of the
corrected handshake success test. All controlled delay outcomes stayed non-success. Both
platforms' independent final timing and cleanup verifications PASS. The closing per-file
source continuity manifest proves no executable/test/workflow changes after6e152bce.
