# M026 V2 integration and qualification contract

The review branch starts from
`70e976c1e990db2fbbc88f786b5d7c06a691aa70`. It imports only the
M021 runner repair and the atomic synthetic PID marker repair as
runtime and fixture changes. It keeps the SDK producer diagnosis,
style history, and scientific evidence on their original branches.

| Reference | Verified source revision |
|---|---|
| M021 runner repair | `35f338dc52adc3ea19c2268dd019c05ce51ca05a` |
| Atomic fixture correction | `c91cd4d5e2884a6f03333118762ffe30573e7228` |
| M020 evidence | `c713c6bc0a30cf8696e72e022d33e40b4ec495a0` |
| Style evidence | `f8676e5af1c200e3e8a4f14679eda89663f9b72a` |

The imported runner stops and closes the recording during the final
500-frame yield, after processing the final observation and checking
pending receipts. The loop then exhausts normally. No samples are
discarded. The reopened HDF5 must match the expected final frame,
8000 samples and the observed start. Existing SDK checks independently
reconcile committed stimulation, samples, synthetic spikes, invalid
and expired commands, and process cleanup. The worker fixture stages
the PID record before renaming it. An interruption can leave a staging
file, which the artifact collector retains, while the committed marker
is absent. The qualified clock, deadlines, supervisor and lifecycle
assertions remain unchanged.
[Exact-file provenance authorization](M026_PROVENANCE_AUTHORIZATION.md)

Qualification uses the unchanged hosted substrate, installed package
and regression, and original SDK workflows. The local full regression
is supervised for 180 s, the golden fixture and archive reproduction
stages for 240 s each, and the local SDK matrix for 120 s. Historical
M015 and M016 verification reads archived copies or writes only to
scratch. The frozen SDK and supervisor deadlines remain in force.
No locked cohorts or new scientific experiments are run.

Record one exact-head hosted attempt, including failures and cleanup.
The superseded implementation was dispatched before an independent
collection check found that the plain pytest entry point could not
import the repository's scripts namespace. Retain those runs as
superseded evidence. The corrected test loads the verifier from its
file path. Qualification uses one hosted attempt on the corrected
source, with the existing workflows and all assertions unchanged.
Record executed outcomes and raw artifact hashes on a separate
qualification evidence ref based on the tested integration source.
The integration ref stays at the source SHA actually tested. This
avoids treating a later reporting commit as a qualified release SHA.
See [release decision](../V2_RELEASE_DECISION.md).

## Optional style candidates

Preserve M022's twelve counterbalanced process pairs. MEA and reservoir
tail gates failed, and FIR and ARX remained uncertain. Independent
follow-ups could isolate the formatting-only planner file, then the
named RLS residual or PI proportional/integral intermediates in separate
commits, with exact golden comparison and the same performance gates
on each candidate. The bundled planner and PI measurements do not
qualify an isolated patch. No style code is included in M026.
[Preserved style review](https://github.com/adithyakupad/neuromancer/blob/refactor/recover-performance/reports/engineering/M022_STYLE_PERFORMANCE.md)

## Executed local and numerical checks

The tested source is `27872242ef2885fec8a04a7c6061584b6cb68c76`.
The independent Git comparison found one PID-publication block changed
and exact imported bytes for the worker and runner. The baseline
manifest, package source, workflow definitions and historical evidence
trees are unchanged. The three added cases passed and ordinary
`pytest` collected them. The full host-clock regression passed
**231 tests**, with 46 warnings, in 71.13 s of pytest time and 71.529 s
supervised. The original cancellation, descendant, clock error and
outer watchdog tests remained active.

| Stage | Executed result | Supervised s |
|---|---|---:|
| Exact golden replay | 102 arrays match dtype, shape and bytes. NPZ and deterministic records are byte-identical. | 10.982 |
| V1 evidence reproduction | Canonical numerical outputs, four figures, independent model and statistics checks passed | 154.048 |
| M013/M014 evidence | Both archived analysis summaries reproduced. Strict audit checked 38,721 paths. | 9.425 |
| M015 evidence | 336 trajectories and eight scalar archives verified. Cue-access gate remains HOLD. | |
| M016 evidence | Archived paired receipts, HDF5 and original synthetic spike timing verified | |
| Clean wheel and installed CLI | Dependency check, installed imports and CLI smoke passed | 16.140 CLI |

The fresh `neuromancer-2.0.0rc1-py3-none-any.whl` SHA-256 is
`6f4f84fa8d944449e97d3cd489ea209c7f977fd8ba1752378afdcbb6149dc036`.
All 42 unpacked wheel members match the archived wheel byte for byte.
The local wheel installation was isolated from the source checkout.
The first optional SDK pip check inherited the repository source
path and reported core-dependency mismatches in the separate SDK
environment. The isolated SDK check passed. The first restricted
local PID tests could not establish macOS boot identity. They passed
with host clock access and the fail-closed clock check stayed intact.
The prior pytest entry-point failure and superseded runs are retained
separately from final qualification.

## Exact hosted SDK and recording checks

The original SDK workflow passed on Linux and macOS Intel. Independent
artifact verification confirmed **144 windows, 28 matched commitments
and nine HDF5 endpoints per platform**, each 8000 × 64 raw samples.
Archived deterministic fields match exactly, excluding host timing
fields. The workflow also verified synthetic spike timing and invalid
and expired command rejection. Both hosts reported verified worker
and descendant cleanup with no watchdog intervention. Supervised
wall time was 9.501 s on Linux and 25.814 s on macOS Intel.
Observed peak process-tree RSS was 305,500,160 and 208,801,792 bytes.
The historical M019 failure is unmodified and the producer stall is open.
[Exact SDK workflow](https://github.com/adithyakupad/neuromancer/actions/runs/42325130966) ·
[SDK loop and recording reference](https://docs.corticallabs.com/cl)

The M022 performance run is preserved. Independent AST comparison of
the planner, MEA adapter and reservoir files across original and style
refs found identical ASTs after omitting positions. The formatting-only
planner file is an isolatable candidate. Equal ASTs do not qualify its
latency, especially given M022's MEA and reservoir timing results.
No style source was imported or timed again.

## Reproduction commands

Use fresh output directories and the repository's qualified Python
and independent SDK environments. The main commands were:

```sh
python scripts/m014_supervise.py /tmp/m026-reg 180 python -m pytest -q --junitxml=/tmp/m026-tests.xml
python scripts/m014_supervise.py /tmp/m026-gold 240 python scripts/m017_probe.py /tmp/m026-golden --neural --reference reports/engineering/evidence/m017/golden_final
python scripts/m014_supervise.py /tmp/m026-v1-guard 240 python scripts/reproduce_v1_evidence.py --output /tmp/m026-v1
python scripts/m014_supervise.py /tmp/m026-v2-guard 240 python scripts/m017_reproduce.py /tmp/m026-v2
"$SDK_PYTHON" scripts/m016_watch.py /tmp/m026-sdk 120 "$SDK_PYTHON" scripts/m016_run.py /tmp/m026-sdk matrix
"$SDK_PYTHON" scripts/m017_sdk_verify.py /tmp/m026-sdk
```

M015 access and cross-simulator verifiers ran on scratch copies.
M016 archive verification called the existing verifier in read-only
mode. Raw artifacts and exact revision checksums are retained in
[the M026 evidence directory](evidence/m026).

## Exact-head hosted decision

| Workflow | Linux | macOS Intel |
|---|---|---|
| Substrate qualification | PASS | No job in this workflow |
| Installed package, core regression, supervisor repeats and CLI | PASS, 231 tests | PASS, 231 tests |
| Original SDK and HDF5 matrix | PASS | PASS |

Both core JUnit files report zero failures, errors and skips. The
superseded source's substrate and SDK workflows completed, and its
core workflow was cancelled after the independent plain-pytest
collection defect was identified. None of those runs was substituted
for the corrected revision. Engineering qualification passed on
`27872242ef2885fec8a04a7c6061584b6cb68c76`. The archive branch adds
reports and checksums to that exact source. It is not a new release
revision. [Substrate CI](https://github.com/adithyakupad/neuromancer/actions/runs/42325130932) ·
[Core CI](https://github.com/adithyakupad/neuromancer/actions/runs/42325130927)
