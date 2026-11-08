# M027 numerical portability certificate

## Scope and source

The input evidence is `aef7e04dd0132b42a431bbb3f59ba802d0561224`; the preceding tested verifier is `8591dc6e266aae429e3f19ba1b06723898b446a0`. Work is on `engineering/m027-numerical-certificate`. The prospective plan is committed at `713487fe`. Initial implementation is `551d0b09`, initial hosted source `70073198e4c6bd290a8ca5fe8261dfbd06e9ba45`, and final soundness-guard source **`88b6e94d7e5db572ddc8a954f46e1dec7f9b3d4f`**.

No file in `src/neuromancer/` changes. Scientific/controller arithmetic, random generators, data, production supervision, clock domains, candidate set, objective and the 1e-12 tie rule are unchanged. No scientific cohort is acquired. The original strict failures and all preceding reports are preserved. A certificate is verification code, not a new RLS controller.

## Investigation order

1. **Dependency-aware intervals:** the original componentwise recurrence repeatedly loses the dependence among covariance, gain and residual. Taking absolute values of each dependency does not preserve the stable cancellation in RLS. Its previous rejected planner choice is not evidence of a changed nominal action.
2. **Matrix center/radius:** the original verifier already uses this representation. Merely vectorizing those same componentwise radii cannot remove wrapping. Profiling also shows large candidate/time/channel arrays dominate its cost.
3. **Affine/structured errors:** unrestricted affine symbols for every rounding operation would grow with 128,000 updates. Dropping symbols without an enclosing remainder would be unsound. Instead, retain the fixed information equations and a structured dual projection for each prediction query.
4. **Information form:** algebraically exact information equations are suitable as a *verification reference*. Production remains covariance-form RLS, including its original symmetrization and update order.
5. **Residual certification:** independently bound each computed/archived state relative to the same continuously accumulated ideal system. This avoids recursive state-radius amplification.
6. **Tighter reductions:** replace the verifier's full interval array of 625 x 100 x 4 candidate predictions with equivalent horizon-mean linear queries, and separately bound the original planner's floating evaluation. The native planner still evaluates every candidate in its original order.

## Information equations and validity

Let `lambda` be the actual binary64 constant `.999`, `z_k` the fixed standardized input row, and `v_k` the completed rate minus the fixed output mean. Define exact-real equations from the exact archived initial binary64 state:

```
S_0 = P_0^-1
h_0 = S_0 theta_0
S_k = lambda S_(k-1) + z_k z_k.T
h_k = lambda h_(k-1) + z_k v_k.T
```

`S` has shape (41,41), `h` and `theta` (41,4), and `z` (41,1). The ideal reference is `theta*_k=S_k^-1 h_k`, `P*_k=S_k^-1`. Existence is certified, not assumed. Eligibility uses the original completed-observation/update count; skipped observations do not enter these equations.

For approximate initial inverse `A` and `R=I-A P_0`, a certified `eta=||R||inf<1` implies

```
||P_0^-1-A||inf <= eta ||A||inf / (1-eta).
```

The inverse enclosure initializes `S` once. `h_0` is formed from that same enclosure and exact initial coefficients. Every subsequent multiplication/addition carries an operation-derived radius. No archived checkpoint resets `S`, `h`, their radii or the update count. Initial boxing loses some correlation and remains conservative.

At any bin choose the actual computed covariance `B` only as an approximate inverse. For a certified `eta=||I-S B||inf<1`,

```
||S^-1||inf <= ||B||inf/(1-eta)
r = h-S theta
||theta-theta*||inf <= ||S^-1||inf ||r||inf
||B-P*||inf <= ||S^-1||inf ||I-S B||inf.
```

All residual evaluations include interval input errors and reduction roundoff. Both computed and archived states refer to this same system. Triangle bounds compare dense coefficients/covariance. These are a posteriori certificates, not assertions that any rounded path is the exact ideal path. The native state is checked at every update; archived dense states and planner coefficients are checked wherever retained. Digest differences are reported separately, never relabelled byte equality.

The coefficient bound is applied separately to each of the four output columns. The quoted maximum coefficient radius is an entrywise bound over those columns, not a sum over outputs. The covariance norm bound is also a conservative bound for every covariance entry.

In particular, a stored inverse need not be bit-symmetric. The exact information reference is still well defined, but production's explicit symmetrization is not silently dropped or asserted to be an exact inverse identity in that case. Its effect is included through residuals of the actual production states. Nothing in the proof requires replacing production covariance by the information-form solution.

## Directional prediction bounds

For a row query `L`, do not first multiply a global coefficient radius by `abs(L)`. With `R=I-S B`,

```
L S^-1 = L B (I-R)^-1
||L S^-1||1 <= ||L B||1/(1-||R||inf).
|L(theta_left-theta_right)|
  <= ||L S^-1||1 (||r_left||inf + ||r_right||inf).
```

The bound uses an enclosure of `L B` before taking its row norm, preserving cancellations of C02-null directions. `L` is the exact-real horizon-mean FIR feature row, with its own normalization/reduction enclosure. There are 1,250 horizon rows for 625 candidates and two 50-bin horizons. All four output channels receive the same row, then the rate is averaged across outputs.

This is an algebraic identity of FIR predictions with fixed normalization and histories. It is not a different objective, future input access, different external memory budget, or a reduced candidate set.

## Original planner arithmetic and guards

The center cost always comes from unchanged `predictive_planner.plan`. The error bound separately accounts for its coefficient divisions, forty-term offset product, ten lag accumulations and 200-value horizon/channel reduction. `gamma(512)` exceeds the longest original arithmetic path plus the compressed-query evaluation; the absolute expression envelope accounts for cancellation. It is not chosen from the observed discrepancy.

If a mean prediction differs by at most `e`, its squared tracking contribution differs by at most `2*abs(error)*e+e^2`. Positive sums and final cost additions are rounded outward. Exact equality of the *rounded* dose, switch and exposure arrays is required, so those fixed terms cancel in the comparison; no shorter reduction budget is incorrectly substituted for a separate 100-term dose reduction. Final source adds this explicit check and a changed-component rejection regression. It also requires the absolute expression envelope to certify the existing 100 Hz forecast guard.

The unchanged tie-membership and lexicographic certificate must pass in addition to exact native/archive chosen-index equality and exact four-channel delivered policy equality. A matching nominal action alone never qualifies a choice. No tie threshold is widened.

The offline final guard audited all 2,560 immutable plans: fixed terms matched exactly, 15 immutable bank states sufficed for caching, maximum absolute expression envelope was 26.96242271932907 Hz, and elapsed time was 2.922 s.

## Arithmetic domain

The inherited binary64 model uses `u=2^-53`, outward rounding and `gamma(n)=n*u/(1-n*u)`. Positive reductions include their own rounding and a lower-rounded denominator. Nonfinite inputs/radii, negative radii, unverified inverse contractions, nonpositive denominator bounds and unsupported subnormal products/divisions fail closed.

The compressed planner rejects very small nonzero operands or tracking squares outside its declared normal-arithmetic domain, rather than pretending the relative error model covers gradual underflow. Zero arithmetic is handled explicitly. These are validity restrictions on the verifier, not alterations to scientific limits. Overflow or an uncertifiable normal-domain assumption blocks promotion.

## Fixed fits and SVD

`m027_fit_svd.py` checks exact equality of the retained 1,550 x 41 initial design and targets before using a common fixed regression problem. It encloses `Z.T Z + D` and `Z.T Y` and applies the same residual/inverse proof. The local coefficient comparison radius was 6.4245082552692845e-12; inverse contraction was 6.061482630569287e-11.

For a thin approximate SVD `U Sigma V.T`, certify orthogonality residuals `eta_U,eta_V<1`. Polar factors exist with

```
||U-Q_U||2 <= eta_U/(1+sqrt(1-eta_U))
||V-Q_V||2 <= eta_V/(1+sqrt(1-eta_V)).
```

Bound reconstruction error using `||E||2 <= sqrt(||E||1 ||E||inf)` with outward rounding. Add the polar-factor reconstruction corrections. Weyl's inequality then encloses singular values of the exact input matrix. A finite condition interval requires a strictly positive smallest-singular-value lower bound. A zero lower bound is rejected, not patched by epsilon.

The full initial C02 design is structurally rank 11: inactive columns are exactly zero, active channel columns are paired exactly, and the independent eleven-column design has a certified positive minimum singular value. This avoids pretending a near-zero Gram eigenvalue proves rank. Locally its reduced minimum lower bound was 23.8691877120352 and the full singular-value error bound 2.949211009068685e-10. Ten M013 probe-conditioning diagnostics were also enclosed without altering the archived summaries.

## Independent tests and development results

The first bounded batch passed 13 tests; the second 14; the third 21; the fourth/final 22. Cases include 90-digit Decimal RLS gain/covariance/coefficient evolution, well-conditioned and 1e6-scaled covariance, prediction and candidate objectives, ambiguous ties, zero/subnormal rejection, invalid denominators, analytic singular values, singular-condition rejection and exact immutable cost cancellation. Original arithmetic tests remain enabled. High-precision examples are finite evidence supporting the derivations, not a substitute for their assumptions.

The original 256-update prerequisite and residual prerequisite both passed. The complete first branch passed, as did the complete previously rejected n5/r47 LOSS branch. A predecessor implementation then completed all forty branches in 204.575718583 s under the original 240-second supervisor, with verified cleanup and no watchdog intervention:

- 128,000 bin updates; 2,560 certified planner decisions; 2,600 records including branch completions.
- Maximum coefficient radius relative to the common ideal: 6.319999729988319e-09.
- Maximum covariance radius: 1.074961878572608e-08.
- Maximum candidate-cost radius: 1.8909900758632585e-08.
- Minimum saved nominal selected-versus-other cost gap: 2.2465998319176617e-06.
- Minimum conservative uniform-radius gap: 2.221347890131878e-06. Actual certification uses candidate-specific radii and the original lexicographic rule.
- Zero local recomputed digest differences. This is not generalized to hosted builds.

The local remaining stage passed fixed ridge/SVD, all 102 arrays and records byte-for-byte, original V1 table/figure reproduction, and strict M013/M014 analyses. These are local reference-host results, not proof that every remaining array family has a portable certificate. The current extension does not yet replace every strict golden or archive comparison with a portable proof. Any hosted mismatch there remains uncertified and blocks release.

The final guard was added after the full local predecessor replay; the offline audit checks its fixed-data preconditions without repeating the complete RLS optimization loop. Exact final-head hosted qualification is authoritative. Both preceding and final attempts must remain visible.

## Final hosted outcome

**NUMERICAL CERTIFICATE HOLD.** Both final jobs on `88b6e94d7e5db572ddc8a954f46e1dec7f9b3d4f` stopped at the unchanged 240-second budget. Their remaining fit/SVD/102-array/scientific stages were correctly not promoted. They did not produce a complete terminal numerical certificate. Both retained valid atomic progress and supervisor terminal records.

| Final-source check | Linux | macOS Intel |
| --- | --- | --- |
| Core regression | 275 passed, 0 failed/errors/skipped, 112.601 s | 275 passed, 0 failed/errors/skipped, 320.378 s |
| Arithmetic/phase tests | 34 passed | 34 passed |
| A1 fixed rounds | 18/18 checks passed | 18/18 checks passed |
| Original and residual 256-update prerequisites | PASS | PASS |
| Exact fixed objective tables | 2,560/2,560 | 2,560/2,560 |
| First complete branch | 15.1365 s, PASS | 39.1277 s, PASS |
| Former dependency-growth branch | 15.3582 s, PASS | 32.3022 s, PASS |
| Full archive at cutoff | 15 branches plus partial branch | 9 branches plus partial branch |
| Last retained step | n3/r48 LOSS, step 1300 | n2/r47 LOSS, step 450 |
| Retained planner checkpoints | 987 | 586 |
| Stage elapsed | 239.4204 s | 239.5442 s |
| Final status/cause | DEADLINE_EXCEEDED | DEADLINE_EXCEEDED |
| Cleanup / outer watchdog | Verified / no intervention | Verified / no intervention |

The largest retained planner-checkpoint coefficient bounds were 5.869380878174487e-09 and 5.558239437951402e-09; largest retained cost bounds were 1.882872288273422e-08 and 1.5227626103720805e-08. These are maxima of *retained checkpoints*, not claimed maxima of all post-checkpoint operations before termination. Interrupted stages did not retain full-stage peak RSS or worker CPU totals. Completed branch records retain their own resource measurements.

The initial source `70073198` also timed out on both hosts: sixteen complete branches on Linux and seven on macOS, with partial branches retained. The change in completion counts is not evidence that the final guard caused a particular performance change; these are different source/process executions with uncontrolled scheduling differences. All failures remain failures.

Final [core CI](https://github.com/adithyakupad/neuromancer/actions/runs/42443939147), [numerical/A1 CI](https://github.com/adithyakupad/neuromancer/actions/runs/42443939143), and [substrate CI](https://github.com/adithyakupad/neuromancer/actions/runs/42443939199) identify the exact final source. The [initial numerical attempt](https://github.com/adithyakupad/neuromancer/actions/runs/42443586068) is retained. Both hosts also completed the original 35 M008 process diagnostics with no outer watchdog interventions. Expected resource-failure controls are passing *checks of failed trials*, never successful scientific trials.

No release-qualified status is inferred from local completion or ordinary core tests. See `reports/V2_FINAL_RELEASE_READINESS.md` for the sealed decision and source/evidence distinction. The finite campaign stops here: the next change must reduce information/residual checking cost without weaker bounds or omitted states. Remaining portable coverage of any legacy strict floating checks must also be completed before release.

## Reproduction

From the pinned core environment, create new output directories for every attempt:

```sh
PYTHONPATH=.:src .venv/bin/python scripts/m014_supervise.py /tmp/new-prerequisite-guard 180 .venv/bin/python tools/m027_certify.py /tmp/new-prerequisite --stage 256
PYTHONPATH=.:src .venv/bin/python scripts/m014_supervise.py /tmp/new-first-guard 180 .venv/bin/python tools/m027_certify.py /tmp/new-first --stage first
PYTHONPATH=.:src .venv/bin/python scripts/m014_supervise.py /tmp/new-dependency-guard 180 .venv/bin/python tools/m027_certify.py /tmp/new-dependency --stage dependency
PYTHONPATH=.:src .venv/bin/python scripts/m014_supervise.py /tmp/new-all-guard 240 .venv/bin/python tools/m027_certify.py /tmp/new-all --stage all
```

Promote only after the preceding stage passes. Original strict commands are retained unchanged. Do not interpret an incomplete artifact, native-action match, digest mismatch or a resource stop as full qualification.
