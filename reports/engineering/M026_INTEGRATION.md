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
