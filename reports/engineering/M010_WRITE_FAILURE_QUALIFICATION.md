# M010 — write-failure fixture reliability and refactor qualification

**Overall decision: PARTIAL / HOLD.** The local fixture repair, numerical and
preservation checks pass. The prespecified performance repeat fails two p95
bounds; that failure is retained. Hosted reliability qualification is a separate
remaining gate, not a way to override performance HOLD. No merge/tag/publication.

## Repository and evidence

Started clean at72824e6cb48e714e11a398f2787146099daec397 on
refactor/personal-code-style. Review branch:engineering/m010-write-failure-qualification.
Preregistration ec6a8e99 preceded instrumentation and fixture changes. Instrumented
bank source02838f0e; fixture repair d9781990; resource/CI verification and deadline
inheritance changes are separately reviewable commits. Pre-report source revision:
`822cbf5433e474f9b7da29499829b61d394f10b3`. Exact final containing commit and final hosted checks are supplied in
the handoff; a report cannot embed its own commit hash without changing that hash.

The original failure remains unchanged in
`evidence/personal_style/final_ci_failure/`, including complete hosted artifact ZIP
SHA25658dd90e3eaba87dc23c109db33c0893b4222e5af3ce32fddec283b0dcf9dd206.
Original run41895058114 at3cf88af1:199passed/1failed/25warnings. Later green
72824runs41896515737/41896515788 are historical observations, not a repair.
M008's report/source08a956ce and M009 backport/CI evidence were inspected. No
historical report, source snapshot, protocol or numerical archive was rewritten.

## Root-cause disposition

The original worker completed imports at101.764ms; work cutoff999.953ms; TERM
1200.106ms; a running poll1200.212ms; first observed exit1210.369ms, returncode-15.
Global deadline1799.953ms. Partial checkpoint survived, cleanup_verified=true,
no outer-watchdog intervention. Incomplete stderr traceback and no atexit marker
do not establish the exact time of the exception or interpreter termination.

| Hypothesis | Evidence-based assessment |
| --- | --- |
| A: operation/filesystem delayed | Possible historical contributor; no operation timestamps recover it. Controlled pre-operation delay reproduces deadline classification. |
| B: traceback/finalization delayed | Historical traceback is incomplete. Independently injected traceback and shutdown delays reproduce late living workers after an actual error. Which historical substage stalled remains unidentifiable. |
| C: timely exit only observed late | Not supported by the preserved running polls; no timely exit is established. Actual kernel exit time is distinct from first observed exit. |
| D: fixture assumed bounded prompt exception exit | Established contract defect: raising/reporting an exception is not process termination. The old unconditional expected failure status assumed completion within1s. |
| E: production lifecycle defect | No demonstrated contract violation in this trace or the controlled probes. Deadline result and bounded cleanup are appropriate. |

The explanation is a defective test inference, not a claimed reconstruction of
an unknown historical OS syscall/scheduling stall. We do not infer A or B solely
from passing reruns. Root disposition D is supported by the original live process
observations and causal delayed-stage controls. The residual A/B uncertainty is
explicit and cannot be recovered by repeatedly rerunning the old test.

Python documents exception display separately from exit, and os._exit bypasses
normal cleanup/stdio flushing: [sys.excepthook](https://docs.python.org/3.12/library/sys.html#sys.excepthook),
[os._exit](https://docs.python.org/3.12/library/os.html#os._exit),
[traceback formatting](https://docs.python.org/3.12/library/traceback.html).
Accessed2026-11-04; runtime remains3.12.15, not a documentation-version upgrade.

## Frozen investigation and actual results

`DIAGNOSTIC_PLAN.md` froze25trials before execution. Original1.8sglobal deadline,
1.0swork cutoff and0.2/0.2/0.4scleanup allowances remain. Each trial has an
independent6souter watchdog, CPU20s/file16MiB limits and1GiB measured-child-RSS
check; no physical sleep/artificial machine load. Twenty-five cases finished
inside240s with227.256sremaining. No trial exclusion or replacement.

| Diagnostic | Count | Actual result |
| --- | ---: | --- |
| Untouched original write_failure |5|5WORKER_FAILURE; observed exit113–153ms |
| Instrumented filesystem error |5|5WORKER_FAILURE |
| Pure-Python error |3|3WORKER_FAILURE |
| Caught filesystem error / explicit nonzero exit |3|3WORKER_FAILURE |
| Traceback-stage1.2sdelay |2|2DEADLINE_EXCEEDED |
| Normal interpreter exit |3|3COMPLETED |
| Pre-operation1.2sdelay |2|2DEADLINE_EXCEEDED |
| Interpreter-shutdown1.2sdelay |2|2DEADLINE_EXCEEDED |

All25have verified cleanup, surviving partials, matching qualified-clock domains,
no watchdog intervention, reaped leaders and independently absent owned groups.
Per-event timelines and source manifests are retained. Custom traceback hooks are
explicitly diagnostic instrumentation and are not identical to native display.

## Repair and constraints

Production supervisor/clocks are UNCHANGED. The original worker is UNCHANGED and
continues as diagnostic prior art. New `tests/supervisor_failure_worker.py` uses
stdlib-only qualified-clock bootstrap; ready/release under the already-created
original deadline; a real attempted write under an existing partial.txt file;
catch/validate NotADirectoryError and ENOTDIR; close/publish failure.json with
scientific_success=false; explicit nonzero exit23. It never fabricates an error
or exits0. The record/intent alone cannot satisfy the test: supervisor-observed
exit AND reaping must precede work cutoff. Explicit os._exit is only a synthetic
fixture choice, not a production shutdown recommendation.

`test_real_worker_lifecycle[write_failure]` is strengthened to exact WORKER_FAILURE,
code23, clock/receipt ordering and observed exit before cutoff. No late worker is
accepted. Added `write_failure_late` performs and records the SAME error, then
remains alive until TERM/original absolute bound. It must be DEADLINE_EXCEEDED,
code-15, with verified cleanup; an earlier failure record cannot create success.
All prior general exception, interpreter exit, cancellation, group/descendant,
clock-discontinuity and boundary tests remain enabled. New CI steps run the fixed
25diagnostics plus20timely/5late repeats and independent same-host group checks.
15/20min workflow budgets and test assertions are not relaxed.

## Local verification and commands

- Focused supervisor/boundary/clock suite:59passed in21.66s; final budget-guard
  revision repeated59passed in22.04s, with its own separately retained20/5bank.
- Corrected repeat bank:20/20WORKER_FAILURE and5/5DEADLINE_EXCEEDED; cleanup and
  no live owned groups independently checked. Timely observed-reaping margins:
  min903.439ms,median947.858ms,max958.543ms. These are finite measurements,
  not guarantees against arbitrary scheduler stalls.
- Full regression:201passed,25existing Brian/pyparsing warnings,89.99s; no skips.
- Exact91-array and canonical-JSON comparison:PASS, including FIR/ARX forecasts,
  RLS coefficients/inverse information, PI/anti-windup, all625MPC scores/actions,
  neural spikes/counts and continuous/chunked replay.
- Evidence-only reproduction:four canonical numerical outputs and four figures
  byte-identical. Independent model/statistical verifiers pass; no neural study.
- Full1200squalification completed with945.601sremaining; installed wheel/pip-check/
  200mssmoke used the SAME original deadline,823.638sremaining.
- Installed site-packages hashes match the four source modules. Python3.12.15,
  NumPy2.5.4,Brian2.10.1,SciPy1.18.0,pytest9.1.1; package1.0.0. No dependency upgrade.
- Whole starting-tree audit permits only tests/test_supervisor.py and the two
  active workflows to change. All src, including four style modules, and all
  historical scientific records are byte-identical to72824e6c.

Actual command files/logs/XML are under focused/,full/,diagnostics/ and repeats
manifests. Relevant commands (fresh output roots):

```sh
PYTHONPATH=src .venv/bin/python tools/m010_diagnose.py NEW_DIAGNOSTICS
PYTHONPATH=src .venv/bin/python tools/m010_qualify.py focused NEW_FOCUSED
PYTHONPATH=src .venv/bin/python tools/m010_qualify.py full NEW_FULL
PYTHONPATH=src .venv/bin/python tools/m010_verify.py repeats NEW_FOCUSED/repeats NEW_VERIFY.json --live-groups
PYTHONPATH=src .venv/bin/python tools/m010_verify.py preservation . NEW_PRESERVATION.json
```

Actual local interpreter:/tmp/neuromancer-m007-20261101/bin/python. Batch drivers
inherit an enclosing earlier deadline, require enough time for the unchanged
fixture/watchdog before launch, and never reset an enclosing budget. Test trees
are losslessly archived with per-entry digest/link verification; originals remain
in/tmp/neuromancer-m010-retained-test-trees. Existing committed evidence is not
migrated or deleted. Reading archived old PID records on another host is not a
live process check; live-group assertions run on their originating host.

## Performance verification — HOLD retained

No production source was modified; source trees are byte-identical. Each bank
uses threeABBAcycles,12processes,54raw samples/source/workload, same91-array
outputs, one worker, no outlier exclusion. All numerical comparisons pass.

First bank misses p95bounds and is FAILED/CONFOUNDED:17.897sof overlap with
installed-wheel verification is established by qualified-clock records. This was
an avoidable execution-control error and is retained. The prospectively frozen
`PERFORMANCE_EXECUTION_CORRECTION.md` allowed exactly one isolated repeat, same
thresholds, inside the FIRST bank's unchanged600sabsolute deadline. No third
attempt. The isolated repeat also misses two p95limits. Identical source does
not excuse changing the frozen measured gate; timing variability is not proof
of a code regression or proof of universal performance equivalence.

| Workload | First median / p95 ratio | Serialized median / p95 ratio | Serialized gate |
| --- | ---: | ---: | --- |
| fir_1000_predictions | 0.996 / 1.627 | 1.019 / 1.296 | FAIL |
| rls_100_updates | 1.004 / 1.584 | 1.017 / 1.231 | FAIL |
| planner_625_candidates | 0.996 / 1.313 | 0.883 / 0.828 | PASS |
| pi_1000_observations | 0.999 / 1.510 | 0.955 / 0.656 | PASS |
| arx_fit | 0.996 / 1.791 | 1.058 / 1.045 | PASS |

Thresholds remain<=1.10median,<=1.20p95,<=1.10max-RSS ratio. Serialized max-RSS
ratio1.036; current peak937.05MiB,
inside2GiB. Both banks and CPU/wall samples are retained. No speedup claim.

## Hosted qualification and final integration boundary

Hosted Linux/macOS15Intel package and legacyLinux checks must run on exact final
code; earlier green jobs do not substitute. Their actual outcomes are recorded
in the closing appendix/handoff. All201tests and fixed50M010probes/job remain
enabled, with independent cleanup checks and failure-retaining uploads. Hosted
Intel macOS is distinct from local Apple M5/arm64; no hosted-arm64 claim.

Overall M010 stays PARTIAL/HOLD even if hosted reliability checks pass, because
current performance qualification is unresolved. Reliability repair may be
reviewed independently, but V1/personal-style integration is not automatically
cleared and no merge/tag/publication is performed. The old personal-style HOLD
and all negative scientific findings remain unchanged: adaptive control losing
to PI, V0.1/V0.2 failures and other historical findings are not reinterpreted.

Smallest next decision: independently review the source-identical timing
comparison and measurement uncertainty, then prospectively authorize an appropriate
performance qualification if justified. Do not silently drop tail samples, lower
a threshold, run further retries or start a broad optimization/neural campaign.
The historical exact A/BOS-latency subcause also remains unrecoverable from its
partial trace; the justified fixture repair does not claim to recover it.
