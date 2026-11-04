# M005A.2 — reliable process supervision

**Engineering qualification PASS for the tested POSIX/active-machine contract; scientific qualification unchanged; M005B HOLD.** No scientific controller experiment, PI selection, reserved confirmation or locked cohort was executed.

## Revision and preservation

Starting clean branch `research/m005a-1-qualification`, HEAD `6077ba50fc05a140fa6bdfc21fe2f6e6a859e7d0`. Review branch `research/m005a-2-resource-supervisor`. The final publication revision is supplied in the mission return; this report is part of that commit.

Audited M005A and M005A.1 reports, frozen protocol009, resource failures/clock evidence, supervisor ownership/deadline paths and tests. All historical scientific protocols, reports, archives and negative results remain unchanged. The sole modified previously tracked path is `src/neuromancer/control_experiment.py`, for execution plumbing and atomic publication only. New code uses Python's standard library; no dependency or scientific parameter change.

## Exact failure mechanisms

The former executor sent termination only to direct worker processes and then entered an unbounded executor shutdown wait. SIGTERM-resistant children could prevent return; descendants had no explicitly owned cleanup group. The earlier resource clock used adjustable calendar time without monotonic enforcement. Completed worker flags could not establish resource qualification. Historical elapsed/calendar mismatch is preserved; its underlying physical cause remains unknown.

## Implementation

[Supervisor](../src/neuromancer/supervisor.py) replaces the executor path with explicitly owned POSIX process groups, lifecycle/exit records, a caller-owned absolute monotonic deadline, bounded stop-file cancellation, TERM, KILL and nonblocking reaping. Default `.2/.2/.4s` cleanup windows are **reserved within** the original budget. Work stops `.8s` before the hard deadline, not after it. Nested calls use the same deadline; queued work cannot acquire a fresh allowance. Calendar time is recorded only for provenance.

[Design and state diagram](../docs/architecture/005_RESOURCE_SUPERVISOR.md) specify all states, terminal causes, containment assumptions, deadline semantics, restart and persistence. The acquisition CLI passes the exact deadline to each fresh interpreter; imports/calibration cannot bypass parent enforcement. It fails closed on any supervisor failure. Legacy `check_deadline` remains only for immutable historical unit fixtures; production acquisition no longer calls it. Scientific equations, schedules, cohorts, PI grid and acceptance rules are untouched.

Atomic JSON/NPZ publication preserves completed artifacts on interrupted replacement. Failed writes retain partial `.tmp` files and cannot return success. In-memory samples at a forced kill are not guaranteed; this is explicitly not sample-by-sample journaling. Existing output directories reject restart. Every worker result retains PID/PGID, state timestamps, exit status, failure cause and log; the supervisor retains progress even if later work fails. Terminal-write failure also emits a failure record to stderr.

## Failure-injection coverage

All real worker fixtures are bounded by an independent six-second watchdog. Their own work budget is1.8s with .8s reserved cleanup. The progress-write failure fixture uses2s. The outer watchdog addresses recorded worker groups separately from the supervisor group; no unbounded resistant fixture is used.

Covered: normal completion; deadline overrun; ignored cancellation; ignored SIGTERM; blocked shutdown; Python exception; abrupt exit17; child/grandchild process-group cleanup; partial checkpoint survival; worker artifact failure; parent progress/final-artifact failure; completion before cutoff; race at cutoff; multiple workers with queued jobs; unchanged nested deadline; backward calendar mutation; exclusive restart; atomic NPZ replacement; acquisition failure integration without neural acquisition; explicit CLEANUP_FAILURE under injected unprovable group cleanup.

Initial restricted-sandbox tests reached their cleanup checks but lacked permission to run `ps`:13 failed/2 passed. Their logs are retained. A permitted run then exposed an orphan-group PermissionError during cleanup:14 passed/1 failed. The code was repaired to retain this as unproven cleanup instead of throwing again from emergency cleanup. Intermediate18-,122- and124-test successes are retained as engineering development records; the final release run and independent reconstruction are authoritative.

## Final executed evidence

**125 tests passed, 25 existing warnings, 53.61 seconds.** This is the original103 regressions plus22 supervisor/integration tests. [Final log](evidence/m005a_2/final_release_tests.txt), [JUnit](evidence/m005a_2/final_release_tests.xml), [raw trials](evidence/m005a_2/final_release_trials) and [independent verification](evidence/m005a_2/verification.json) are preserved. Historical short replay fixtures ran as regressions; no TUNE/CONFIRM scientific stage ran.

Independent reconstruction checked16 returned process records, ordered lifecycle timestamps, shared child deadlines, queued-job states, correct non-success on timeout and completion before the work cutoff. It imports no supervisor implementation. A final process-table inspection found **no live fixture workers or descendants and no fixture zombies**. Source hashes and platform/clock identity are in the verification record.

| Synthetic condition | Supervisor status | Elapsed seconds | Hard-deadline margin seconds |
|---|---|---:|---:|
| injected unprovable cleanup | CLEANUP_FAILURE | 1.782191 | 0.017805 |
| two active / three queued | DEADLINE_EXCEEDED | 1.424506 | 0.375414 |
| before | COMPLETED | 0.822810 | 0.977148 |
| complete | COMPLETED | 0.052423 | 1.747539 |
| cooperative | DEADLINE_EXCEEDED | 1.023688 | 0.776276 |
| descendant | DEADLINE_EXCEEDED | 1.225206 | 0.574759 |
| exception | WORKER_FAILURE | 0.054374 | 1.745590 |
| ignore_stop | DEADLINE_EXCEEDED | 1.225311 | 0.574651 |
| ignore_term | DEADLINE_EXCEEDED | 1.425623 | 0.374340 |
| orphan | WORKER_FAILURE | 0.516843 | 1.283120 |
| race | DEADLINE_EXCEEDED | 1.027386 | 0.772580 |
| shutdown_block | DEADLINE_EXCEEDED | 1.424502 | 0.375462 |
| timeout | DEADLINE_EXCEEDED | 1.225932 | 0.574026 |
| unexpected | WORKER_FAILURE | 0.041424 | 1.758536 |
| write_failure | WORKER_FAILURE | 0.051682 | 1.748278 |
| parent progress-write failure | SUPERVISOR_FAILURE | 0.429246 | 1.570749 |

All final records finished before their original hard deadline; no outer watchdog intervened. Termination-resistant and shutdown-blocked workers reached KILLING then REAPED. Group cleanup was checked independently from direct-parent cleanup. The deliberately unprovable-cleanup fixture returned CLEANUP_FAILURE, retained the deadline cause and correctly reaped its real direct child. This is an expected injected failure, not a successful trial. The real orphan fixture was cleaned in this final run; earlier transient permission/unreaped-group evidence remains retained.

Independent checking initially detected duplicate pytest alias symlinks (not duplicate trials); aliases were removed without deleting trial data. A subsequent check found that the deliberately unprovable-cleanup case could finish slightly past the exact deadline because it consumed the full reaping allowance before terminal publication. The final implementation reserves20ms for publication inside the existing .4s final interval. Its complete regression suite was rerun and the independent checks then passed. Earlier release records and their logs are retained; they are not the final qualification dataset.

## Commands and scope

```text
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/neuromancer-m005a-mpl /tmp/neuromancer-m004-venv/bin/python -m pytest -q --basetemp=reports/evidence/m005a_2/final_release_trials --junitxml=reports/evidence/m005a_2/final_release_tests.xml
/tmp/neuromancer-m004-venv/bin/python reports/evidence/m005a_2/verify.py
```

Test stdout/stderr was redirected to the final log. Process-table assertions required execution permission outside the restricted process-inspection sandbox. Do not rerun pytest with the same basetemp over committed evidence; use a fresh output directory. Requested BLAS thread settings are recorded, not a measured thread-count guarantee. No neural-throughput or standardized BLAS benchmark is claimed.

## Decision and limitations

Engineering execution PASS for the tested contract: bounded cooperative/TERM/KILL cleanup, monotonic global-budget inheritance, explicit failure classifications, independent descendant verification and preserved partial artifacts. A failure remains a failure even if a child exits zero after work cutoff. Historical M005A PARTIAL and M005A.1 resource failure remain unchanged; no PI has been selected and scientific stationary/recovery qualification remains NOT ESTABLISHED. **M005B HOLD.**

Limits: POSIX trusted process groups only; detached/escaped descendants are unsupported. Linux and Windows were not executed locally; CI has not run remotely. Non-child orphan reaping depends on the OS and unproven cleanup fails conservatively. Suspend-inclusive calendar time, machine-wide scheduling stalls and uninterruptible filesystem/kernel operations are not qualified. Python supervision is not hard real-time; terminal records and independent watchdog evidence bound the tested responsive-OS behavior. Fully published checkpoints survive, but killed in-memory buffers do not. No resumption protocol or scientific resource-budget amendment was executed.

Next engineering test: qualify the same failure bank on the intended Linux execution host. A separate prospective scientific continuation must explicitly authorize reuse of all corrected tuning data, independently apply/freeze the original global PI-selection rule and retain the original reserved conditions/budgets before any confirmation acquisition. This mission authorizes none of that execution.
