# Final qualification resolution

## Current decision

**V2 Core release HOLD.** The maintainer approved prospective A1 phase-specific acceptance and the operation-derived portability contract. The implemented portability certificate has not qualified the complete saved study. Scientific algorithms, archives and scientific thresholds remain unchanged. No merge, tag or publication was performed.

The final reviewed implementation source is `8591dc6e266aae429e3f19ba1b06723898b446a0` on `engineering/final-qualification-resolution`. Initial diagnosis source was `c321ea1c8a7a9d52243d493737de9d027addfacb`, based on evidence commit `34f41378b3a986422c953de99017348becf9a6db`. Prospective approval was committed at `87d6d6e1` before the new qualification. Its scientific modules and production supervisor are identical to candidate `5994e64c91cfc81717f4682aab5f2ad8da102a1c`. Evidence and this report will have a separate archival commit identity. The [finite plan](FINAL_QUALIFICATION_RESOLUTION_PLAN.md) preceded the new probes.

The maintainer explicitly selected both prospective alternatives in the conversation. [The approval and fixed budget](FINAL_RESOLUTION_APPROVAL.md) record the selection. Successful diagnostic tests establish observed behavior and arithmetic mechanisms. They do not retrospectively qualify the failed closure run.

## A. Cleanup clock transition

All 25 artifact hashes from the prior closure evidence manifest verified before analysis. The original archives remain unchanged. Regular members were read into scratch without following historical absolute symlinks.

The failing macOS case was reconstructed from raw returned/progress records, worker events and the independent process check.

| Boundary | Time relative to supervisor start |
| --- | --- |
| Parent RUNNING | 0.010109791 s |
| Work cutoff | 0.999840692 s |
| STOP_REQUESTED | 1.001562255 s |
| Descendant imports complete | 1.013930732 s |
| First injected resume | 11.025463477 s in the injected clock |
| TERM | 11.025585672 s |
| KILL | 11.026099473 s |
| Final result | 11.026607045 s |

The clock jump occurred after cancellation began, when the descendant checkpoint finally became visible. Global deadline and selected cleanup end were both `874739667487 ns`. `post_deadline_cleanup` stayed false because the supervisor selected its cleanup policy before the jump. The supervisor sent TERM and KILL, but the jumped clock left no drain time within the selected cleanup deadline. Its last poll did not verify reaping. It returned `CLEANUP_FAILURE`, retaining cause `DEADLINE_EXCEEDED`.

Actual active elapsed time was 1.029750765 s. A later independent `ps` query found no rows for owned PIDs 8871 and 8875. That proves absence at the query time. It does not establish that the supervisor observed/reaped the parent and proved group absence before its contractual cleanup end. There is no contradiction between the failed cleanup-verification status and later process disappearance.

### Promised and observed guarantees

M005A.2 specifies a single experiment deadline, work cutoff reserving .2 s cooperative, .2 s TERM and .4 s final cleanup, process-group signaling, direct-child reaping, explicit failure when group absence cannot be verified, and artifact retention subject to filesystem availability. Grace intervals are upper bounds. It does not guarantee the OS schedules workers or reaps every group within those intervals.

M005A.4 adds the suspend-inclusive clock and an at-most .8 s cleanup-only allowance when cleanup starts after expiry. Experiment success remains prohibited after expiry. Current source chooses that allowance once at cleanup entry. Its documentation describes resume cleanup more generally than this implementation boundary, leaving a policy ambiguity for a jump partway through cleanup. No existing guarantee warrants silently classifying an unreaped group as clean or resetting a cleanup budget repeatedly.

The original real fixture assumes its post-checkpoint injection takes place during running work. Checkpoint existence does not establish that phase. This assumption was violated. The diagnostic tests below reproduce the failure without slow scheduling, filesystem variance or physical sleep.

### Deterministic phase tests

`tests/test_cleanup_clock_phases.py` exercises the actual supervisor with controlled processes, distinct active/continuous clocks and a fixed 1.8 s global budget. The simulated signal effect and its later observation/reaping are separate state transitions.

| Injection boundary | Positive ten-second elapsed jump | Qualified clock error |
| --- | --- | --- |
| Before readiness | DEADLINE_EXCEEDED, NOT_STARTED, cleanup verified | CLOCK_FAILURE, no invented readiness |
| After readiness, before cutoff | DEADLINE_EXCEEDED, existing post-expiry allowance, cleanup verified | CLOCK_FAILURE, bounded emergency cleanup |
| During cancellation | CLEANUP_FAILURE when exit cannot be observed within selected end | CLOCK_FAILURE, bounded emergency cleanup |
| After STOP_REQUESTED, before descendant reaping | CLEANUP_FAILURE with terminated-but-unreaped controlled process | CLOCK_FAILURE, bounded emergency cleanup |
| After cleanup verification, during publication | DEADLINE_EXCEEDED, verified absence retained | CLOCK_FAILURE, publication cannot succeed |

Two further cases verify ordinary cleanup expiry does not reset the original deadline, and normal escalation verifies both parent reaping and group absence. All 12 cases passed locally and on both hosted platforms. They do not substitute for actual process tests. The unchanged complete core workflow separately runs the original real lifecycle/clock tests.

### Cleanup alternatives presented before approval

**A0. Retain the original unconditional real-fixture acceptance.** Keep release HOLD until an implementation/fixture can satisfy it within unchanged budgets. Any production change must first have a deterministic test of a specifically approved promise. The current investigation does not justify a production patch that invents time after a selected cleanup window is exhausted.

**A1. Prospectively approve phase-specific fixture acceptance.** Specify separately that a running-phase suspend case must inject before cancellation and must verify cleanup within its declared allowance. A cancellation-phase exhaustion case must preserve CLEANUP_FAILURE, its original cause and checkpoint, signal its owned group and report the later independent process check. It is an expected resource-failure control, never a successful trial. A missed running-phase setup must be reported as setup failure, not silently substituted by a cancellation-phase pass. No test may choose the favorable interpretation after seeing its status.

A1 received explicit maintainer approval before changing the active fixture or release gate. It preserves a mandatory real-process check of supported running-phase cleanup and visible failures for unsupported timing. All existing cleanup/status/timing assertions remain present. The running-phase fixture now uses a stdlib-only worker and rejects first injection at or after work cutoff. A separate real cancellation-phase control preserves the failed trial status and records post-result reaping. The historical failures remain unchanged. A separate design would be needed if the maintainer instead requires a new post-resume cleanup window during every phase. That change must define how it consumes the existing allowance without repeatedly extending it.

## B. Numerical inventory

The machine-readable inventory contains 306 rows, every one of the 102 immutable golden arrays compared in three retained environments. Each row includes shape, dtype, byte equality, semantic equality, maximum absolute and relative error, zero-reference exceptions, maximum ULP distance, likely generating operation and conditioning/propagation notes. Decision records and available covariance condition numbers are retained separately.

| Environment against historical arm64 reference | Exact arrays | Maximum absolute difference |
| --- | --- | --- |
| Retained local arm64 execution | 102/102 | 0 |
| Retained Linux x86-64 execution | 47/102 | 5.3290705182007514e-14 |
| Retained macOS Intel execution | 47/102 | 7.815970093361102e-14 |

Shapes and dtypes matched in all 306 comparisons. Relative error is undefined when a zero reference becomes nonzero. The inventory marks this explicitly and reports a separate maximum over nonzero references. ULP distance uses ordered finite encodings and normalizes signed zero only for that metric, while byte equality still distinguishes its sign. Distances across zero are diagnostic encodings, not an acceptance tolerance. NaNs/infinities are counted separately. No global relative/ULP threshold was imposed.

The maximum relative errors over nonzero references were about 5.48 and 6.20. These occur in cancellation-sensitive inverse entries near zero. Sign changes in tiny entries cause ordered ULP distances near `8.6e18` despite maximum inverse errors below `5e-18`. This is why neither an array-wide relative threshold nor a fixed ULP budget is adequate.

### Effects on outputs and decisions

- Floating coefficients, inverse/covariance entries, several FIR/online forecasts, shuffled least-squares forecasts, planner predictions/costs and feedback coefficients differ numerically.
- All stored fixed/adaptive/PI action arrays and finite-bank choices match exactly. Controller failure/event records match exactly.
- All tested spike indices, spike times, observations, population rates, reservoir features, cue schedules, eligibility and reward-weight outputs match exactly.
- DAG edge source/destination indices and delays match exactly. Its floating weights differ.
- Stored bootstrap and qualification decisions match. Independently compared V1 trial metrics, timecourses, network qualification CSV and summary JSON from both retained hosted runs are byte-identical to the canonical outputs. The adaptive-superiority FAIL is preserved.
- Full strict evidence verification still fails on recomputed RLS state hashes, and archived M013/M014 exact checks retain their prior failures. Matching outcomes does not erase those failures. No new scientific acquisition was used to assess consequences.

These observations apply to the measured fixtures and saved trials. They do not prove every future network or near-tied controller decision is invariant to floating-point changes.

### Installed builds and operation localization

The diagnostic probe records NumPy/SciPy versions, wheel metadata, Python executable/compiler, build configuration, CPU dispatch report, loaded BLAS/LAPACK paths and binary hashes. Thread-count environment requests are recorded separately from actual thread-pool evidence. No standardized threading claim is made when no pool introspection is available.

| Host | Python | Numerical implementation |
| --- | --- | --- |
| Local arm64 | 3.12.15, Clang 21 | Apple Accelerate, aarch64 NumPy wheel |
| Linux x86-64 | 3.12.16, GCC 15.2 | bundled OpenBLAS, x86-64 wheel |
| macOS Intel | 3.12.10, Clang 13 | Apple Accelerate, x86-64 wheel and different OS build |

All use NumPy 2.5.4 and SciPy 1.18.0. Version pins therefore did not pin the backend or CPU arithmetic. NumPy documents BLAS use for matrix multiplication and LAPACK `_gesv` for `solve`. Its build-report API reports the linked configuration. [NumPy matmul](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html), [NumPy solve](https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html), [NumPy build configuration](https://numpy.org/doc/stable/reference/generated/numpy.show_config.html)

Fixed archived `Z` and `Y` inputs isolate arithmetic from trial randomness. Native `Z.T@Z` differed from the local matrix by up to `2.05e-12` on Linux and `2.27e-12` on Intel. Native `Z.T@Y` differed by about `7.39e-13`. Identical scalar accumulation produced identical Gram/RHS matrices across all three hosts. Native LAPACK solves of those same scalar matrices still differed, local versus hosted, by about `1.3e-16`. Thus both product accumulation and solve implementation contribute.

With archived coefficients held fixed, the tested full candidate-cost arrays match exactly across all three hosts. Native refitting changes cost values. A fixed-state RLS coefficient step matched in this probe, while covariance differed by about `1.69e-21`. This separates coefficient-fitting drift from subsequent covariance arithmetic. It does not replace a complete recursive trajectory check.

The raw 41-column design has rank 11 because of the prescribed C02 allocation. The regularized Gram matrix is well conditioned at approximately 58.05. The independent C02 design condition is about 2.786. Normalized solve residuals range from `5.65e-17` to `1.13e-16`. AR/ARX augmented regularized conditions in the stored fixtures are about 24–31. These results support roundoff propagation without evidence of an unstable fit. Rank-deficient unregularized singular-value diagnostics remain particularly sensitive near zero.

### A second mechanism in random uniform scaling

The new probe also captured the raw generated synaptic weights before Brian2 unit conversion. Among 49,873 values, 4,211 differ between local arm64 and either hosted x86-64 result. The difference is fully reproduced by independent arithmetic.

The installed local `_random_uniform` disassembly contains `fmadd`. A 100-digit Decimal calculation followed by one binary64 rounding reproduces every local value. Separate binary64 multiplication and addition reproduce every Linux and Intel value. The same underlying local unit-uniform draws and fixed affine ranges were used for this check. The maximum raw-weight difference is one ULP, about `7.11e-15 pA`. Brian2's multiply/divide unit roundtrip can produce a two-ULP comparison, about `1.42e-14 pA`.

This establishes an affine-rounding mechanism beyond BLAS. The seeds/roles and graph identities are unchanged. Previously uncaptured raw integer generator states were not independently recovered on both hosted processes, so the investigation does not claim a direct cross-host comparison of every original random bit or noise block. A portable contract must protect random stream identity and define the arithmetic mapping explicitly. It cannot quietly tolerate arbitrary stimulus-dependent random consumption.

## C. Two numerical alternatives

### Alternative 1. Preserve the original exact-byte contract

A diagnostic implementation now performs ordered binary64 multiplication/addition and first-largest partial-pivot Gaussian elimination without BLAS. Its Gram matrix, RHS and fitted coefficients are identical on all three tested hosts. It is intentionally outside `src/neuromancer`.

However, its fitted coefficients differ from the immutable historical reference by up to `1.1102230246251565e-16`. It therefore does **not** satisfy the original contract. Replacing `solve` or rounding its output would not be an honest exact-byte repair.

A fully compliant implementation would have to reproduce the historical reference backend's reduction, factorization, scaling/FMA, unit-conversion and diagnostic operation order, including recursive updates, and match all 102 arrays plus archived state digests. Running a source-compatible backend is insufficient unless its builds and arithmetic are also qualified. Emulating or distributing that entire reference numerical implementation is not completed here. No current deterministic alternative is claimed qualified.

Advantages are immutable byte-level acceptance and readily auditable digests. Costs include a larger implementation/provenance obligation, reference-backend compatibility, potential runtime changes, and the fact that a mathematically more accurate solver can still fail the historical-byte requirement. This alternative keeps HOLD until demonstrated, without rebaselining archives.

### Alternative 2. Proposed numerical portability contract

**Prospectively approved for implementation and qualification. It is not yet a qualified release contract implementation.** It replaces no archived artifact or historical decision. Every original strict result remains recorded. It retains exact requirements for shapes/dtypes, identifiers, labels, split membership, graph indices/delays, input schedules, spike events, observation counts/times, controller choices/actions, receipts, constraint decisions and final scientific gates.

For floating intermediate states, use bounds derived from operations and conditioning, not the largest observed discrepancy. Binary64 unit roundoff is `u=2^-53`. For `n*u<1`, define `gamma(n)=n*u/(1-n*u)`. Under normal finite arithmetic, a dot-product enclosure is

`abs(fl(a @ b) - exact(a @ b)) <= gamma(n) * sum(abs(a_i*b_i))`.

Two implementations can differ by the sum of their enclosures. Any overflow, unsupported underflow model or invalid finite-state assumption blocks certification rather than increasing a tolerance.

For ridge `A=Z.T Z+D`, `H=Z.T Y`, bound product and addition errors using dimensions and absolute products. For a computed solution, use a certified residual bound. If approximate inverse `B` satisfies `||I-B A||_inf < 1` after rounding enclosure, then

`||A^-1||_inf <= ||B||_inf / (1-||I-B A||_inf)`.

For two candidate/reference coefficients evaluated against the same exact `A,H`,

`||theta-theta_ref||_inf <= ||A^-1||_inf * (||A theta-H||_inf + ||A theta_ref-H||_inf)`.

Residual evaluation itself needs outward rounding or a conservative operation enclosure. Bounds on differently accumulated `A,H` must be included. The provided normalized residual measurements are diagnostics, not already-certified interval bounds. LAPACK distinguishes backward residuals from conditioning-sensitive forward error. [LAPACK error measures](https://netlib.org/lapack/lug/node75.html), [LAPACK linear-system error bounds](https://netlib.org/lapack/lug/node80.html)

For prediction `y=mu+z theta`, propagate coefficient/normalization radii and dot/addition roundoff. For RLS, propagate enclosures through `Pz`, `lambda+z.T P z`, gain, residual, coefficient update, rank-one covariance update and symmetrization in the original order. Require a positive denominator lower bound and finite covariance checks. Propagate recursively from the original initialization. Do not reset the error radius to the archived state at each step.

For candidate cost, if a horizon-mean prediction has radius `e`, its squared tracking-error contribution changes by at most `2*abs(mean-target)*e+e^2`, plus reduction roundoff. Preserve the existing 1e-12 tie rule and exact selected action. An interval crossing a choice boundary requires explicit ambiguity handling and cannot authorize a different action. Uniform affine transforms can use a correctly rounded reference with separate/single-round envelopes, while raw generator identities remain protected. Neural threshold discontinuities still require exact spike/observation checks in the qualified fixtures.

The implemented enclosure tracks operation-derived uncertainty through the original RLS order and planner objective. It uses outward rounding, positive-denominator checks and exact action matching. The uncertainty is never reset to archived snapshots. Complete qualification of all trajectories and remaining fitting/SVD/archive checks is blocked by the failed RLS prerequisite described below. This avoids replacing the contract with a blanket `allclose(1e-12)` rule.

## D. Qualification and preserved scope

Initial diagnosis source passed 251 local tests. The first approved implementation passed 259 local tests. The final corrective source passed **260 local tests with 46 warnings** in 50.55 s. The original 237 tests remain enabled. Production scientific modules and supervisor clocks are unchanged. The protected active suspend fixture has one narrowly authorized hash transition. Final hosted results are recorded below.

The pinned fresh wheel built and installed, `pip check` passed, installed imports resolved to fresh site-packages and CLI smoke ran outside the checkout with source overrides removed. Version remains 2.0.0rc1. Final-source wheel SHA-256 is `9aae56dd63916096a296bbe5cb65428c05132abb108bfb2c239bf8d1f9888156`. Its filename is `neuromancer-2.0.0rc1-py3-none-any.whl`, 95,561 bytes, built from final source `8591dc6e266aae429e3f19ba1b06723898b446a0`. Every uncompressed member is identical to the previous retained wheel. ZIP-container timestamps yield a different wheel checksum. No claim of container-byte reproducibility is made.

Historical file verification is repeated before closing. No new scientific acquisition was run. The canonical findings remain PI 11.46875, adaptive RLS-MPC 13.12921875 and fixed MPC 18.9778125 Hz·s. Adaptive superiority over PI remains FAIL. M013 and M014 remain inconclusive. M015 cue access failed and retention remains unrun. M016 PI remains 1.50 versus no-pulse 1.00 spikes/bin. Biological validation remains NOT RUN and physical hardware execution NONE.

SDK reliability HOLD and the optional personal-style refactor HOLD remain outside this work. Existing workflows are retained. An incidental SDK workflow result cannot resolve producer scheduling or clear the numerical/cleanup gates.

The A1 real-process confirmation and the first saved-data portability prerequisite were executed after approval. The complete portable scientific verifier remains unqualified. Earlier byte-exact failures remain historical failures. Complete ordinary core CI cannot substitute for the failed numerical prerequisite.

## Approved implementation and numerical stopping boundary

A1 is implemented with a stdlib-only real worker that publishes completed checkpoint/PID/readiness records. It avoids coupling a clock-phase fixture to unrelated NumPy import latency. The first running-phase injection must precede the original work cutoff. A missed setup latches an explicit failed-setup flag while preserving native clock reads so cleanup can finish. The test rejects the failed setup. No arbitrary sleep or larger timeout was introduced. The original 1.8 s budget, .2/.2/.4 s cleanup phases, six-second watchdog and existing status, reaping and 1.5 s elapsed assertions remain intact.

The protected fixture moved from previously authorized SHA-256 `f78dac7ee7caea0f66bd2d573e648933e765b654c6178a90b2778a7debce5bb0`, through reviewed implementation `1edd4e2a5db202b4626371b2127c9f5b801b534aba8fdea27c711e18c5461128`, to final `ecb6800157398aaf1e8f8887b3e056c83af6310cf8b9fd14497576d70dd98b25`. The original baseline hash `e6ac4422f251c6de7602321c7cc4dc01bffd19a00ff76f8f0e7bcb1bd46eca86` and original manifest are preserved. The authorization and mutation-rejection regression are versioned. Every other protected path retains its original or previously authorized hash. No test-directory exemption was added.

The separate cancellation control retains the supervisor result before any additional observation. Its caller can reap the direct child after the failed result and record that action explicitly. This is late cleanup under the independent outer watchdog, never a retroactive successful trial. Permission errors are retained as inability to verify and polling continues only within the original observer budget. Group absence must actually be established.

`tools/portable_numeric_verification.py` implements nonnegative outward-rounded error propagation for sums, products, division, RLS updates and planner costs. Each candidate includes the same bank, predictions, objective terms and 1e-12 tie semantics. It requires the archived selected action to equal the native selected action and to remain certifiable within the propagated enclosure. It does not modify any controller or use uncertainty to choose a new action.

The fixed 256-update feasibility trajectory passed. A development replay from the uncommitted implementation predecessor of `2fef4327` completed 21 full saved RLS branches and 1,405 dense checkpoints. It stopped on network 5, replicate 47, `LOSS_RLS-MPC`, zero-based bin 3050, because the cost enclosure could no longer certify planner tie membership. At that point the largest coefficient radius was `0.00014769993584128857` and covariance radius `1.2180989947604297e-08`. Native model failure was null. All 70,250 recomputed model digests before that boundary matched on local arm64. The nominal planner choice also matched at the rejected boundary. This demonstrates conservatism/dependency growth in the certificate, not measured control failure. Its 168.27 s stage completed with verified cleanup and no watchdog intervention.

That local development replay preceded the final commit. Finalization changed progress persistence to atomic JSON and clarified result-field scope, without changing its numerical enclosure expressions. Hosted executions, rather than this uncommitted trial, provide the exact-source qualification record.

The implementation deliberately stops rather than loosening a bound, resetting uncertainty to archived state, or accepting nominal action equality in place of the approved certificate. The remaining smallest mathematical repair is a tighter dependency-aware or information-form enclosure that can be justified without changing the controller or acceptance rule. Runtime qualification must also fit the fixed archive-verification budget. This campaign does not start another refinement loop after its prescribed failure.

## Retained implementation failures and limits

- The first focused running-phase setup check incorrectly checked every injected clock read. It failed `short_suspend`. The check was corrected to apply to the first injected resume only, and the failed artifact is retained.
- The first post-result observer encountered PermissionError on a group query. It was corrected to retain the error and continue bounded observation, requiring actual absence. A permission failure is never treated as proof of absence.
- A subsequent local focused run failed the unchanged 1.5 s active-time assertion, recording 2.841171917 s. Cleanup was eventually verified. The continuous-clock lifecycle also contains a long gap after KILL. No independent power/scheduling trace was collected, so the precise environmental pause remains unclassified. This failure is retained alongside later successful full tests and is not relabeled as passing or used to change the bound.
- An initial feasibility JSON field incorrectly named a completed 256-update prerequisite as a qualified full archive verifier. The field was corrected before final source qualification. The original raw output is preserved and is not used as a full qualification result. Final code always reports complete release qualification as false at this stage.

## Final execution record

The exact final source and per-host results, including any resource stops and certificate prefixes, are retained with this report. No unfavorable hosted job was rerun. Old strict scientific verifiers and their archives remain available and unchanged apart from the active fixture authorization hash. Complete portable M013–M016/V1 qualification is not claimed after the RLS prerequisite fails.

Publication remains **HOLD**. The maintainer decisions have been received and implemented prospectively. The remaining blocker is satisfying the approved numerical contract within its declared execution budget. The artifact is a review candidate, not a published release. SDK reliability remains HOLD, personal-style work remains excluded, biological validation is NOT RUN and physical hardware execution is NONE.

## Exact final-source results

All rows below refer to `8591dc6e266aae429e3f19ba1b06723898b446a0`, including the final underflow-domain and setup-containment corrections.

| Check | Linux | macOS Intel |
| --- | --- | --- |
| Complete core regression | 260 passed, zero skipped, 85.94 s | 260 passed, zero skipped, 347.55 s |
| Existing M008 process diagnostics | 35 completed | 35 completed |
| A1 three fixed real-process rounds | 18/18 checks passed | 18/18 checks passed |
| Deterministic clock/arithmetic tests | PASS | PASS |
| 256-update interval prerequisite | PASS | PASS |
| Full 40-branch saved RLS prerequisite | DEADLINE_EXCEEDED, incomplete | DEADLINE_EXCEEDED, incomplete |
| Supervisor cleanup after certificate cutoff | Verified, no outer watchdog intervention | Verified, no outer watchdog intervention |

Final Linux verification retained 425 checkpoints through network 1, replicate 48, `STATIC_RLS-MPC`, completed bin 2050. Six branches completed before that partial branch. It recorded 21,250 recomputed digest mismatches. macOS retained 255 checkpoints through network 0, replicate 48, `LOSS_RLS-MPC`, completed bin 3150. Three branches completed before that partial branch. It recorded 12,750 digest mismatches. These digest differences remain visible while semantic verification is incomplete. No missing terminal certificate was treated as success.

The unchanged 240 s global stage cap stopped the workers at the reserved work cutoff. Reported elapsed stage times were 239.4205 s and 239.5443 s, both with `cleanup_verified=true` and `watchdog_intervened=false`. No resource allowance was extended after seeing outcomes. The fail-closed underflow checks add verification work. These observations are not standardized performance comparisons and do not change any core controller performance claim.

- [Final core package/regression run](https://github.com/adithyakupad/neuromancer/actions/runs/42439784737)
- [Final A1 and numerical certificate run](https://github.com/adithyakupad/neuromancer/actions/runs/42439784762)
- [Final substrate run](https://github.com/adithyakupad/neuromancer/actions/runs/42439784735)
- [Retained earlier approved implementation run](https://github.com/adithyakupad/neuromancer/actions/runs/42438319251)
- [Retained arithmetic-domain correction run](https://github.com/adithyakupad/neuromancer/actions/runs/42439428685)

The source at `5550f912d8c3da377819a4d925bf4a4b667f6d5c` rejects underflow in model/radius arithmetic and avoids manufacturing subnormal radii for exact zero bounds. The last correction latches missed fixture setup instead of repeatedly raising from its clock reader. Both were justified correctness repairs. Their prior test outcomes are preserved. No unchanged failed workflow was rerun to obtain green results.

All 38,721 historical paths verify under the four exact authorized active-path replacements. The manifest itself remains SHA-256 `f88c41d51355e115863fd1a12dee6901aa4034ac7bf68f86c0c64e622e1719b1`. The new mutation regression rejects an additional unauthorized edit to the same suspend fixture.

Raw evidence, all three-platform array rows, decision comparisons, operation probes, source/binary hashes, approval record, failure logs, wheel audit and exact-source CI metadata are retained in [the resolution evidence directory](evidence/final_qualification_resolution). The source-change inventory records 15 paths against the initial evidence base and zero changes under `src/neuromancer/`. A final review checks the source inventory again when sealing the evidence. Earlier artifact identities and negative outcomes remain available through their original branches and manifests.

The fresh final-source wheel installs in an isolated environment, passes dependency consistency and installed imports, and executes its CLI smoke outside the checkout without a source override. Its payload matches the source. No scientific NPZ/HDF5 archives are distributed in the wheel. The resource and numerical failures prevent describing this artifact as release-qualified.

Representative reproduction commands require fresh output directories and the pinned Python 3.12 environment.

```sh
.venv/bin/python tools/final_numeric_inventory.py /tmp/new-array-inventory
PYTHONPATH=src .venv/bin/python scripts/m014_supervise.py /tmp/new-kernel-watch 180 .venv/bin/python tools/final_numeric_diagnosis.py /tmp/new-kernel-probe
PYTHONPATH=src .venv/bin/python scripts/m014_supervise.py /tmp/new-feasibility-watch 180 .venv/bin/python tools/portable_numeric_verification.py /tmp/new-feasibility
PYTHONPATH=src .venv/bin/python scripts/m014_supervise.py /tmp/new-archive-watch 240 .venv/bin/python tools/portable_numeric_verification.py /tmp/new-archive-certificate --archive
```

The final command currently has an unmet qualification gate and must preserve its nonzero/resource-failure outcome. Full portable verification of all remaining fitting, SVD and M013–M016 archive checks was not promoted past the failed RLS prerequisite.

| Final boundary | Decision |
| --- | --- |
| A1 cleanup disposition | Implemented, passing finite hosted phase matrix, earlier timing failure retained |
| Complete ordinary core regression | PASS on final source |
| Full numerical portability qualification | HOLD |
| Overall final qualification | PARTIAL |
| Release publication | HOLD |
| SDK reliability | HOLD, outside this investigation |
| Personal-style refactor | HOLD, excluded |
| Biological validation | NOT RUN |
| Physical hardware execution | NONE |

No further maintainer acceptance decision is pending for A1 or the portability design. The blocker is completing a sound, sufficiently tight and computationally feasible numerical certificate under the approved contract. Publication remains unauthorized while that criterion is unmet. No merge, tag or GitHub release occurred.
