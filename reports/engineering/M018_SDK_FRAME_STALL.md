# M018 SDK frame-stall diagnosis

**Reliability PARTIAL. Release HOLD.** The macOS Intel failure has been
localized to the interval before the missing source callback in a traced
C0 session. The evidence does not establish why the producer failed to
enter the callback before the SDK's wait expired.

## Revision and evidence lineage

The release source is `70e976c1e990db2fbbc88f786b5d7c06a691aa70`.
The historical diagnostic source is
`bcaa941020fbed00f1afe30d2dce57ea6a556c9a`. The latter is based on the
release tip. The independent style tip
`f5703ce048c30ac4fa050c5b5f9bde3e3b73c296` is outside the release
ancestry. Diagnostic changes live on
`engineering/m018-final-qualification`, with the focused tests and probe
plan at `9fd8c070` and the hosted probe workflow at `8933f52a`.

| macOS Intel run | First incomplete case | Last processed stop | SDK wait target |
|---|---|---:|---:|
| [42172116497](https://github.com/adithyakupad/neuromancer/actions/runs/42172116497) | FROZEN | 5000 | 5500 |
| [42179696188](https://github.com/adithyakupad/neuromancer/actions/runs/42179696188) | C2 | 7500 | 8000 |
| [42179704455](https://github.com/adithyakupad/neuromancer/actions/runs/42179704455) | C4 | No completed bin | 500 |
| [42180155904](https://github.com/adithyakupad/neuromancer/actions/runs/42180155904) | C2 | 1000 | 1500 |
| [42180183794](https://github.com/adithyakupad/neuromancer/actions/runs/42180183794) | C0 | 1500 | 2000 |

Earlier tracing work also produced a verifier failure when it put
diagnostic entries into the scientific stimulation ledger. Separate
JSONL streams resolved that instrumentation issue. A later green run
on the original release SHA leaves its prior macOS failure intact.
[Original revision's later CI](https://github.com/adithyakupad/neuromancer/actions/runs/42175284006)

## Traced boundary

In C0, source open, SDK session open and the first three reads completed.
The host monotonic timestamps below are from the hosted artifact. SDK
frames are a separate 25 kHz clock.

| Host monotonic ns | Event | SDK frame interval |
|---:|---|---|
| 436255374757 | Source opened | |
| 438405652568 | SDK session open returned | |
| 440995869014 | Last source read entered | [1000, 1500) |
| 440996573564 | Last source batch constructed | [1000, 1500) |
| 441003752314 | SDK iterator returned the batch | [1000, 1500) |
| 441004430042 | Application processed the batch | [1000, 1500) |
| 441004542589 | Consumer entered next iterator call | Expected [1500, 2000) |
| 441104827710 | Recording stop began during timeout cleanup | |
| 441606976070 | Recording stop returned | Three processed bins |
| 441609695473 | Source close entered | Last source stop 1500 |
| 441964807164 | Source registration cleared | |

About 100.285 ms elapsed from the next-call trace to recording cleanup.
No target-batch callback entry or exit was recorded. The source close
ledger reported zero pending responses and collisions, with zero stim
commits in the entire session. The partial HDF5 and processed rows were
retained. Reopening the partial HDF5 independently found 1,500 × 64
frames, three spikes and zero stimulation records. The supervisor returned `WORKER_FAILURE`, reaped its worker
and verified cleanup. No watchdog intervention or surviving sampled
descendants were recorded.

The installed SDK 1.0.0 accelerated iterator raises after its internal
100 ms shared-buffer wait. This timeout is separate from NEUROMANCER's
120 s experiment limit. Installed source inspection found that the
producer waits for a request and processes SDK commands before entering
the custom read callback. No supported API exposes an independent
record of producer scheduling and ring request acceptance. The traces
support a missing observed callback entry in C0, and supply no evidence
of a slow callback body, a produced fourth batch, application processing
of that batch or a recording stop that caused the stall. The running
recording process could still affect resource contention. OS scheduling,
SDK request handoff and producer-side work before callback entry remain
plausible. FROZEN, C2 and C4 lack paired source and consumer traces at the
failure point, so the C0 localization cannot be assigned to those runs.
[Official custom-source API](https://docs.corticallabs.com/cl/sim)

## Diagnostic corrections

Trace hooks are opt-in via `NEUROMANCER_M018_TRACE=1`. Source config
passes the opt-in flag to the subprocess. The source trace, application
trace, stimulation ledger and supervisor records have separate paths.
The consumer wrapper now exhausts the SDK iterator normally and rejects
early termination and extra ticks. The untraced path uses the original
SDK iterator. Three focused tests passed. A real local arm64 traced
matrix independently passed every unchanged verifier assertion across
144 windows and 28 receipts. It used 8.294 s supervised, sampled
254,656,512 bytes peak process-tree RSS and saved 15,272,148 recording
bytes. The local stock-SDK control also completed. Both had verified
cleanup with no forced cleanup or observed descendants remaining.
The original limits and scientific algorithms remain intact.

No production reliability repair is justified by these findings. The
stock control and bounded hosted matrix are defined in
[M018 final diagnostic plan](M018_FINAL_DIAGNOSTIC_PLAN.md).

## Bounded hosted comparison

The one corrected diagnostic run at
`8933f52a25a0bf6f9e76b3b7da348617722ea498` passed the full matrix on
Linux and macOS Intel. The separate stock SDK macOS control passed.
The stock probe removed the custom source, application controller
and recorder together, so its success cannot identify which removed
component might contribute to the intermittent failure. It provides
no positive stock-SDK reproduction. A separate already-scheduled
full-trace run also passed at the same historical SHA as the traced
C0 failure. All recorded attempts remain part of the diagnosis.
[Corrected hosted comparison](https://github.com/adithyakupad/neuromancer/actions/runs/42181466722) ·
[Mixed-results companion run](https://github.com/adithyakupad/neuromancer/actions/runs/42180191823)

| Hosted SDK probe | Wall s | Sampled peak tree bytes | Outcome |
|---|---:|---:|---|
| Linux full matrix | 8.082 supervised | 304709632 | 144 windows, 28 receipts |
| macOS Intel traced full matrix | 28.877 supervised | 209403904 | 144 windows, 28 receipts |
| macOS Intel stock control | 5.523 outer | 322199552 | 144 windows |

Both full matrices reopened 15,272,148 bytes of HDF5 output per
platform and exactly matched the archived 144-window frame and event
records, requests, decisions, receipts and PI state after excluding
host timing fields. The stock control and both matrices had no forced
cleanup or remaining observed descendants. The full HDF5 evidence
remains in the linked CI artifacts, with its hashes and selected raw
traces retained in the repository.

The next discriminating measurement needs an independently timestamped
producer scheduling or request-acceptance boundary during a failure.
That requires upstream diagnostics or an independently reviewed
read-only process observation method on macOS Intel. A further green
run alone would leave the observed failure mechanism unresolved.
