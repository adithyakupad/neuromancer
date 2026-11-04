# Proposed V1 research release

**Suggested title:** NEUROMANCER v1.0.0 — In Silico Neural Dynamics and Closed-Loop Control

**Suggested description:** A reproducible simulation research platform for constrained neural stimulation, partial spike observation, transparent system identification and causal feedback experiments. Includes a 1,000-cell Brian2 E/I LIF substrate, FIR/RLS and PI/predictive baselines, deadline-aware process supervision, numerical evidence and preserved negative results. In the frozen development comparison, adaptive predictive control improved on fixed predictive control but did not outperform PI. No biological, plasticity, held-out controller-generalization or hard-real-time hardware validation is claimed.

## Included

- Pinned Python 3.12 research environment and installable wheel.
- Causal stimulation/observation interfaces, deterministic replay contracts and common-noise comparisons.
- Transparent identification and controller implementations with explicit physical units.
- Complete primary evidence: 20 trials/260 branches; separate faults: 3 trials/24 branches.
- Network-level uncertainty, all unfavorable outcomes, source/configuration/seed manifests and evidence-only reproduction commands.
- Full regression suite and CI configuration. Actual M007 hosted results, not configuration alone, determine the CI gate.

## Main result

Post-loss IAE (Hz·s): PI 11.46875, RLS-MPC 13.12922, fixed MPC 18.97781. RLS's mean within-network relative benefit was −14.63% versus PI and +30.60% versus fixed MPC. The required adaptive-superiority conjunction **FAILS**. Validation and locked controller cohorts remain unopened; M006 HOLD.

## Publication status

This is a suggested future release, not an existing tag or GitHub release. The M007 audit originally inspected package metadata version **0.2.0** and no LICENSE file. Release-preparation changes now set package metadata to **1.0.0** and add an **MIT LICENSE** on a dedicated branch. The release-preparation commit `abd811a053e10ad7ee5126efbc95fefd73e55c8d` passed Linux/macOS hosted CI, and its wheel was built and inspected again during FINALIZE & OPTIMIZE. Publication still requires final maintainer authorization. Scientific evidence is unchanged. Neither issue changes the measured scientific results.

See the [M007 audit](../reports/M007_FINAL_RELEASE_AUDIT.md), [scientific limitations](V1_SCIENTIFIC_LIMITATIONS.md) and [reproduction guide](V1_REPRODUCIBILITY.md). No merge, tag, locked experiment or publication follows automatically.
