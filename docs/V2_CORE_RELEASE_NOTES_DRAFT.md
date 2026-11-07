# NEUROMANCER V2 Core Research Candidate — Release Notes (Draft)

**Release status:** NOT PUBLISHED. **Version:** `2.0.0rc1` (candidate). **Tested source:** `27872242ef2885fec8a04a7c6061584b6cb68c76`.

This is a proposed **core-only in-silico research software** release. It is not a full V2 release with qualified CL SDK reliability. The original full-V2 release remains HOLD. Read the proposed [support boundary](V2_CORE_RELEASE_SCOPE_REVIEW.md) before using the software.

## Supported scope proposed for maintainer approval

- Brian2 spiking E/I LIF substrate, stimulus/observation interfaces and validated command representation.
- FIR/ARX identification, RLS adaptation, PI and predictive-control implementations with auditable causal replay.
- Optional experimental plasticity, reservoir analysis and feedforward controls, with original uncertainty/negative findings retained.
- Historical scientific evidence reconstruction, deterministic verification, supervised worker cleanup and package/CLI smoke.

**Evidence:** M026 source revision passed 231 hosted tests on each Linux/macOS environment, 102 golden arrays, V1 canonical numerical/figure replay, M013–M016 archives and the package installation checks. The SDK simulator matrix also passed its executed cases on M026 source; this does *not* establish intermittent reliability.

## Experimental / unsupported integration

**CL SDK 1.0.0 accelerated simulator adapter:** experiments only, separately pinned environment. A macOS Intel run reproduced a published frame request with a stationary producer write head and no source callback before the SDK's 100 ms internal timeout. Producer scheduling/request handling remains unresolved. Do not use SDK demonstrations for reliability-sensitive operation.

M021 repaired the unrelated HDF5 recording extent issue, caused by an optional final iterator prefetch. Its successful verification does not repair producer scheduling. Keep existing SDK tests and the hardware interlock enabled.

**No** physical hardware access, biological/neural-culture control, clinical validation or hard-real-time guarantee. There are no claims of reliable adaptive-controller superiority or biological learning.

## Scientific findings and limitations

- Historical V1 development set cumulative tracking error: PI **11.46875 Hz·s**, adaptive RLS-MPC **13.12921875 Hz·s**, fixed MPC **18.9778125 Hz·s**. Adaptive MPC did not outperform PI.
- M013 reward-modulated plasticity pilot: superiority **INCONCLUSIVE**. Confirmation **NOT RUN**.
- M014 reservoir delayed recall: recurrence-specific memory **INCONCLUSIVE**.
- M015 feedforward cue-access qualification **FAIL**. Retention experiment **NOT RUN**. Independent reduced scalar LIF numerical fixture verified.
- M016 SDK simulator PI tracking MAE **1.50 spikes/bin**, no-pulse **1.00 spikes/bin**, so control improvement was not demonstrated.
- Historical datasets and locked cohorts have not been overwritten or opened.

## Installation / demonstrations

Use Python 3.12 and the documented pinned core dependencies. See [quickstart](V2_QUICKSTART.md), [reproducibility](V2_REPRODUCIBILITY.md), [scientific limitations](V2_SCIENTIFIC_LIMITATIONS.md) and [evidence ledger](../reports/V2_EVIDENCE_LEDGER.md). The SDK demonstration is **experimental** and must run in the separate pinned CL SDK environment.

## Publication conditions

This draft is for scope approval only. Before tagging or publishing, the maintainer must explicitly approve this bounded support scope, review user-facing documentation/packaging descriptions, and confirm exact-source core qualification. Any code or packaged-member change requires corresponding requalification. Preserve full-SDK HOLD; an intermittently passing SDK job is not a reliability repair.

## Immutable CI evidence

- M026 Linux/macOS core: https://github.com/adithyakupad/neuromancer/actions/runs/42325130927
- M026 SDK executed matrix: https://github.com/adithyakupad/neuromancer/actions/runs/42325130966
- M019 reproduced producer failure: https://github.com/adithyakupad/neuromancer/actions/runs/42183363096
