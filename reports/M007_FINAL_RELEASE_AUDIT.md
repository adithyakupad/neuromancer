# M007 — Final scientific and engineering release audit

Audit requested 2026-11-01 (America/New_York). Starting clean `codex/v1-finish` at **6420f8529289ec31f0237eb69a705c64d8467ed7**; review branch **release/v1-audit**. No merge, tag, release, controller tuning, scientific acquisition, validation or locked-network access is authorized or performed by this audit.

**Final release recommendation: PARTIAL.** Local installation, software, numerical evidence and hosted CI qualify the scoped research candidate. Explicit license/reuse terms and alignment of package0.2.0 metadata with a proposed v1.0.0 publication remain prepublication decisions. A negative adaptive finding does not block a correctly scoped research release.

## Independent gates

| Gate | Current decision | Evidence |
|---|---|---|
| A Repository/provenance |PASS|Expected revision/clean start; original16417-file preservation and16275-file release manifests verified before authorized documentation changes. Scientific source/data remain unchanged.|
| B Clean installation |PASS|Fresh isolated CPython3.12 environment; exact pins; wheel build/install; all29 source modules match; imports and pip check; actual installed-wheel200ms smoke.|
| C Local regression |PASS|183 passed,25 warnings,0 failures/errors/skips in63.43 s before documentation changes; after the provenance-path repair,183 passed again with25 warnings in62.77 s. All hosted failures are retained below.|
| D Numerical reproduction |PASS|New raw-count implementation plus fresh existing analytical replay; complete20/260 primary and3/24fault cohorts.|
| E Claim validity |PASS|Stale README corrected; scoped development-only claims and mechanism uncertainty explicit. Claim catalog includes unsupported broad claims as exclusions, not release assertions.|
| F Documentation |PASS|Updated README/guide, evidence-only CLI, scientific limitations and suggested release notes; documented fresh-output/current-boot deadlines.|
| G Hosted CI |PASS|V1 Linux/macOS wheel jobs and substrate workflow passed atf76c09d0; exact run links and earlier failures below.|
| H Final release readiness |PARTIAL|No numerical discrepancy; public publication still requires license/version choices and final maintainer review.|

## Clean installation and executed software checks

Fresh environment `/tmp/neuromancer-m007-20261101` was created with `/opt/homebrew/bin/python3.12 -m venv`. Installed `requirements-v1.txt` without upgrades: Brian2 2.10.1, NumPy2.5.4, SciPy1.18.0, pytest9.1.1 and all original transitive pins. Built with `pip wheel --no-deps --no-build-isolation`, installed that wheel with `pip install --no-deps`, ran `pip check` and imported every package module from the new environment's **site-packages**, not an editable source path. Wheel/source byte identity and SHA256 are in `wheel_verification.json`; build/install/freeze logs are retained.

The full183-test suite covered neural dynamics/replay, causal timing, binning, constraints, estimation/forecasting, FIR/RLS, residual detection, PI/predictive planning, isolation, atomic artifacts, process-tree failure injection and deadlines. All passed;25Brian2/pyparsing deprecation warnings are preserved in worker-0.log and JUnit. The installed `neuromancer-diagnostic --mode smoke` executed10legal20ms steps on development network0/defaultnoise0. This200ms example is non-confirmatory and does not generate new controller endpoints. No complete neural scientific acquisition was rerun.

Commands and fresh1800s same-domain audit deadline are retained in `reports/evidence/m007/commands.json`, `environment.json`, `supervision/` and `local_qualification.json`. The command sequence separately ran the historical raw model/planner verifier on primary and fault evidence, the frozen analyzer into a new directory and deterministic figure generation. This uses fresh audit deadlines, not expired historical execution deadlines.

## Scientific numerical reproduction

The M007 implementation `reproduce.py` independently reads raw E80 spike counts, reconstructs baseline from[7,15)s of the51s prefix, sets target=baseline+1 Hz, aggregates nonoverlapping1s rates and scores **all[16,64)s** after loss. It verifies receipts, timestamps, event/channel counts, exact cohorts, current bounds/budget/slew, fallback flags and original resource closures. It does not fit/select new models or substitute an analysis.

Each independent network averages noise47/48 first. Paired percentile-bootstrap resampling uses PCG64seed20261105 and10000 whole-network draws, exactly as protocol011. Relative benefits are formed per network with the frozen.01 Hz·s denominator floor; no floor activates.

| Controller | Recomputed post-loss IAE (Hz·s) |
|---|---:|
| PI10/5 |11.46875000|
| RLS-MPC |13.12921875|
| FIXED-MPC |18.97781250|
| BIAS-MPC |13.82062500|
| Calibrated FIXED |17.76281250|
| ZERO |46.28375000|

| Paired adaptive benefit | Mean absolute [95%CI], Hz·s | Mean relative [95%CI] | Positive networks | Frozen gate |
|---|---|---|---:|---|
| Versus PI |−1.66046875 [−2.19515625,−1.14796484]|−14.63065% [−19.36594%,−10.09400%]|0/10|FAIL|
| Versus fixed MPC |5.84859375 [5.04307422,6.55656250]|30.59795% [27.18958%,33.62081%]|10/10|PASS|

Both comparisons are required. **Final adaptive-superiority FAIL independently reproduced.** H3 late feasibility and H4/H5 cost/stationary guards reproduce their original PASS; they cannot rescue failed H1a. There is no numerical discrepancy requiring neural reacquisition. Per-network values, all284branch rows, costs, biases and guards are in `independent_results.json` and `independent_trials.csv`.

All260 primary branches have zero unexpected fallback/model-failure/constraint events. The24fault branches are checked separately: deliberate safe bins are53 perPI branch and100 perRLS branch; no constraint or model failure. DELAY and DROP expose the same missing on-time data after stale discard; no asynchronous transport fidelity is inferred. Completed worker cleanup and original10800s development/shared-fault budgets are verified from original launch/closure records, sampled memory/storage and high-water evidence. Nominal1s polling had documented overhead; sampled checks do not prove continuous hard limits or hard-real-time behavior.

## Interpretation and claim audit

The empirical conclusion is narrow: online updating improved this model-based controller over its frozen counterpart, while competitive PI achieved lower cumulative error on all ten development networks. RLS used less current and had better final-window MAE; those are genuine trade-offs, not primary superiority. Prediction improvement is not control improvement.

Possible explanations include model mismatch, planner objective/regularization, forgetting timescale, weak excitation, uncertainty and feedback robustness. The experiment does not causally isolate why PI wins. Neither severe late regressor conditioning nor a coefficient-scale projection identifies physical actuator gain. No new mechanistic outcome is introduced.

`claim_catalog.csv` classifies37substantive claim families across README, V1 report, figures, methods/schema, historical summaries and release scope. Incorrect stale README status and unsupported present-tense biological framing are corrected. Historical reports themselves remain unchanged. M003.1's negative superiority finding does not prove equivalence; M003.2 does not establish biological state independence. M004's one-sided residual detection and probing-based prediction success remain distinct from control, with causal-effect validation/coverage/repeated-alarm limitations. V0.1/V0.2 failures and M005A.5 short-horizon FAIL remain intact.

There is no evidence for living-neuron control, biological validation, neural plasticity, hardware-safe stimulation, CL1 real-time compatibility or generalized adaptive superiority. These are exclusions in the corrected release documentation, not supported features. Previously inspected M003/M004 validation identities do not constitute new controller validation. M005B validation10–14 and locked100–119 remain unexecuted.

## Figure, table and guide reproduction

All four retained PNG/SVG figures were regenerated **byte-for-byte** on the pinned local stack. Frozen tables/summary and independent primary statistics are compared separately; numerical audit tolerance is1e-12 for headline statistics and declared2e-8for weighted matrix reconstruction, with exact events/counts/digests/actions where specified. Image identity on other OS/font stacks is not promised. Gray figure bands are tolerance references, not confidence intervals.

The old guide incorrectly suggested reusing an existing analysis directory and historical boot-scoped deadlines, omitted a minimal quickstart and made fresh acquisition too easy to confuse with evidence reproduction. These are corrected. `scripts/reproduce_v1_evidence.py` is a thin evidence-only launcher with a fresh1200s deadline (or inherited enclosing deadline), unique outputs and byte comparisons. It never acquires neural trajectories or opens held-out cohorts. Its actual guide-following run passed: four tables/summary files and four figures byte-identical; no new neural acquisition.

## Hosted CI and publication boundary

Authorized GitHub access was confirmed without retaining credential values. Only `release/v1-audit` may be pushed; main remains untouched. The V1 workflow now builds/installs the wheel before tests, matching the clean-install audit; pins are unchanged and scientific acquisition is absent from CI. Hosted source revision **f76c09d0f18850f063aad43ffa2dc09d313ba7b5** passed the [V1 matrix](https://github.com/adithyakupad/neuromancer/actions/runs/41344770135) and [substrate workflow](https://github.com/adithyakupad/neuromancer/actions/runs/41344770098). Linux JUnit records183 tests/0 failures/errors/skips in67.408 s; macOS records183/0/0/0 in81.658 s. Both report25pytest warnings, plus retained Brian unused-object notices. The V1 jobs built/installed wheels, passed pip check/imports and executed the smoke. Downloaded JUnit, wheel/smoke artifacts and full logs are committed; wheel source bytes and smoke hashes verified. Linux regression qualification does not qualify the macOS-specific full acquisition launcher or cross-platform bitwise replay.

Earlier attempts are not erased: run41344138785 failed workflow parsing after M007 introduced runner.temp at job env scope. [GitHub context availability](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts) excludes runner there; a literal temporary path repaired it. The substrate run41344142135 and matrix41344361424 then reported182passes/1failure because the authorized README update conflicted with an old immutable-file check. The exact starting README was archived as docs/history/README_M002_SNAPSHOT.md and the test now checks that snapshot against the **unchanged** historical digest. No expected hash, scientific source or data was changed; no assertion or test was skipped. Both repairs have separate source/log records. Node20-action deprecation/forcedNode24 notices are retained as non-blocking maintenance warnings. A report/evidence-only closing commit retains identical tested package/test/workflow bytes; its CI status can be checked independently.

The repository has no LICENSE file and package metadata remains0.2.0. Maintainers must settle reuse terms and align any eventual publication version; this audit does not invent a license, create a tag or publish a release. Suggested future title: **NEUROMANCER v1.0.0 — In Silico Neural Dynamics and Closed-Loop Control**. Suggested description is in `docs/V1_RELEASE_NOTES.md`.

## Change inventory and closure

Authorized modifications: README.md, docs/V1_REPRODUCIBILITY.md, .github/workflows/v1-qualification.yml and the README snapshot lookup in tests/test_calibration.py. New files: this report; docs/V1_SCIENTIFIC_LIMITATIONS.md; docs/V1_RELEASE_NOTES.md; scripts/reproduce_v1_evidence.py; docs/history/README.md and the exact README snapshot; audit source, logs, wheel, numerical comparisons and verification evidence under reports/evidence/m007. Starting-snapshot hashes and explicit before/after hashes are in authorized_changes.json. No frozen scientific source, protocol, report or numerical file is modified.

The final Git revision is the commit containing the closed audit report, supplied in the handoff. A later report/evidence-only commit may follow a CI-tested source revision; exact tested revision and source equivalence must remain explicit. The final handoff supplies the exact closing revision and clean-tree verification. Complete changed-path inventory and before/after hashes accompany the audit evidence.

## Historical procedural caveat

The V1 report discloses that explicit storage-projection arithmetic was persisted during acquisition rather than as a separate pre-launch artifact. M007 verifies actual sampled caps and final allocation records, but cannot certify undocumented prospective checking or retrospectively repair that gap. The original reporting-publication failure and resource/clock stops remain preserved. This limits any blanket assertion that every historical procedural requirement was perfectly satisfied; it does not change the reproduced scientific endpoint or justify new neural acquisition.


## Remaining publication choices and proposed release

No numerical discrepancy remains. A–G pass with the explicitly scoped limitations above; H remains PARTIAL until maintainers select explicit license/reuse terms and align publication-version metadata (currently0.2.0) with a chosen release label. Historical pre-launch storage documentation cannot be retroactively perfected and remains a declared caveat. These are not reasons to reinterpret adaptiveFAIL or open new evaluation networks.

Suggested title: **NEUROMANCER v1.0.0 — In Silico Neural Dynamics and Closed-Loop Control**.

Suggested description: Reproducible simulated neural dynamics, constrained stimulation, partial spike observation and transparent identification/control comparisons. Includes complete evidence and negative findings: adaptive predictive control improved on a frozen model but lost to PI in the tested development task. No biological, plasticity, hard-real-time or held-out controller-generalization claim.

This audit is complete without merging main, creating tags, publishing a GitHub release or executing validation/locked networks. M006 remains HOLD. Final publication requires maintainer review rather than additional target engineering.

Complete path inventory is retained in `reports/evidence/m007/file_inventory.txt`. `authorized_changes_final.json` records the four modified pre-existing paths and verifies all production source, scientific dependency pins, frozen protocols and prior numerical/report evidence unchanged. Qualified production/test/workflow bytes match hosted-tested revisionf76c09d0; closing changes are documentation and audit evidence only.

Fresh numerical reproduction in M007 focuses on M005B. Earlier missions were reviewed for historical integrity and correct interpretation, with their algorithm tests executed; M007 does not claim a new complete reanalysis or neural reacquisition of every earlier mission.
