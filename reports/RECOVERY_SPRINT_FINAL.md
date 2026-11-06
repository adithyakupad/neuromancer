# Operation Recover final handoff

## Decisions

| Mission | Engineering | Scientific | Release |
|---|---|---|---|
| M020 SDK producer scheduling | PARTIAL, boundary preserved and trace qualified on completed sessions | NOT RUN | SDK HOLD |
| M021 HDF5 extent | PASS, lifecycle defect fixed and original matrix qualified on both hosts | NOT RUN | Recording candidate reviewable, SDK HOLD |
| M022 personal style | PARTIAL, exact behavior and tests passed, performance gate failed | NOT RUN | HOLD |
| M023 reward mechanism | PASS for deterministic arithmetic | NOT RUN for fresh neural study | Research HOLD |
| M024 cue access | PARTIAL, development proposal without acquisition or cost qualification | NOT RUN | Research HOLD |
| M025 controller mechanism | PASS for deterministic model | NOT RUN for independent closed-loop efficacy | Controller HOLD |

The original release candidate remains unchanged at
`70e976c1e990db2fbbc88f786b5d7c06a691aa70` on
`release/v2-0-research-candidate`. Core package and scientific
reproducibility qualify independently. Publication remains HOLD under
the existing mandatory SDK gate. No release scope change was applied.

## Completed recovery

- **SDK producer scheduling.** The standalone diagnostic completed
  256 M020 windows across Linux and macOS Intel with no frame timeout.
  M019 still establishes that a published frame request can wait
  without a producer callback. Successful producer phase traces
  cannot identify the failed request-load or dispatch event. The
  minimal standalone fixture and byte-checked disposable SDK trace
  are ready for an upstream diagnosis. No change was made to the
  SDK's internal 100 ms or NEUROMANCER's 120 s supervisor limit.
  [M020 diagnosis](engineering/M020_SDK_PRODUCER_DIAGNOSIS.md)
- **Recording extent.** SDK iterator exhaustion can request an
  additional 500 frames after all sixteen windows were consumed.
  Before-exhaustion and frame-bounded recording passed 3/3 on each
  host with exact endpoints. The minimal repair stops the recording
  during the final yield and checks expected and actual endpoints
  in the original HDF5. The full repair matrix independently
  reproduced 144 windows, 28 receipts and nine exact HDF5 endpoints
  per host. The original timeout, past extent failures and PI
  tracking result are preserved.
  [M021 result](engineering/M021_RECORDING_EXTENT.md)
- **Style.** All 24 processes reproduced 102 arrays and deterministic
  records exactly. Planner and PI met the new timing gate. MEA p95
  ratio 1.362 and reservoir p95 ratio 1.284 exceeded 1.20, and FIR and
  ARX were inconclusive at the gate. Peak RSS passed. Style regression
  passed 228 tests. No change was integrated from the 18-file branch.
  [M022 report](https://github.com/adithyakupad/neuromancer/blob/refactor/recover-performance/reports/engineering/M022_STYLE_PERFORMANCE.md)

## Scientific recovery

M023 separated signed mean reward, reward–eligibility alignment and
trace decay. With a fixed eligibility vector, exact balanced reward
permutations produced signed means from −2 to +2 around zero, compared
with an unmodulated mean of +1. The proposed controls distinguish
cold-start and timing mechanisms. This does not explain the historical
two-network ranking. Existing training rewards averaged −0.5625 and
−0.125 on the two reward-modulated networks. The archive has no
trial-by-edge eligibility vectors to separate signed reward bias from
edge-specific alignment.
[M023 design](https://github.com/adithyakupad/neuromancer/blob/research/recover-designs/docs/research/M023_PLASTICITY_DESIGN.md)

M024 now requires comparable cue-end encoding before running retention.
Its design separates structural accessibility, effective evoked signal
and sham-calibrated firing-rate matching. No fresh neural trajectory
was collected. The old cue-access gate stays failed.
[M024 design](https://github.com/adithyakupad/neuromancer/blob/research/recover-designs/docs/research/M024_RESERVOIR_DESIGN.md)

M025 reproduced the 1/4 spike alternation and 1.50 PI MAE versus
1.00 no-pulse MAE in a deterministic quantized plant. At target two
the nominal predictor chose no pulses and matched 1.00. Under
gain-one mismatch it lost to PI, 1.00 versus 0.50. At target three
it used 23 pulses versus 12 for nominal PI. This is a tracking-cost
and dose tradeoff in a declared synthetic model, without SDK or
biological efficacy inference.
[M025 design and results](https://github.com/adithyakupad/neuromancer/blob/research/recover-designs/docs/research/M025_CONTROLLER_DESIGN.md)

## Provenance and scope

| Track | Branch | Tested revision or frozen artifact |
|---|---|---|
| Unchanged V2 release | release/v2-0-research-candidate | 70e976c1e990db2fbbc88f786b5d7c06a691aa70 |
| SDK diagnostics | engineering/recover-sdk | d3ac56bd7ae0e48c82849c82723f1c0048a0353f |
| Recording repair | engineering/recover-recording-contract | 35f338dc52adc3ea19c2268dd019c05ce51ca05a |
| Style benchmark | refactor/recover-performance | archive f8676e5af1c200e3e8a4f14679eda89663f9b72a, tested f5703ce0 vs 4ec26248 |
| Test-only atomic PID marker | engineering/recover-core-fixture | c91cd4d5e2884a6f03333118762ffe30573e7228 |
| Research design | research/recover-designs | 8d975c1cfb8716a2026d0add04fd27f6744adabc |

On the recording repair, independent V1 reproduction matched canonical
numerical outputs and figure hashes in 156.442 s. M013/M014 summaries
matched and the V2 verifier checked 38,721 preserved paths in 9.115 s.
All supervisor stages had verified cleanup. The repair did not alter
`src/`, `tests/` or any historical evidence. The exact-head Linux wheel
`neuromancer-2.0.0rc1-py3-none-any.whl` SHA-256 is
`b6e0255f04746e68b51be040a984d250ba021d57629903628344e1b8fa9052dd`.
All 42 unpacked member bytes match the archived release wheel. The
Linux core workflow verified the installed imports, dependency
integrity, supervisor repeats and CLI. The original recording-repair
macOS core workflow built and installed the wheel, then logged 228
passing test calls plus an evidence-finalizer teardown error. The
worker was intentionally cancelled by a persistence-failure fixture
and left an empty PID marker. Its authoritative supervisor record
shows verified cleanup and a reaped leader. A separate test-only
atomic marker change passed 59 local supervisor and clock tests.
Both SDK workers on that candidate reproduced 144 windows and 28
receipts independently, but both hosted SDK workflows failed at
the protected fixture hash. Historical fixture bytes and the
preservation manifest remain intact. The combined candidate is HOLD. No hardware, locked cohort,
main merge, tag or public release occurred.
[Checksums and evidence](engineering/evidence/recover)

## Maintainer release-scope decision

The core wheel already installs without the CL SDK. A future
prospective scope decision could qualify the pinned core wheel and
V1/V2 archive reproduction separately, then offer a separately
installed, simulator-only SDK experiment marked macOS Intel
reliability unqualified. This would require independently reviewed
release criteria, an explicit boundary and clean package/CI evidence
for the scoped core, fail-closed SDK activation and accurate docs.
The existing combined V2 release gate remains in force. This report
does not implement the scope change or authorize publication.

## Before the application

Use the preserved negative findings and the recording repair as the
defensible case studies. Explain what the frame request snapshot
established and what a producer request-load timestamp would add.
Derive why exhausting a generator can change an HDF5 endpoint without
changing any consumed window. Explain why bootstrap resamples whole
process pairs and why equal ASTs do not prove timing equivalence.
Derive the signed reward–eligibility covariance, identify the
cue-access confound, and explain why a target inside the actuator's
amplitude range can still favor no pulse under pointwise absolute
error. Do not present these synthetic fixtures as hardware results.

## Exact hosted gates

| Source | Linux substrate | Linux/macOS core package | Linux/macOS SDK |
|---|---|---|---|
| Standalone diagnostics d3ac56bd | PASS | PASS / PASS | Diagnostic PASS / PASS |
| Recording-only repair 35f338dc | PASS | PASS / FAIL, PID evidence teardown | Original matrix PASS / PASS |
| Atomic fixture follow-up c91cd4d5 | PASS | PASS / PASS, 228 tests per host | FAIL / FAIL, protected fixture hash |

On the atomic follow-up the full installed core regression, traced
supervisor checks and CLI passed on both platforms. Both SDK data
runs and independent HDF5 checks passed, and the hosted source
preservation assertion failed on both. No further run or manifest
waiver was used. The exact recording candidate remains independently
reviewable, while the combined candidate and V2 publication remain HOLD.
[Recording-only core CI](https://github.com/adithyakupad/neuromancer/actions/runs/42298039845) ·
[Atomic follow-up core CI](https://github.com/adithyakupad/neuromancer/actions/runs/42299151759) ·
[Atomic follow-up SDK CI](https://github.com/adithyakupad/neuromancer/actions/runs/42299151853)
