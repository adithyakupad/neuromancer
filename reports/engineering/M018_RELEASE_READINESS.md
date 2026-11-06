# M018 release readiness

| Gate | Decision |
|---|---|
| M018 SDK reliability | PARTIAL. The failing C0 callback boundary is localized. The underlying failure mechanism is unresolved. |
| V2 core integration | PASS for the pre-style release source and independent evidence checks. |
| Personal style | HOLD. Exact equivalence passed historically and frozen timing gates failed. |
| V2 publication | HOLD. The release SHA has a retained macOS SDK failure and an unresolved reproducibility blocker. |
| Biological validation | NOT RUN |
| Physical hardware execution | NONE |

## Source and package

The unchanged pre-style release source is
`70e976c1e990db2fbbc88f786b5d7c06a691aa70` on
`release/v2-0-research-candidate`. The diagnostic branch is based on
M018 tip `bcaa941020fbed00f1afe30d2dce57ea6a556c9a`. No reliability fix
or style change was integrated into the release branch.
[Open historical M018 PR](https://github.com/adithyakupad/neuromancer/pull/3)

The exact release source built a fresh MIT
`neuromancer-2.0.0rc1-py3-none-any.whl`, 95,561 bytes and 42 members,
SHA-256
`2d33716b48c7bcaf00847b13a6dfabcfb93ee730a070a58073eed1b742dbe31a`.
Every ZIP member name and decompressed payload matches the earlier
archived wheel. ZIP metadata makes the container checksum differ.
The fresh environment used pinned requirements, passed `pip check`
and imported installed V2, Brian2 2.10.1 and SciPy 1.18.0. The installed
diagnostic CLI smoke passed. The SDK environment was separate and its
recorded dependencies resolved with `cl-sdk==1.0.0`.

## Executed qualification

- Exact release local regression. 228 passed, 46 warnings, 55.05 s.
- Diagnostic-only local regression. 231 passed, 46 warnings, 42.02 s.
- Demo A. The supervised Brian2 feedback and deterministic replay probe
  completed using the original synthetic calibration fixture.
- Demo B. The preserved M013/M014 analysis reproduced exactly from
  scratch copies. The V1 evidence command independently checked model
  and statistics outputs and reproduced canonical numeric/figure hashes.
- Demo C. The full arm64 SDK simulator matrix with corrected tracing
  passed. The original negative PI tracking comparison remains 1.50
  versus 1.00 spikes/bin. Hosted SDK reliability remains a distinct gate.
- Historical numeric archives and locked cohort access remain unchanged.
  No new scientific acquisition was performed.

[Exact release substrate](https://github.com/adithyakupad/neuromancer/actions/runs/42172116537) and
[Linux/macOS package regression](https://github.com/adithyakupad/neuromancer/actions/runs/42172116501)
passed. The original exact release SDK run passed Linux and failed macOS.
A later all-green run on that SHA does not explain the failure.
[Original SDK failure](https://github.com/adithyakupad/neuromancer/actions/runs/42172116497)

## Reproduction

From a clean checkout, use the existing V2 quickstart. On the diagnostic
branch, the extra probe commands use fresh output paths and the isolated
SDK Python:

```sh
PYTHONPATH=src python -m pytest -q tests/test_m018_trace.py
export PYTHONPATH="$PWD/src"
export NEUROMANCER_M018_TRACE=1
"$SDK_PYTHON" scripts/m016_watch.py /tmp/m018-matrix 120 "$SDK_PYTHON" scripts/m016_run.py /tmp/m018-matrix matrix
"$SDK_PYTHON" scripts/m017_sdk_verify.py /tmp/m018-matrix
"$SDK_PYTHON" scripts/m016_watch.py /tmp/m018-stock 120 "$SDK_PYTHON" scripts/m018_sdk_only.py
python scripts/m018_summarize.py /tmp/m018-matrix
```

[Quickstart](../../docs/V2_QUICKSTART.md) ·
[Scientific ledger](../V2_EVIDENCE_LEDGER.md) ·
[Technical defense](../../docs/INTERVIEW_TECHNICAL_DEFENSE.md)

Demo A reproduced all 102 golden arrays exactly by dtype, shape and
bytes and matched the deterministic records. Supervised elapsed times
for A, B and V1 archive reproduction were 5.664 s, 12.079 s and
82.437 s. All had verified cleanup.

[Retained structured evidence](evidence/m018-final) ·
[Prospective style performance design](../V2_PERFORMANCE.md)

The latest corrected diagnostic source passed the full SDK matrix on
Linux and macOS Intel, including the independent macOS stock control.
These are diagnostic checks and do not qualify the unresolved failure
on the release source. [SDK diagnostic CI](https://github.com/adithyakupad/neuromancer/actions/runs/42181466722)

The preserved V1 errors are 11.46875 Hz·s for PI, 13.12921875 for adaptive
RLS-MPC and 18.97781250 for fixed MPC. Adaptive superiority over PI
failed. M013 and M014 remain inconclusive without confirmation. M015
cue-access qualification failed and retention remains unrun. M016
demonstrated synthetic causality and had worse tracking MAE under PI.

On diagnostic source `8933f52a25a0bf6f9e76b3b7da348617722ea498`,
[substrate](https://github.com/adithyakupad/neuromancer/actions/runs/42181466730),
[Linux/macOS package and regression](https://github.com/adithyakupad/neuromancer/actions/runs/42181466715)
and the SDK comparison passed. The closing archival commit retains
the exact tested source identity, reports, artifact summaries and
evidence-only summarizer. It does not request another diagnostic
execution or alter the release ref.
