# M019 SDK producer boundary

The investigation started from M018 archive
`8194810b22f6be73a31d647f4375fd118471d829`. The fixed diagnostic plan
was committed at `cde644c5`, and the hosted run uses `6cd482ca`.
The V2 release ref remained at `70e976c1`. The reported M018 C0
failure completed through frame 1500 and lacked a source callback
entry for the target at frame 2000. The FROZEN and C2 timeouts were
also retained. No source or evidence from those runs was edited.
[M018 diagnosis](M018_SDK_FRAME_STALL.md)

## Installed SDK and observation method

The public source hooks are open, read, stimulation callbacks and
close. Read records entry into batch generation. The documented live
source cursors describe producer output and read position. None
acknowledge the accelerated ring request or timestamp OS dispatch.
Local inspection of the installed SDK 1.0.0 found the consumer's
request store and the producer's load in separate processes. Between
the producer load and the source read, the producer handles command
state and attempts to deliver committed stimulus events. An
unchanged write head alone cannot distinguish delay in those steps.
The SDK's accelerated wait remains 100 ms.
[Public SDK simulator API](https://docs.corticallabs.com/cl/sim)

The separate observer uses a version-checked 72-byte read-only map of
the shared-memory header. Two equal consecutive decodes mark a
stable sample for analysis. They cannot establish a transactional
snapshot. The helper records request and write frames, the stimulus
watermark, producer PID/status/CPU time and its own host monotonic
interval. A visible request rules out a missing published value at
those sampled instants. CPU status is sampled and CPU time is
quantized. Neither shows when the producer loaded the request or
entered a specific SDK step. Polling and tracing may perturb scheduling.
The application passes the header name and PID from private SDK
handles in the diagnostic harness only. The SDK, its memory and V2
release source were left untouched.

The local arm64 preflight passed 16 windows and clean shutdown. Its
observer independently saw the final write head at 8500 after the
16th consumed window. Local installed SDK module SHA-256 values:

| Module | SHA-256 |
|---|---|
| _data_buffer.py | `3e4b19a8d5c1650a98a0576ad5e8b0334cbefa7d4e2ab87f8b275ad94bb95122` |
| _data_producer.py | `3626ca8a3444190d580b5c248a14f9babfed467262d3d664b57abd4e401fe87a` |
| _closed_loop.py | `5f42813359eda603892f99201d49824e39dabf2cc24fdd6414ed6a68c9a019fb` |

## Fixed controls

One run per platform, in stock, custom, record, replay and PI order,
with three fresh sessions per condition. Every session consumed up
to 16 × 500 frames. The replay condition adds the archived eight
stimulus commands without feedback. PI changes the decision source
to the receipt-gated controller. Each worker kept the original 120 s
supervision limit. The platform job had a 15 min outer bound. The
first condition failure ended that worker. Remaining conditions could
run only after verified cleanup.
[Frozen plan](M019_DIAGNOSTIC_PLAN.md)

## Linux recording-tail finding

Linux completed all 240 requested observation windows. Stock, custom,
record and replay passed 3/3 sessions each. PI completed 2/3 sessions
under its full checks. The third produced all sixteen windows and
eight receipts, then failed the HDF5 extent check. Reopening the file
confirmed 8500 × 64 samples and eight stims. The independent ring
observer also saw write frame 8500 and request reset to zero before
the recording stop. The SDK iterator requests the next batch after
yielding the final window before clearing the request in its exit path.
This allows an extra producer write. The diagnostic waits for the
observer to exit before stopping recording, which can give the producer
time to advance. This Linux result documents a distinct tail-recording
race in the diagnostic and supplies no frame-stall observation. Its
failure stands. A frame-bounded SDK recording could test this
separately. No alternate recording mode was executed.

## macOS Intel frame wait

| Condition | Linux complete / planned | macOS Intel complete / planned | First macOS failure |
|---|---:|---:|---|
| Stock | 3 / 3 | 3 / 3 | None |
| Custom source | 3 / 3 | 3 / 3 | None |
| Recording | 3 / 3 | 0 / 3 | SDK timed out waiting for 4500 after eight windows |
| Frozen stimulus replay | 3 / 3 | 0 / 3 | HDF5 held 8500 frames after sixteen windows |
| Receipt-gated PI | 2 / 3 | 0 / 3 | HDF5 held 8500 frames after sixteen windows |

macOS processed 136 windows, with six planned sessions unstarted under
the fixed stop rule. Both replay and PI produced eight receipts before
the separate recording-tail failures. The recording-only failure
occurred before recording shutdown, with no controller or pulse
commands. Reopening its partial HDF5 independently found 4000 × 64
samples, eight spikes and zero stims. All ten condition workers across
the two platforms had verified cleanup and no outer watchdog
intervention, forced cleanup or observed descendants remaining.
The macOS recording worker used 4.984 s outer elapsed and sampled
212,258,816 bytes peak process-tree RSS.

| Host monotonic ns | Independently recorded event |
|---:|---|
| 323973309894 | Last source batch completed [3500, 4000) |
| 323975358921 | Client completed observation through frame 4000 |
| 323975396180 | Client entered the next SDK call |
| 324001802915 | First stable read-only ring snapshot in the failed wait |
| 324074748759 | Last stable read-only ring snapshot before timeout |
| 324077879198 | Client recorded the SDK TimeoutError for frame 4500 |
| 324081606592 | Observer saw the request reset to zero, with write head still 4000 |

The two stable snapshots were approximately 26.4 ms and 99.4 ms after
the application call began. Both showed request and stimulus watermark
4500, write head 4000, producer-ready set and pause/shutdown clear.
Both process observations reported the producer sleeping and the same
2,209,209,344 ns cumulative CPU counter. The first snapshot's process
observation did not return until 324059956833 ns, so ring and process
samples cannot be treated as simultaneous. The gap between snapshots
also prevents reconstruction of continuous scheduling. Source trace
records contain no entry for [4000, 4500). The client failed after
102.483 ms host elapsed.

**Established boundary.** The consumer successfully published the
request, and the producer did not reach the next observable source
callback or advance the write head during the sampled wait. Failure
before request publication, a slow source callback body, and late
application processing of a returned target batch do not explain this
observed failure. Recorded CPU snapshots cannot distinguish producer
dispatch/wake-up delay, request visibility from the producer's own
execution context, or work after the load and before the callback.
No supported SDK hook records these events.

The recording-only condition reproduced the failure without
stimulation or controller logic. One fixed-order run with no stall in
stock or custom-only conditions is insufficient to conclude recording
caused it or is necessary. The observer also introduces timing
overhead. This is an intermittent macOS Intel compatibility
limitation in the accelerated SDK 1.0.0 path. An upstream timestamp at
producer request load, or a scheduler trace independently correlated
to that load, is required for stronger attribution. No production
change was justified. The frozen budget ended after this run.

[Exact hosted matrix and artifacts](https://github.com/adithyakupad/neuromancer/actions/runs/42183363096) ·
[Retained raw artifacts, summaries and checksums](evidence/m019)

Summed condition-level watchdog wall time was 20.001 s on Linux and
37.699 s on macOS Intel. The maximum sampled process-tree RSS across
conditions was 362,356,736 bytes on Linux and 323,264,512 bytes on macOS.
These totals exclude setup and artifact upload.

To inspect either retained platform artifact without opening the SDK,
extract the archive into a fresh directory and run the summarizer:

```sh
shasum -a 256 -c reports/engineering/evidence/m019/artifact-sha256.txt
out=$(mktemp -d)
tar -xzf reports/engineering/evidence/m019/macos-artifacts.tar.gz -C "$out"
python3.12 reports/engineering/evidence/m019/summarize.py "$out/m019"
```
