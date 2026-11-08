# Final V2 Core closure campaign

## Decision

**NEUROMANCER V2 CORE RELEASE HOLD**

The one-day campaign completed a finite qualification attempt and preserved its failures. Publication is blocked by a macOS suspend-during-cleanup failure and cross-platform exact numerical reproduction failures. Successful ordinary regression and SDK jobs do not clear these failures.

| Boundary | Decision |
| --- | --- |
| Core engineering | FAIL against the complete closure acceptance criteria |
| Core qualification | HOLD |
| Core release publication | HOLD |
| Full SDK reliability | HOLD |
| Personal-style refactor | HOLD, unchanged and excluded |
| Biological validation | NOT RUN |
| Physical hardware execution | NONE |

## Release identities and repository state

- Remote main at reconnaissance and closing audit was `db4485613cba8128ee643159b25ef29523ca6c95`.
- PR #5 had already been merged at `a5ebbad40bc9018ee33f201380200e1c52127718` before this campaign began. The originally supplied integration and evidence references were historical references.
- Exact tested hardening source is `5994e64c91cfc81717f4682aab5f2ad8da102a1c` on `release/v2-core-closure`.
- This report and retained artifacts are on `release/v2-core-closure-evidence`. Its containing commit is evidence-only and is not represented as a successful release qualification.
- Version remains `2.0.0rc1`, with Python `>=3.12,<3.13`. A research prerelease remains appropriate pending qualification.
- No Git tags or GitHub releases existed at the closing audit. No release URL exists. No merge, tag or publication was performed by this campaign.
- The final instruction prospectively authorized the bounded core scope and conditional publication. Failure of mandatory gates prevented exercising the publication authorization.

PR #5, the earlier core-scope approvals and previous merges remain in history. No branch was force-pushed. The unqualified style and performance branches remain separate. SDK Issue #7 remains open. Unrelated research pull requests were left intact. [Merged PR #5](https://github.com/adithyakupad/neuromancer/pull/5), [SDK Issue #7](https://github.com/adithyakupad/neuromancer/issues/7)

## Finite plan and exact source changes

The committed [closure plan](FINAL_CORE_CLOSURE_PLAN.md) preceded execution. One source push launched one attempt of each existing hosted workflow plus a new finite closure workflow. Each closure host prescribed three sequential rounds of five suspend tests, stopping on the first failed round. No workflow was rerun. Linux completed all three rounds. macOS stopped after round one, leaving rounds two and three unexecuted under the frozen stopping rule.

The hardening commit changed five files relative to main.

| File | Purpose |
| --- | --- |
| `tests/test_final_core_closure.py` | Six deterministic regressions exercising the actual embedded suspend-injection function with controlled clocks and checkpoint files |
| `.github/workflows/final-core-closure.yml` | Bounded, read-only Linux/macOS confirmation and exact evidence reproduction, with unconditional artifact retention |
| `reports/engineering/FINAL_CORE_CLOSURE_PLAN.md` | Prospective budgets and stopping rules |
| `docs/V2_CORE_RELEASE_SCOPE_REVIEW.md` | Record superseding conditional publication authorization and current numeric blocker |
| `docs/V2_CORE_RELEASE_NOTES_DRAFT.md` | Keep the release unpublished and distinguish current qualification from historical M026 results |

There were no changes to `src/`, scientific analysis scripts, the protected worker fixture, the protected suspend test, numerical archives, package dependencies, mathematical tolerances or supervisor deadlines. No new provenance exception was needed. Source algorithms and protected active-file replacements remain as found on main.

## Original missing-checkpoint failure

The original failed run retained `DEADLINE_EXCEEDED`, worker state `CREATED`, terminal `NOT_STARTED`, no worker PID and `cleanup_verified=true`. The injected resume timestamp was `523719462890 ns`, against deadline `515151107639 ns`. Active host elapsed time was about `0.37012408 s`. This establishes that the fixed-time injection expired the deadline before worker launch. No worker existed to publish `partial.txt`.

The test assumed a checkpoint existed while its setup permitted termination before startup. This is an evidenced fixture precondition race. It does not establish loss of a checkpoint previously written by a worker. The production contract preserves published artifacts and permits fail-closed termination before startup.

Main already contained a later fixture correction. Post-checkpoint suspend scenarios wait for the actual parent checkpoint and, for the descendant case, the child's checkpoint. Deadlines remain 1.8 s globally, with the original cleanup allowances and independent six-second watchdog. Clock-error scenarios retain distinct pre-readiness and post-checkpoint cases. The supervisor, native clock implementation and fail-closed statuses were unchanged.

The six added regressions compile the actual injection function from `test_suspend_clock.py` and supply deterministic time/filesystem states. They demonstrate absent checkpoints, interrupted staging files, delayed parent and child readiness, the exact elapsed-time boundary and pre/post-readiness clock faults. The original unguarded injection fails the absent-checkpoint assertion. These tests establish the specific original correction, not universal real-process scheduling reliability. The original failure artifact is retained in `original-suspend-failure.tar.gz`. [Original failed run](https://github.com/adithyakupad/neuromancer/actions/runs/42334001244)

The M008–M012 histories, M005A.2 architecture, M005A.4 clock qualification and subsequent readiness records were reviewed. No physical suspend was automated.

## New macOS failure in the fixed confirmation

The first macOS closure round failed `expired_suspend_descendant`. The checkpoint files existed, but the descendant finished imports too late for the intended running-phase injection.

| Event | Qualified-clock time, ns | Seconds relative to supervisor start |
| --- | --- | --- |
| Start | 872939826795 | 0 |
| Worker RUNNING | 872949936586 | 0.010109791 |
| Work cutoff | 873939667487 | 0.999840692 |
| STOP_REQUESTED | 873941389050 | 1.001562255 |
| Child imports completed | 873953757527 | 1.013930732 |
| First injected resume | 883965290272 | 11.025463477 |
| TERM | 883965412467 | 11.025585672 |
| KILL | 883965926268 | 11.026099473 |
| Final result | 883966433840 | 11.026607045 |

Actual active elapsed time was `1.029750765 s`. The injected clock advanced by ten seconds after cleanup had begun. Cleanup retained its previously selected end `874739667487 ns`, and `post_deadline_cleanup` remained false. The jump exhausted that cleanup budget before reaping was verified. The supervisor correctly reported `CLEANUP_FAILURE` with cause `DEADLINE_EXCEEDED`, rather than success.

This exposes an additional setup/cleanup interaction beyond the original missing-checkpoint race. Checkpoint gating alone does not guarantee injection occurs before work cutoff. The retained timeline supports that mechanism. It does not establish a safe production repair or prove all real suspend-during-cleanup cases are handled. Neither a longer deadline nor accepting the failure as a pass is justified.

The artifact finalizer independently checked owned PIDs 8871 and 8875. `ps` returned 1 with no matching rows. No outer watchdog intervention was recorded. Thus no surviving owned process was observed at that check, while cleanup verification within the supervisor contract failed. Both facts remain explicit. No claim of timely verified reaping is made for this case.

The next smallest discriminating test would deterministically inject the clock jump after STOP_REQUESTED and before cleanup reaping, separately from worker startup. Any proposed correction must retain the existing deadline and fail-closed contract and obtain fresh exact-source qualification. This campaign did not start another repair/retry cycle after mandatory failure.

## Hosted results on the exact hardening source

| Workflow | Linux | macOS Intel |
| --- | --- | --- |
| Package and regression | PASS, 237 tests, 46 warnings, 85.65 s | PASS, 237 tests, 46 warnings, 218.88 s |
| Existing M008 diagnostic campaign in package workflow | 35/35 completed | 35/35 completed |
| Additional fixed suspend confirmation | 15/15 passed across three rounds | 4/5 passed in first round, remaining rounds not run |
| Exact 102-array golden replay | FAIL at `initial_theta` | FAIL at `initial_theta` |
| V1 archive model-state replay | FAIL at archived model-state hash | FAIL at archived model-state hash |
| Strict M013/M014 archive script | FAIL at M013 JSON equality, M014 not reached | FAIL at M013 JSON equality, M014 not reached |
| Experimental SDK matrix | PASS in this execution | PASS in this execution |

Substrate qualification also passed on its existing Linux job. There is no separate macOS substrate workflow in the repository. The complete macOS suite nevertheless exercises substrate tests. No checks were removed or marked optional to hide failure.

- [Package/regression run 42433119416](https://github.com/adithyakupad/neuromancer/actions/runs/42433119416)
- [Finite closure run 42433119372](https://github.com/adithyakupad/neuromancer/actions/runs/42433119372)
- [Substrate run 42433119325](https://github.com/adithyakupad/neuromancer/actions/runs/42433119325)
- [Experimental SDK run 42433119592](https://github.com/adithyakupad/neuromancer/actions/runs/42433119592)

Warnings were retained. Each complete suite reported 46 Brian2 parser dependency deprecations. Brian2 also logged an unused `public_tick_driver` object warning from a test fixture. Hosted infrastructure reported Node action-runtime migration and Ubuntu image migration notices. These are maintenance risks. The explicit cleanup and exact reproduction failures are the release blockers.

## Numerical evidence and preservation

Local macOS arm64 Python 3.12.15 reproduced all 102 golden arrays exactly, including neural events, observation counts, FIR/ARX forecasts, RLS states, PI actions, planner actions and plasticity outputs. Local V1 canonical reproduction passed, including all four required numerical artifacts and four byte-identical figures. The existing strict M013/M014 script passed locally. It verified 38,721 protected paths and the unchanged preservation manifest.

Both hosted hosts reproduced 47 of 102 arrays byte-for-byte. All array shapes and dtypes matched. Independent comparisons of the saved outputs found maximum absolute differences `5.3290705182007514e-14` on Linux and `7.815970093361102e-14` on macOS Intel. Differences include initial fitted coefficients, covariance, predictions and candidate scores. Tested fixed/adaptive/PI action arrays, spike indices/times, observation counts, eligibility and reward-weight arrays matched exactly. This narrows the discrepancy but does not satisfy the byte-equality gate.

V1 statistical analysis emitted the preserved adaptive-superiority FAIL, but the independently recomputed RLS state digest failed before the canonical reproduction command could complete on both hosted hosts. The original data and its stored hashes were unchanged. This is a recomputation failure, not evidence of archive replacement.

The strict M013 JSON script encountered condition-number differences on hosted environments. The prior publication workflow already had a narrowly bounded `1e-14` condition-number allowance. That existing allowance was not expanded. The current strict script stopped before M014. Independently, the previous main publication run failed M014's zero-tolerance prediction assertion, with Linux maximum error `4.99600361e-16`. That earlier failure remains historical evidence. Small floating-point implementation differences are a plausible explanation for these portability failures. No particular BLAS or CPU instruction was isolated as the sole cause. [Previous failed publication run](https://github.com/adithyakupad/neuromancer/actions/runs/42428618054)

No numeric implementation, threshold, rounding rule, archive or golden reference was changed. A passing local reconstruction does not replace failing hosted exact reconstruction. Resolving this requires either an independently qualified deterministic numerical implementation or a prospectively reviewed portability contract. A tolerance amendment is not authorized by the current frozen acceptance criteria.

M015 verification reconstructed 336 trial/sham records and eight reduced scalar/Brian2 archives, with maximum current difference `7.105427357601002e-14 pA` under its original tolerance. M016 archived verification reconstructed all nine cases, 144 windows and 28 receipts and retained PI MAE 1.50 versus 1.00 spikes/bin. The protected data were read or copied to scratch. No historical scientific acquisition or locked cohort was opened.

## Package and core demonstration

Candidate wheel is `neuromancer-2.0.0rc1-py3-none-any.whl`, 95,561 bytes.

SHA-256 is `3a3a4bc6655b4dcb5a10885bfba52d3def64751bfcafd9e623d2b0a3f499ba20`.

It was built from an archive of exact candidate HEAD, including `LICENSE`, `README.md`, `pyproject.toml` and `src/`. Every module payload was compared with the archived source. Metadata and the included MIT license matched. No scientific NPZ/HDF5 archives were included. Scientific dependencies remain Brian2 2.10.1, NumPy 2.5.4 and SciPy 1.18.0. No CL SDK is needed for the core installation.

A fresh environment installed the pinned stack and wheel. `pip check`, installed imports, CLI help and the bounded CLI neural smoke passed. Imports resolved into fresh `site-packages`. The final installed smoke ran outside the checkout with `PYTHONPATH` unset. An initial smoke invocation inherited a source-path override and was not used as proof of installed execution. Its supervisor record is retained alongside the corrected installed invocation.

The local golden probe also completed the short causal Brian2 feedback/replay demonstration. Archived neural-computation and SDK demonstrations were reconstructed. No new favorable scientific cohort was collected. Wheel payload equivalence was checked. Cross-build wheel-container byte reproducibility was not asserted.

There is no public asset to download. Public-release installation audit, tag resolution and public-release checksum verification were therefore NOT RUN. The retained wheel is a candidate artifact only.

## SDK boundary

The accelerated SDK 1.0.0 producer request/callback stall remains unresolved. The successful matrix in this campaign verifies executed simulator operations, including nine 8,000-frame recordings, 144 observation windows and 28 paired commitments on each platform. It does not establish intermittent scheduling reliability.

M021's recorder stop during the final yield remains preserved. Invalid/expired request rejection, hardware interlock and existing SDK workflow remain enabled. SDK tests and historical failures remain visible. Original M019 recording-only producer failures and M020's lack of a safe repair continue to limit the backend. There is no asserted upstream workaround in this candidate. SDK installation stays separate and simulator-only. Full SDK reliability remains HOLD. [M019 failure](https://github.com/adithyakupad/neuromancer/actions/runs/42183363096)

## Immutable scientific findings

| Study | Preserved result |
| --- | --- |
| V1 | PI 11.46875, adaptive RLS-MPC 13.12921875, fixed MPC 18.9778125 Hz·s. Adaptive superiority over PI FAIL |
| M013 | Plasticity engineering demonstrated. Reward-modulated superiority INCONCLUSIVE, confirmation NOT RUN |
| M014 | Reservoir benchmark implemented. Recurrence-specific memory INCONCLUSIVE |
| M015 | Structural feedforward access verified, cue-access gate FAIL, retention NOT RUN. Reduced scalar numerical comparison qualified |
| M016 | Synthetic simulator causal I/O demonstrated. PI 1.50 versus no-pulse 1.00 spikes/bin. Control improvement FAIL |
| Historical studies | V0.1/V0.2, M003 model-superiority negatives, M004 identification/detection distinction and M005A horizon-specific findings remain unchanged |

There is no living-neuron, clinical, physical stimulation-safety or hard-real-time validation. Hardware execution remains NONE. The personal-style branch and failed V1.1 speedup claims remain excluded. No style changes were accepted during this campaign.

## Execution and resources

Local bounded stages used the existing qualified supervisor and independent watchdog. Regression used 180 s. Golden replay, V1 replay and archive analysis used 240 s each. Installed smoke used 120 s. All local stage supervisors completed with verified cleanup and no watchdog intervention.

| Local stage | Supervised wall time |
| --- | --- |
| Complete 237-test suite | 50.2343 s |
| Golden and neural replay | 6.41275 s |
| Strict archive analysis | 5.95393 s |
| Canonical V1 reconstruction | 84.6921 s |

The golden probe recorded native macOS maximum RSS `951336960` bytes. This is a process high-water mark, not total simultaneous workload memory. No hardware timing or performance-improvement claim is made. Hosted job caps remained the configured 20/25-minute limits, original worker deadlines and independent watchdogs. The new closure jobs finished at approximately 100 s on Linux and 312 s on macOS including setup.

The local independent owned-PID inspection found no remaining processes. Two duplicated `cleanup_verified=false` records came from the intentional `test_cleanup_failure_is_explicit` fixture, which forces the group-existence probe to stay true and asserts the failure is visible. The new hosted macOS cleanup failure is recorded separately and is not classified as an intentional passing injection.

Representative actual commands, with retained output roots substituted, were as follows.

```sh
.venv/bin/python -m pytest -q tests/test_final_core_closure.py
PYTHONPATH=src .venv/bin/python scripts/m014_supervise.py OUTPUT/regression-guard 180 .venv/bin/python -m pytest -q --junitxml=OUTPUT/tests.xml --basetemp=OUTPUT/pytest-tmp
PYTHONPATH=src .venv/bin/python scripts/m014_supervise.py OUTPUT/golden-guard 240 .venv/bin/python scripts/m017_probe.py OUTPUT/golden --neural --reference reports/engineering/evidence/m017/golden_final
PYTHONPATH=src .venv/bin/python scripts/m014_supervise.py OUTPUT/v1-guard 240 .venv/bin/python scripts/reproduce_v1_evidence.py --output OUTPUT/v1
PYTHONPATH=src .venv/bin/python scripts/m014_supervise.py OUTPUT/archive-guard 240 .venv/bin/python scripts/m017_reproduce.py OUTPUT/archives
```

Each invocation requires a new output directory. Qualified-clock access was used for native local process tests. The core and SDK exact executed commands are also preserved in hosted logs and workflow source. Fresh installation used `pip wheel --no-build-isolation --no-deps`, the unchanged requirements file and a new venv. `ruff check tests/test_final_core_closure.py` and `git diff --check` passed. No configured type-checking or coverage gate was added or claimed.

## Evidence and next permitted action

Raw logs, returned supervisor results, failed and passing fixture records, JUnit, original failure evidence, wheel audit and independent array comparisons are retained under [the closure evidence directory](evidence/final_core_closure). The [artifact manifest](evidence/final_core_closure/artifact-manifest.json) records file sizes and SHA-256 values. Historical manifests were not rewritten. This evidence commit is a separate archival review identity, while every execution points to tested source `5994e64c91cfc81717f4682aab5f2ad8da102a1c`.

The exact blocking work is a deterministic disposition of the late cleanup clock transition and a qualified way to satisfy the cross-platform byte-exact numerical contract. No favorable rerun can substitute for either. Optional SDK and style work remain deferred.

The existing main publication workflow additionally restricts its allowed post-PR5 source delta to the workflow file itself. Any future reviewed source hardening will need an explicitly updated narrow source guard, fresh exact-source qualification and the documented merge/publication sequence. It must not be force-merged around these guards.

No new research mission was started. The release campaign stops here with an evidence-complete HOLD candidate.
