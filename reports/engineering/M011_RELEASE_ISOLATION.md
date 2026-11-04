# M011 — isolated V1 publication review

This document accompanies a **documentation-only integration candidate**, not a
published release. Its containing commit is the proposed source revision; the
engineering M011 handoff records that exact SHA and fresh CI outcomes. Publication
requires all mandatory checks on that revision and final maintainer approval.

## Exact source and exclusion boundary

Base `86ad99f6956c76a5bb6d169e21544684f57c9270`, M009 reliability-only backport.
Licensed predecessor `c7012fc4d002a9904abbb68a21a554e11e78d570` remains PR#1's older
head; it does not include the M008/M009 correction and should not be mistaken for
this candidate. Local main d5a16da3 and remote main011c3ce1 are preserved.

This candidate has MIT licensing and version1.0.0, the qualified M008/M009
supervisor/fixture correction, original scientific implementation and frozen
numerical evidence. It excludes performance/v1-1-optimization ce147866, optional
style72824e6c and M010fixture follow-up4a8e91ee. No M010failure-worker or optional
production code is imported. Compared with86ad99f6, ONLY README.md, release notes
and this new audit document change. Original scientific reports are immutable.

## Executed baseline audit and exact-candidate gate

The86ad99f6baseline independently passed fresh Linux/macOS package CI41925624286
and legacyLinux41925624531; full local200tests/25warnings; exact91-array and JSON
replay/predictor/controller comparison; four byte-identical numerical outputs and
four figures; actual noneditable-wheel imports/license/version/CLI; ten valid
fresh-root original write_failure invocations. No natural original V1 deadline
assertion failure was observed. All original deadlines/graces remain.

Audit-harness mistakes are retained separately: source-path metadata made an
initial pip invocation skip installation; a wrong working directory correctly
failed a wheel/source comparison; shared artifact roots caused teardown errors
in an initial ten-case bank whose lifecycle assertions passed. They were corrected
outside release source, without replacing an unfavorable source outcome. These
failed attempts are not labelled successful commands or hidden.

The README still had a superseded publication-HOLD reason, so this minimal
status-documentation integration is needed. The baseline's green checks do NOT
qualify the new documentation revision automatically. It receives the same full
local200-test/wheel/replay/evidence checks and fresh Linux/macOS/legacy CI. See
checks on the exact containing commit and final M011 handoff for actual results.
No optional FIR/RLS p95or V1.1 speedup target is silently added to V1's frozen gates.

## Scientific and resource scope

M005B remains a simulation development result: PI11.46875,RLS-MPC13.12921875,
fixed MPC18.9778125Hz·s. Adaptive superiority against PI FAILS. Historical V0.1/V0.2,
M003.1/M003.2 and M005A.5 negative findings remain. No locked or newly reserved
network study, living preparation, plasticity or hard-real-time hardware validation.

Existing negative process controls and variable OS/I/O latency remain limitations.
A worker error/intent marker does not prove actual exit. Deadline checks fail
closed; no universal upper scheduling/fsync bound or physical-suspend guarantee
is established by finite green CI. M010's missing operation opportunity remains
inconclusive on its own optional fixture, not retroactively successful.

## Independent readiness decisions

- V1: eligible for final publication APPROVAL only if the new exact candidate
  satisfies all original gates; final handoff reports the actual decision.
- Personal-style branch: HOLD under its own unresolved declared qualification;
  it is not a prerequisite to reviewing this isolated V1 candidate.
- V1.1 performance candidate: HOLD;2x neural/workflow and30%p95targets were not
  met. This release does not claim those speedups or include its code.

No merge, tag, publication, new scientific acquisition or automatic follow-on
research is authorized. If an unmodified release test fails here, retain V1HOLD;
no old green result, optional-branch result or favorable retry may override it.

## Final M011 exact-revision disposition — V1 HOLD

The required new candidate is `42e20ada6e737c37f616950056c3444cfa99d400`,
branch `release/m011-v1-isolated`. Its full local qualification PASS used the
fresh noneditable 1.0.0 wheel, pinned dependencies, pip check, actual installed
imports/CLI, 200 tests (0 failures/errors/skips; JUnit 44.511 s; 25 warnings),
91 exactly equal arrays and JSON records, four byte-identical numerical artifacts
and four byte-identical figures. Ten original write_failure repetitions passed.
The entire 1200 s qualification finished with 1060.346 s remaining. Reproduction
was from preserved evidence, not new scientific acquisition. Incidental timings
in the functional golden checker do not clear M010 performance gates.

**Mandatory hosted macOS qualification FAILED.** Run41929010204 on this exact
candidate: Linux PASS; macOS199passed/1failed/25warnings in218.93s. Failure:
`tests/test_suspend_clock.py::test_real_workers_after_injected_resume[clock_failure]`,
missing `worker/partial.txt`. Independent legacyLinux41929010497 PASS. The failed
package job skipped subsequent traced repeats and CLI smoke; they are not claimed
as executed on that job. The earlier86ad99f6green run does not substitute.
No favorable retry was requested. Raw logs, both platform artifact ZIPs, hashes
and the failure assessment are preserved under evidence/m011/hosted_final.

The injected API inconsistency occurs after350ms active elapsed, regardless of
worker readiness. Worker entry was93.843ms after deadline creation; imports_begin
94.362ms. No imports_completed, PID record or partial checkpoint was observed.
Supervisor returned CLOCK_FAILURE, verified reaping, worker returncode-15,
0.488752274s active elapsed, no outer watchdog. The assertion presumes checkpoint
publication before fault injection; that opportunity was not established here.
This supports a fixture precondition/race diagnosis, not a demonstrated supervisor
acceptance of late success. Whether import work or scheduling caused the delay is
unresolved; preserved events do not separate those costs. V1 remains HOLD anyway.

Smallest follow-up: prospectively test fault injection after a verified worker
checkpoint/ready handshake, while preserving the same absolute deadline and
cleanup allowances. If readiness is not reached, retain failed/inconclusive
coverage rather than pretending the error path was tested. Keep an independent
pre-ready clock-failure negative control proving fail-closed cleanup. This is a
proposal, not an implemented fix or approval to waive the failed mandatory gate.

## Inventory / preservation / integration decision

| Reference | Revision | Scope / disposition |
|---|---|---|
| local main | d5a16da3 (full inventory.json) | preserved, not publication candidate |
| origin/main | 011c3ce1a71960544032717e91076730416c19fd | preserved |
| release/v1-license-version / PR1 | c7012fc4d002a9904abbb68a21a554e11e78d570 | older, lacks M009 correction |
| M009 reliability baseline | 86ad99f6956c76a5bb6d169e21544684f57c9270 | original scientific V1 |
| release/m011-v1-isolated | 42e20ada6e737c37f616950056c3444cfa99d400 | doc-only integration, HOLD |
| refactor/personal-code-style | 72824e6cb48e714e11a398f2787146099daec397 | optional, HOLD |
| engineering/m010-write-failure-qualification | 4a8e91ee16ed2458c8978783f251bf045e7dbfa5 | historical HOLD preserved |
| performance/v1-1-optimization | ce147866186e8502af343157e4e0d45ac446665a | separate, failed speedup targets |
| engineering/m011-persistence-review | 9fca6f6420d5ddc77c1a7b815913af699544b080 + closing evidence commit | diagnostics only |

Physical source audit checked38056 candidate paths. Only README/release-notes and
new M011 report differ from86ad99f6; all scientific code/evidence remains original.
All43503 starting-M010 tracked paths also independently hash unchanged in the
engineering workspace, including all four style-refactored modules. No production
code or old tests were edited on either review branch. Package MIT/version,
constraints, replay, FIR/ARX/RLS/PI/MPC golden checks pass; historical negative
findings remain unchanged. No tags/releases created; PR1 remains unmerged.

M011 disposition: isolation and local numerical/package verification PASS;
mandatory hosted release qualification FAIL; overall release recommendation HOLD.
Personal-style qualification HOLD and V1.1 performance HOLD remain independent.
Neither can be represented as qualified by the new diagnostic green checks.
The engineering closing commit identifies these appendices; it does not change
the frozen42e20candidate or retrofit its failed CI outcome.

## Commands and recovery of audit evidence

Executed from isolated release worktree (full argument lists/exit records are in
`v1_candidate_42e20.tar.gz`, `status.json` and stage artifacts):

```text
M011_EXPECTED_SOURCE=42e20ada6e737c37f616950056c3444cfa99d400 PYTHONPATH=src /tmp/neuromancer-m011-v1-env/bin/python /Users/adithyaupad/Developer/neuromancer/tools/m011_release_qualify.py /Users/adithyaupad/Developer/neuromancer/reports/engineering/evidence/m011/v1_candidate_42e20
python tools/m011_verify.py isolation /tmp/neuromancer-m011-v1 reports/engineering/evidence/m011/integration_isolation_verification.json
```

The audit harness logs pip/build/install/CLI, functional goldens, evidence-only
reproduction and pytest commands separately. Initial failed86ad99f6harness
attempts are in `v1_qualification.tar.gz`; its original HOLD status is retained.
Both new audit trees are losslessly archived to avoid thousands of duplicate
pytest files. `audit_archive_preservation.json` inventories every file/link and
SHA256; all extracted bytes were verified, and local originals remain under
`/tmp/neuromancer-m011-retained-audit-trees`. Extract into a new scratch directory,
not over historical evidence. No previously committed tree was migrated/deleted.
Hosted ZIPs remain raw, with independent SHA256 and CI metadata. The initial
reference NPZ is deliberately retained even though generic ignore rules exclude
NPZs. The engineering final commit is a report/evidence closure, not a new release
source; any future repaired publication candidate requires fresh exact-head gates.
