# V2 Core final release readiness — M027

**CORE RELEASE READINESS: HOLD. No merge, tag or publication was performed.**

The final tested implementation is **`88b6e94d7e5db572ddc8a954f46e1dec7f9b3d4f`** on `engineering/m027-numerical-certificate`. Source starts from evidence `aef7e04dd0132b42a431bbb3f59ba802d0561224` and preceding tested source `8591dc6e266aae429e3f19ba1b06723898b446a0`. This closing report and raw artifacts are archived separately; their evidence commit is not represented as an additional tested code revision.

## Decisions

| Mandatory boundary | Decision | Evidence |
| --- | --- | --- |
| NUMERICAL CERTIFICATE | **HOLD** | Final Linux/macOS full stages exceeded their original 240-second cap |
| CORE REGRESSION | **PASS** | All 260 existing tests plus 15 new tests: 275 passed per platform |
| CLEANUP QUALIFICATION | **PASS** | Three six-case A1 rounds per platform; 35 M008 diagnostics per platform; timeout cleanup verified |
| Historical preservation | **PASS** | 38,721 protected paths verified, original manifest unchanged |
| Clean package and CLI | **PASS** | Fresh final-source wheel, pinned dependency install, pip check, installed imports and bounded CLI smoke |
| CORE RELEASE READINESS | **HOLD** | Numerical completion and remaining hosted scientific portability gates are unmet |
| Experimental SDK reliability | **HOLD** | Existing producer scheduling limitation remains outside this mission |
| Optional personal-style refactor | **HOLD / excluded** | Not integrated or revisited |
| Biological validation | **NOT RUN** | In-silico verification only |
| Physical hardware execution | **NONE** | Hardware interlock retained |

Passing checks of deliberately failed resource-control trials do not turn those trials into successful experiments. Final cutoff stages retained DEADLINE_EXCEEDED, their cleanup evidence and partial data. No cleanup failure was relabelled success.

## What improved and what remains blocked

The residual-based certificate resolves the former local dependency-growth rejection at n5/r47 LOSS bin 3050. It continuously accumulates information equations from the exact archived initialization, bounds native and archived residuals, and uses directional prediction queries to preserve nullspace cancellation. Native controller execution and all 625 candidate actions remain unchanged.

The local development predecessor completed all forty RLS branches in 204.58 s with 2,560 certified planner decisions, maximum coefficient bound 6.32e-09 and maximum cost bound 1.89e-08. Its smallest conservative uniform cost gap was 2.22e-06. Local exact remaining evidence reproduced all 102 arrays, canonical V1 outputs and strict M013/M014 analyses. This is a local result, not cross-platform completion.

On the exact final source, Linux retained fifteen complete branches and a partial n3/r48 LOSS branch through step 1300. macOS retained nine complete branches and a partial n2/r47 LOSS branch through step 450. Both stopped at their reserved cutoff, approximately 239.42/239.54 s supervised elapsed, with verified cleanup and no outer watchdog intervention. They did not reach the remaining fit/SVD/golden/scientific stages. No incomplete certificate counts as PASS.

The immediate blocker is computational cost: information accumulation and residual checking consumed about 167 s of each retained hosted prefix. Removing a few seconds of archive/logging overhead cannot supply the needed approximately 2.59x/4.37x throughput improvement implied by those prefix forecasts. These are estimates, not completed full-study runtimes or a proof that all future optimizations are impossible.

A further performance method must retain sound bounds and every state/action check within 240 seconds. If a hosted full RLS gate then passes, remaining floating families still require the approved portable certificate where original strict byte comparisons fail. The current fit/SVD extension covers specified fixed problems and diagnostics; it is not falsely described as universal coverage of every legacy golden family. No new tolerance or acceptance decision is inferred from matching nominal actions.

## Final exact-source CI

- [Core package and regression — PASS on Linux/macOS](https://github.com/adithyakupad/neuromancer/actions/runs/42443939147): 275 tests each; zero failures, errors or skips. JUnit durations 112.601 s and 320.378 s.
- [M027 numerical/A1 — FAIL at the archive resource gate on both hosts](https://github.com/adithyakupad/neuromancer/actions/runs/42443939143): 34 arithmetic/phase tests per host, 18 A1 checks per host, both 256-update prerequisites, full fixed-objective audit, first branch and former dependency-growth branch passed before the full-stage cutoff.
- [Substrate — PASS](https://github.com/adithyakupad/neuromancer/actions/runs/42443939199).
- [Incidental unchanged SDK workflow — executed PASS](https://github.com/adithyakupad/neuromancer/actions/runs/42443939149). This does not resolve the intermittent producer issue or qualify full SDK reliability.
- [Initial M027 attempt — resource failure retained](https://github.com/adithyakupad/neuromancer/actions/runs/42443586068). Its source `70073198` precedes the final explicit fixed-objective/forecast guards. No unchanged failed job was rerun.

Final local regression: 275 passed, 46 warnings, 53.99 s. Warnings are retained in logs; the local set consists of existing Brian2/pyparsing deprecations, not suppressed test failures. Hosted configuration reports also retain optional `pyyaml`/`threadpoolctl` diagnostics. Actual BLAS pool behavior is not claimed verified from environment variables alone.

## Source, evidence and package

Production `src/neuromancer/`, dependency pins, scientific protocols, original verifiers, numerical archives and supervisor/clock behavior are unchanged. New files are verification/profiling tools, independent tests, the focused workflow, plan and reports. No additional historical-path authorization was needed. The unchanged protected manifest SHA-256 remains `f88c41d51355e115863fd1a12dee6901aa4034ac7bf68f86c0c64e622e1719b1`.

The final-source wheel is `neuromancer-2.0.0rc1-py3-none-any.whl`, **95,561 bytes**, SHA-256:

```
1a5c1ba47f913daadbbb03cb7ae96b12375036c2094e8082292e4450123a6754
```

All 36 packaged module files match the source archive. MIT license matches. No NPZ/NPY/HDF5 scientific archives are in the wheel. A fresh environment installed pinned NumPy 2.5.4, Brian2 2.10.1, SciPy 1.18.0 and pytest 9.1.1; `pip check` passed. Imports resolved to fresh site-packages. Installed CLI smoke ran with `PYTHONPATH` removed, including a separate check from outside the checkout, under a 120-second supervisor with verified cleanup. There is no claim of public-asset installation or publication: this is a review artifact.

Raw local/hosted records, failed and incomplete attempts, source hashes, full numerical progress, profiles, JUnit XML, environment metadata, wheel and checksum manifest are in `reports/engineering/evidence/m027_numerical_certificate`. The source and evidence closing commits are separate so documentation does not masquerade as an unexecuted exact-head code qualification.

## Scientific preservation

- V1 PI 11.46875, adaptive RLS-MPC 13.12921875, fixed MPC 18.9778125 Hz·s. Adaptive superiority over PI remains FAIL.
- M013 reward-modulated learning superiority remains INCONCLUSIVE; confirmation NOT RUN.
- M014 recurrence-specific memory superiority remains INCONCLUSIVE; confirmation NOT RUN.
- M015 cue access remains FAIL; retention comparison NOT RUN; reduced independent scalar LIF verification retains its qualification.
- M016 simulated causal I/O remains demonstrated on its executed workload. PI MAE remains 1.50 versus no-pulse 1.00 spikes/bin; no PI superiority is claimed.
- Earlier V0.1/V0.2, M003 model-superiority and short-horizon recovery failures remain unchanged.

No locked cohort was opened and no new scientific experiment was run. Engineering replay and saved-data analysis do not constitute new biological evidence. No biological learning, physical stimulation safety or hard real-time operation is claimed.

## Reproduction and stopping boundary

The ordered commands and derivations are in `reports/engineering/M027_NUMERICAL_CERTIFICATE.md`; component costs, observed ceilings and limitations are in `reports/engineering/M027_PERFORMANCE.md`. Existing strict reproduction scripts remain unchanged. The M027 workflow stops promotion at the first failed stage and always retains artifacts.

The four development batches and two distinct-source hosted attempts are finished. The campaign stops with evidence-complete HOLD. It does not silently enlarge the original stage budget, weaken an interval, drop a branch, reset uncertainty, retry an unchanged source or start a scientific study. Further engineering requires a new bounded verification implementation and fresh qualification, not a release action.
