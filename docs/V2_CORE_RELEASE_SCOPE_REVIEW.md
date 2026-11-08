# NEUROMANCER V2 core research release: prospective scope review

**Status. Core scope authorized in the final closure campaign. Publication HOLD pending exact-source qualification.** This document is a prospective decision record and not an amendment to the historical M026 qualification. It does not certify that the full CL SDK simulator integration is reliable.

## Immutable tested source

Core integration candidate: `27872242ef2885fec8a04a7c6061584b6cb68c76` on `release/v2-0-final-integration`.
M026 evidence-only tip: `9ff56d02bb846bbdd80b71187d95831ff620f197`.
The SDK recording-lifecycle repair and narrowly authorized atomic PID fixture change are already present in the tested source. No source patch is proposed here. The documentation-only review branch will have a different commit identity.

## Proposed product boundary

Supported research functionality:
- In-silico Brian2 neural network substrate, model identification, online estimation, feedback-control algorithms and safety-checked simulator command representations.
- Deterministic replay, supervisor/process-cleanup behavior, numerical test fixtures and reproducible archived analyses.
- Reproducible package installation, CLI behavior and explicit reports of scientific uncertainty.

Experimental, **not reliability-qualified** functionality:
- CL SDK 1.0.0 accelerated simulator backend and recording/stimulation adapter, including the M021 recording-extent repair.
- macOS Intel producer scheduling and request handoff. M019 reproduced a published request and stationary write head, with no callback before the SDK's internal 100 ms wait timed out. M020 did not establish a safe production repair.

Excluded from all supported claims:
- Physical MEA / CL1 hardware execution, real living-neuron control, clinical use, hard-real-time performance guarantees, reliable biological plasticity, controller superiority or recurrence-specific memory.

The experimental SDK integration may remain in source for research reproduction but must be identified clearly as unsupported for reliability-sensitive operation. Its existing tests, CI, hardware interlocks and archived failures stay intact; it is not silently removed or represented as qualified.

## Prospective core-only acceptance criteria

1. Exact reviewed release source commit is pinned. Any code or packaging change requires fresh affected qualification.
2. Linux and macOS complete core regression, supervisor repeats, installed CLI smoke, wheel build/fresh install and dependency checks.
3. All 102 golden arrays and deterministic records match; V1 canonical outputs and figure artifacts remain byte-identical; M013–M016 archived evidence is reproduced without opening locked cohorts.
4. Historical evidence and hash manifests are unchanged, except the three exact explicitly authorized active-file hash transitions documented by M026. No blanket preservation exemptions.
5. User-facing quickstart, README, package description and release notes explicitly label the SDK backend experimental, and surface its macOS Intel timeout and recording prefetch limitations. Include installation/runtime isolation and the existing hardware interlock.
6. Scientific claims distinguish engineering passes from inconclusive or negative findings: adaptive MPC did not beat PI on the tested development set, M013/M014 are inconclusive, M015 cue-access gate failed with retention unrun, M016 PI worsened mean absolute tracking error versus no pulse. No living-neuron or hardware evidence exists.
7. An independent maintainer review explicitly approves this *new* core-only support boundary before any merge, release tag or public publication. The original full-V2 gate remains HOLD.

M026's exact-head successful Linux/macOS workflows are relevant prior evidence; this review document is **not itself an executed core-only release qualification**. Recheck the exact final publication candidate and release-facing wording if modified.

## Open risks and deferred work

- SDK producer scheduling remains intermittent and unresolved, including no supported upstream producer request-load timestamp on the failed wait. Track separately and seek upstream support or a minimal external reproducer.
- The personal-style refactor remains on HOLD due to MEA/reservoir latency regressions and uncertain FIR/ARX gates. It is not required for this scoped core release.
- M023–M025 are scientific designs/diagnostics, not confirmation of learning, reservoir memory or control improvements.

## Authorization boundary

The earlier scope-review campaign authorized proposal preparation only. The final closure instruction of November 7, 2026 prospectively authorizes this core-only boundary and conditional merge, tagging and publication after every mandatory core gate passes. PR #5 had already been merged when this campaign inspected remote state. This authorization leaves numerical tolerances, scientific evidence, SDK tests and hardware interlocks intact. A failed mandatory core gate still requires publication HOLD.

## Evidence

- M026: https://github.com/adithyakupad/neuromancer/actions/runs/42325130927
- SDK matrix: https://github.com/adithyakupad/neuromancer/actions/runs/42325130966
- Original M019 failure: https://github.com/adithyakupad/neuromancer/actions/runs/42183363096
- M026 release options: https://github.com/adithyakupad/neuromancer/blob/release/v2-0-final-integration-evidence/reports/V2_RELEASE_DECISION.md

## Release-document review, subsequent CI

The proposed user-facing disclosure text is [V2 core release notes draft](V2_CORE_RELEASE_NOTES_DRAFT.md). Those notes retain the original supported/experimental distinction and all negative scientific conclusions.

The documentation-only scope review branch itself reproduced a **macOS Intel SDK CI failure** at https://github.com/adithyakupad/neuromancer/actions/runs/42333658869 while Ubuntu SDK passed. This is consistent with the existing unresolved intermittent reliability blocker; failure subtype has not yet been independently classified from the retained artifact. Do not characterize the documentation branch as universally CI-green. Core-only publication would require separate explicit approval of the revised release gate and confirmation that core tests, package integrity and reproducibility still pass. This does not alter the full-SDK HOLD.

## Final closure qualification boundary

Current baseline main is `db4485613cba8128ee643159b25ef29523ca6c95`. The final hardening branch preserves version `2.0.0rc1` and adds deterministic regressions for the merged suspend fixture synchronization. Its finite qualification plan is [recorded here](../reports/engineering/FINAL_CORE_CLOSURE_PLAN.md).

Publication run 42428618054 failed strict M014 archived-prediction reproduction on Linux and macOS. The Linux maximum absolute discrepancy was `4.99600361e-16`. The existing zero-tolerance assertion remains mandatory. Historical artifact integrity and exact recomputation are assessed separately. The failure blocks publication even if the discrepancy is consistent with floating-point implementation differences. No tolerance change is authorized by this closure campaign.
