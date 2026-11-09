# M029 remaining portability evidence

The remaining-stage implementation was hosted at `c075cad66889e5dd3e7bcc4b32968046448ad08f`. Its source files are byte-identical in final verifier source `ee2c519d62188dc234d0cce9fb31dd2efe911277`. Hosted evidence belongs to the former SHA. Each platform used one 240-second supervisor for the original remaining stage. The run retained every substage verdict. The Linux and macOS stage verdicts are **FAIL**. [Hosted run 42537995017](https://github.com/adithyakupad/neuromancer/actions/runs/42537995017).

| Obligation | Local arm64 | Hosted Linux | Hosted macOS Intel |
| --- | --- | --- | --- |
| Exact protected historical paths | 38,721 | 38,721 | 38,721 |
| Golden outputs with exact dtype, shape and bytes | 102/102 | 47/102 | 47/102 |
| Golden outputs covered by exact checks or operation-derived certificates | 102/102 | 102/102 | 102/102 |
| Uncovered golden records | 0 | 0 | 0 |
| Canonical V1 tables and summary bytes | 4/4 | 4/4 | 4/4 |
| V1 observed event identities, bins and counts | 23,484,884 events | 23,484,884 events | 23,484,884 events |
| M013 fitted design condition bounds | 10/10 | 10/10 | 10/10 |
| M014 prediction/lag archive certificates | 176/16 | 176/16 | 176/16 |
| M015 reduced scalar trajectories | 8/8 | 8/8 | 8/8 |
| M016 saved recording cases | 9/9 | 9/9 | 9/9 |
| Original complete V1 model and policy audit | PASS | FAIL at model state digest | FAIL at model state digest |
| Remaining-stage wall time | 87.383 s | 41.466 s | 116.594 s |

## Mathematical checks

- **Fixed regression.** A supplemental manifest freezes the exact generated binary64 input witnesses for the initial predictive, online FIR and AR/ARX fixtures. They were recorded after reproducing the historical reference coefficients, covariance or AR/ARX forecasts byte for byte on local arm64. The historical golden arrays remain the acceptance reference. Enclose `A = Z.T Z + D` and `H = Z.T Y` in the original binary64 model. For each native and reference approximation, certify `eta = ||I - A B||∞ < 1` and derive an inverse-norm bound from `||B||∞ / (1 - eta)`. Coefficient errors follow from the enclosed residual `H - A theta`. Covariance errors use the inverse residual. The hosted initial coefficient comparison radii were 6.424523e-12 and 6.424615e-12. Hosted covariance comparison radii were 8.417442e-13 and 8.417443e-13.
- **SVD and conditioning.** The original M027 reconstruction and polar orthogonality certificate supplies Weyl bounds for singular values. Full-rank fixtures require a positive lower bound above the original numerical rank threshold. The C02 design uses its exact zero and repeated columns to establish rank 11, with a separately certified reduced design. Derived condition intervals use outward ratios. The Gram interval includes a norm bound for its operation-derived radius. Native and archived condition diagnostics must lie inside the computed intervals.
- **AR/ARX.** Certify each of the six AR, ARX and shuffled fits against the fixed augmented least-squares design. Derive a companion spectral-radius interval by bounding the inverse and residual of a computed diagonal similarity in real block form. Gershgorin disks give an upper radius and isolated disk components give a lower radius. Each reported diagnostic must lie in that interval, with the entire upper bound below the original 0.999 guard. Propagate lag uncertainty through all 50 forecasts and enforce the original 100 Hz bound.
- **FIR and adaptive forecasts.** The three 100-step fixtures and six 50-step online fixtures use fixed or refitted normal equations, continuous RLS information updates and a positive denominator lower bound. BIAS uses the original scalar gain and intercept operation order with outward uncertainty. Original event counts and states are compared where discrete. The 250-bin fixed and RLS controller tests match every delivered command and recorded event exactly. The ten feedback forecast checks use the identical archived observation and receipt history.
- **Planner and graph.** The five original 625-candidate fixtures certify predictions, tracking and total objective through original lag arithmetic, including exact bank, fixed objective terms, chosen policies and original tie-breaks. Graph indices and delays are exact. The floating graph weights are certified from the frozen random stream and affine plus unit-conversion arithmetic, enclosing separate and fused rounding paths. Spike indices, timestamps, observations, projected actions and constraint outcomes keep their exact checks.
- **Saved studies.** M013 preserves exact scientific rows and outcomes, with a spectral certificate for its ten condition diagnostics. M014 keeps every original analysis assertion except the two floating dot comparisons, which receive operation-derived enclosures and exact class checks. A threshold-crossing interval can pass only with a proof that all binary64 partial sums are exact at the threshold. The largest hosted radius was 4.645e-14 and neither platform needed that exception. M015 replays all eight saved scalar trajectories with exact spike and current traces, then verifies the original scalar-versus-Brian comparison. M016 uses the pinned SDK reader to check nine saved recordings, with exact receipt and event reconciliation.

## Open V1 model and policy proof

The original V1 full study audit compares a SHA-256 of the coefficient array, covariance and scalar bias inverse after every recorded update. Both hosted attempts stop at that assertion in the first trial. This is the expected failure mode of the legacy exact-byte gate under different floating evaluation paths. The local reference audit passed all 384,000 hashes and 4,800,000 candidate scores. The canonical V1 metrics and the independent event audit both passed on the hosted platforms.

The continuous RLS certificate is a separate checked obligation. It does not cover every model family, per-bin prediction, and policy assertion that the original full study audit reaches after its digest gate. A portable substitute for that full audit remains incomplete. Its archived bytes, exact failures and all original outputs remain in the record. The required replacement is a continuous state and forecast proof for the affected archived paths with exact policy reconciliation, followed by a complete run inside the existing remaining-stage budget.

The scientific outcomes are unchanged. V1 adaptive MPC superiority over PI remains **FAIL** at 13.12921875 versus 11.46875 Hz·s, with fixed MPC at 18.9778125 Hz·s. M013 reward-modulated superiority and M014 recurrence-specific memory remain **INCONCLUSIVE**. M015 cue access remains **FAIL** and retention **NOT RUN**. M016 PI tracking improvement remains **FAIL** at 1.50 versus 1.00 spikes per bin. Biological validation remains **NOT RUN** and physical hardware execution **NONE**.
