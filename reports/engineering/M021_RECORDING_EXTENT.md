# M021 SDK recording extent

**Lifecycle mechanism demonstrated. Scientific NOT RUN. SDK release
remains HOLD for the independent M020 scheduling issue.**

The final SDK yield covers frames [7500, 8000). On iterator resumption
the accelerated SDK 1.0.0 code increments the tick and requests
another batch before checking loop termination. The requested 8500
can be cleared before the producer observes it, or produce a real
[8000, 8500) batch. Consumer windows still stop at 8000. The
unbounded recorder can include the produced tail through its stop
watermark. Its HDF5 endpoint describes recorded samples rather than
the last application-consumed window. Producer traces show
request_loaded, callback and write phases for that tail on macOS.
That explains why the same consumer workload can produce either
recording extent. It does not explain M019's frame wait.

| Lifecycle condition | Linux recorded frames | macOS Intel recorded frames |
|---|---|---|
| Stop during final yield | 8000 in 3/3 | 8000 in 3/3 |
| Exhaust, wait 30 ms, stop | 8000 in 2/3, 8500 in 1/3 | 8500 in 3/3 |
| SDK stop_after_frames=8000 | 8000 in 3/3 | 8000 in 3/3 |

Each of these 18 sessions verified every channel-0 timestamp sample,
the declared final-frame attribute, the physical HDF5 end timestamp
and ordered spikes at both edges of each bin. The 8500-frame files
retained their two extra fixture spikes. No samples were trimmed.
The fixtures had no stimulation. The historical failed assertions
remain failed observations. This matrix demonstrates the documented
frame-bounded recording option and the timing risk of an unbounded
recording stopped after iterator exhaustion.
[Exact hosted diagnostic](https://github.com/adithyakupad/neuromancer/actions/runs/42297238288) ·
[SDK recording API](https://docs.corticallabs.com/cl)

## Prospective repair contract

A separate candidate from exact release revision `70e976c1` stops
the SDK recorder while the sixteenth yield is active, after processing
the final observation and checking the qualified deadline. The
SDK generator then exhausts normally. Record both expected and
actual final frame and require exact agreement on the intact HDF5
artifact. Manual stop while active avoids the extra request reaching
the recording and preserves early-failure cleanup without an
auto-stop path that can request missing frames. No changes to neural
outputs, pulses, decisions, timeouts or array validation. Failures
remain partial artifacts and cannot pass the original verifier.
Before promotion, run the original nine-case matrix, exact receipt
and HDF5 verification, clean package and regression checks on both
Linux and macOS Intel. This candidate addresses recording only.

## Exact repair qualification

**Engineering PASS for the recording lifecycle. Scientific NOT RUN.
SDK release HOLD.**

Repair revision `35f338dc52adc3ea19c2268dd019c05ce51ca05a` on
`engineering/recover-recording-contract` changed only the active SDK
runner's recording lifecycle. The independent verifier checked 144
windows and 28 receipts on each platform, exact historical deterministic
records, all nine intact HDF5 files with matching endpoints, and
deadline and cleanup evidence. The hosted original verifier also checked
invalid/expired rejection, sample ordering, matched committed
stimulation and designed response timing. The simulator identity guard
ran in every session. Hosted regression tests exercised interlock refusal. Results exclude
host timing fields from the historical equivalence comparison.

| Host | Supervised wall s | Sampled process-tree RSS bytes |
|---|---:|---:|
| Linux | 9.124 | 305901568 |
| macOS Intel | 27.093 | 209190912 |

No deadline miss, outer watchdog intervention, forced cleanup or
observed surviving descendant was recorded. The original M019
frame stall has no established repair. A green run of the recording
candidate does not explain it.
[Original matrix on the repair revision](https://github.com/adithyakupad/neuromancer/actions/runs/42298039421) ·
[Independent verification and raw records](evidence/recover)

The macOS core workflow on the exact recording revision returned 228
passing test calls and one teardown error. The deliberately cancelled
supervisor worker left a zero-byte `pid.json`, which the artifact
finalizer attempted to parse. The preserved supervisor result says
`SUPERVISOR_FAILURE` for the injected progress-write error,
`cleanup_verified=true`, leader reaped with return code −15 before
the unchanged deadline. The failure is independent of recording.
[Failed macOS core job](https://github.com/adithyakupad/neuromancer/actions/runs/42298039845/job/128168267122)

A separately qualified candidate will publish the synthetic worker's
PID marker atomically through a sibling staging file. Cancellation
before publication can leave a staging file for retention, while
the committed pathname is complete or absent. Supervisor code,
deadlines, process ownership, termination checks and test assertions
remain unchanged. This amendment permits one exact-head hosted
matrix after the test-only change, then stops regardless of outcome.

The atomic fixture change is isolated at
`c91cd4d5e2884a6f03333118762ffe30573e7228`. It passed 59 local
supervisor and clock tests. The follow-up Linux and macOS SDK workers each completed
144 windows and 28 receipts, independently matching the original
deterministic records and recording endpoints. The two hosted SDK
jobs nonetheless failed at the source-preservation assertion
for `tests/supervisor_worker.py`. That protected test file changed
from SHA-256
`c19982062ba119b1a86db187d62c2ee9b1f25725398a526a36e60072250b2fef`
to `2e9a482da8a7819926531119fc9c73b2c4106f9e44f8368858bbddd3ac722471`.
The historical bytes remain in Git and the manifest remains intact.
This candidate has no combined qualification. A future provenance
review must identify the old and new fixture explicitly before
another integration attempt. The sprint did not bypass the gate.
[Follow-up SDK CI](https://github.com/adithyakupad/neuromancer/actions/runs/42299151853)
