# M029 final release decision

**NEUROMANCER V2 CORE RELEASE HOLD**

The ordered verifier passed all 40 RLS branches locally and on hosted Linux. The Intel worker-count experiment failed the predeclared equality gate after its eight-branch components. The hosted remaining stage certified all 102 golden outputs, but the separate full V1 model and policy audit stopped at its exact model-state digest on both platforms. A complete operation-derived replacement for that V1 audit is still missing.

| Gate | Verdict |
| --- | --- |
| Numerical portability | HOLD |
| Core regression | PASS, 305 tests per platform with zero failures or skips |
| Cleanup | PASS for executed qualification checks. Hosted three-round release confirmation was not reached |
| Historical preservation | PASS |
| Core release | HOLD |
| Full SDK reliability | HOLD |
| Personal style | HOLD |
| Biological validation | NOT RUN |
| Physical hardware execution | NONE |

## Source and evidence

| Item | Exact identity |
| --- | --- |
| Starting M028 verifier | `e2836b355950c62e5dac6f69abee92e2476fe92c` |
| Starting M028 evidence | `e355473f2cfcfa46a449e05f3e0cb905a8714d5c` |
| Initial parallel adapter | `7bc21c69b4292d04de488aa3c74fe7d251dcdd6d` |
| Corrected parallel matrix | `a6d43e7f24bdd948e029da3cd2a32c1d19d6c91e` |
| Hosted remaining-evidence verifier | `c075cad66889e5dd3e7bcc4b32968046448ad08f` |
| Final ordered implementation on `engineering/m029-final-portability` | `ee2c519d62188dc234d0cce9fb31dd2efe911277` |
| Evidence on `engineering/m029-final-portability-evidence` | `6295123e7055b4213af11f2c2a3540f02399cf2d` |

The ordered implementation contains the same remaining-evidence source files as the tested remaining-stage SHA. Separate source IDs are retained because the final exact-candidate release sequence did not qualify. All 38,721 protected paths passed the preservation auditor at the final implementation SHA. The manifest SHA-256 is `f88c41d51355e115863fd1a12dee6901aa4034ac7bf68f86c0c64e622e1719b1`. Original path authorizations, scientific assets and production source match the starting evidence byte for byte.

## Measured qualification

- **Parallel proof.** Local 40/40 in 22.945 s and Linux 40/40 in 73.597 s with four workers, down from 54.78 s and 148.73 s respectively in M028. Each full run certified 128,000 sequential updates and 2,560 exact planner decisions under one 240-second stage deadline. Intel completed both eight-branch components, with 39.546 s at two workers. Three native model trajectory fingerprints and one planner cost bound differed. The Intel four-worker and full stages were consequently not run. The per-branch result table enumerates every expected branch for all six measured platform/source pairs. [Parallel proof](M029_PARALLEL_VERIFICATION.md) · [CPU, RSS and scheduling measurements](M029_HOSTED_PERFORMANCE.md).
- **Remaining portability.** Hosted Linux and Intel each retained exact discrete outputs, 47 byte-identical golden arrays and all 102 covered by exact checks or operation-derived certificates. The stage verified canonical V1 scientific outputs, constraints and counts for 23,484,884 archived events, M013 condition diagnostics, M014 readout classifications, eight M015 scalar trajectories and nine M016 saved recordings. It preserved the exact V1 model hash failure on both hosted platforms. Local strict replay matched all 384,000 V1 hashes and 4,800,000 candidate scores. [Remaining evidence and mathematical checks](M029_PORTABILITY_COMPLETION.md).
- **Cleanup.** Completed and failed process groups are represented in the retained terminal records. All measured worker-count components and completed full stages verified group absence with zero watchdog interventions. The initial adapter failure retained its failed-worker verdict and verified cleanup. Three fresh local A1 rounds passed all 18 checks using the original deadlines. The full hosted regression includes the original process and clock tests. The separate repeated hosted A1 release stage was not reached.
- **Core regression.** The final implementation passed 305 tests per hosted platform with no failures, errors or skips. Linux reported 113.064 s in JUnit and Intel reported 533.806 s. Both jobs passed the original process diagnostics, wheel installation and CLI smoke.
- **Review wheel.** `neuromancer-2.0.0rc1-py3-none-any.whl` is 95,561 bytes. SHA-256 `2b291e698fb72247f581ab00ba53389a01d6cec3a663efa5805ab6358ecaed90`. The fresh install used the pinned core dependencies. All 36 package modules match the final source and the MIT license matches. Installed imports resolved to site-packages. `pip check` and the installed CLI smoke passed from outside the checkout with verified cleanup. The compiler overlay and scientific archives are outside the wheel.

## Hosted evidence

| Check | Hosted evidence |
| --- | --- |
| Initial adapter failure on both platforms | [42537294231](https://github.com/adithyakupad/neuromancer/actions/runs/42537294231) |
| Corrected M028-kernel matrix, Linux full PASS and Intel fingerprint FAIL | [42537331495](https://github.com/adithyakupad/neuromancer/actions/runs/42537331495) |
| Ordered matrix, Linux full PASS and Intel fingerprint FAIL | [42538164882](https://github.com/adithyakupad/neuromancer/actions/runs/42538164882) |
| Remaining numerical families, both FAIL at full V1 audit | [42537995017](https://github.com/adithyakupad/neuromancer/actions/runs/42537995017) |
| Exact final implementation core regressions | [42538164893](https://github.com/adithyakupad/neuromancer/actions/runs/42538164893) |
| Exact final implementation substrate | [42538164850](https://github.com/adithyakupad/neuromancer/actions/runs/42538164850) |
| Existing experimental SDK job on final implementation | [42538164872](https://github.com/adithyakupad/neuromancer/actions/runs/42538164872) |

## Release scope and stopping point

The approved scope remains the core in-silico research prerelease. The SDK 1.0.0 accelerated backend remains experimental with a reliability HOLD. Existing SDK CI results, including failures at earlier M029 sources, remain in the record. Hardware interlocks and limitations remain part of the approved scope. The optional personal-style refactor remains HOLD.

Remote main was `db4485613cba8128ee643159b25ef29523ca6c95` at final inspection. The release promotion gates did not authorize a merge or the `v2.0.0rc1` tag. There is no release URL or published artifact. The wheel checksum above identifies a review asset.

The two open mandatory items are the Intel equality gate for the 40-branch certificate and the full hosted V1 model and policy portability audit. The measured two-worker Intel throughput cannot substitute for a completed qualified run. The historical scientific outcomes remain V1 adaptive MPC **FAIL**, M013 and M014 **INCONCLUSIVE**, M015 cue access **FAIL** and retention **NOT RUN**, and M016 PI tracking improvement **FAIL**.

## Reproduction

From the tested source with pinned core dependencies, build the separate ordered verifier and run the fixed experiment in fresh output directories.

```sh
export PYTHONPATH=.:src
python scripts/m014_supervise.py runs/m029-build-guard 120 python tools/m029_kernel.py runs/m029-build
export M029_KERNEL_DIR="$PWD/runs/m029-build/lib"
python -m pytest -q tests/test_m029_ordered.py tests/test_m029_parallel.py tests/test_m029_portability.py
python tools/m029_matrix.py runs/m029-worker-matrix
python scripts/m014_supervise.py runs/m029-remaining-guard 240 python tools/m029_remaining.py runs/m029-remaining --sdk-python .venv-m029-sdk-reader/bin/python
```

The last command reads the preserved M016 recording files with an isolated `cl-sdk==1.0.0` interpreter. The [per-branch results](evidence/m029_final_release/branch-results.tsv), [resource measurements](evidence/m029_final_release/performance-summary.json), and [artifact manifest](evidence/m029_final_release/artifact-manifest.json) identify the retained evidence.
