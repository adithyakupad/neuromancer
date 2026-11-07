# M016 simulator qualification protocol

Base 69be977c06ff9cef32c90ed01e013103fe273e76. Use CL SDK 1.0.0
in a dedicated environment. Verify the installed distribution and strict
simulator identity before opening any session. Use accelerated mode with
visualization disabled. The SDK source is a synthetic I/O fixture.

## Fixed workload and gates

Benchmark one default session with 2,000 raw frames, record opening latency,
CPU, RSS, throughput and observed subprocesses. Fixed probe cap 60 s.
The later custom matrix has nine sessions of 16 ticks at 50 Hz (320 ms per
session), with a 120 s aggregate supervisor deadline and an outer watchdog.
Raw recording forecast is 1.024 MB per second for 20 int16 channels and
3.2 MB per second for 64 channels, before metadata and compression.
Cap total on-disk run output at 25 MiB. Measure RSS and CPU. Allow at least
twice measured default startup per session plus 30 s for closure.
Keep each partial session ledger. Failed sessions stay visible.

Map logical stimulation 0–3 to electrodes 4–7 and logical recordings
0–19 to electrodes 8–27, using 64 raw SDK channels. Simulator-only pulse
160 µs at −1 µA then 160 µs at +1 µA, 80 µs lead, at most one outstanding
request and at most one pulse per 20 ms tick. A returned API call is
acceptance only. Match the next SDK event by channel and frame range.
Do not supply a hardware branch or cast V1 pA commands to electrode pulses.

Custom source identity m016-pulse-v1. Seed 16016 sets phase of one
synthetic background spike every 500 frames on electrode 8 (phase
100–199). Raw frames are all-zero int16 fixture samples at 0.195
µV/sample unit. They are independent of spikes. No waveform synthesis.
A committed event on electrode 4 schedules three synthetic spikes on
electrode 8 at delays of 100, 150 and 200 frames (4, 6 and 8 ms). Other
mapped inputs elicit no response. No refractory model. Coalesce exact
same electrode/frame collisions and retain their count. Reject callbacks
whose response cannot be delivered prospectively. Keep bounded pending
events and callback logs.

C0 no stimulation, C1 pulse with response enabled, C2 same pulse with
response disabled, C3 offline shuffled/circularly shifted committed
timestamps with original responses, C4 pulse on electrode 5, C5 700-frame
extra response delay, C6 invalid destination rejected before SDK call.
Open-loop pulse proposals at ticks 2, 5, 8 and 11 (zero-based).
C3 uses C1 observations and timestamps shifted +500 frames with wrap
inside the analyzed frame interval, with no neural reacquisition.
PI and frozen comparison use the same initial source and 16 ticks.
PI error = 2 minus completed target-electrode spike count, proportional
gain 1, integral gain 0.2 per tick, integral clamp [-2,2], binary pulse
when score > 0.5. Integral advances on a confirmed pulse or valid
no-action tick, and freezes on missing, stale or rejected data.
Frozen comparison emits no pulse. Repeat C1 once with the same seed.
Early fixture smoke (custom, 16 ticks) may precede the fixed matrix and
is retained separately. No V1 controller or predictor tuning.

Qualification requires exact frame widths, valid matched receipts,
recording reopening, real source callback logs, causal response offsets,
zero additional spikes in C0/C2/C4/C6, delayed spikes outside the
following tick in C5, no nominal-lag excess in C3, repeatable C1
relative counts and receipts, and a causal PI feedback trace with valid
receipt-gated state. Report skipped/missing data, all timings and failures.
Application latency is measured with the qualified OS clock. Frame response
latency is separate. No physical device execution is authorized.

## Pre-matrix qualification note

The fixed default probe opened in 1.468 s. The 9-session conservative
forecast is 56.424 s including 30 s of cleanup margin. Initial custom smoke
completed its 16 ticks and wrote the recording, but the report opener treated
the installed `Recording.file` dictionary as a path. Use its observed
`path` field. The first smoke stays archived. C6 additionally tests one
late request at tick 13 with an already expired frame bound. This extends
the rejection checks without changing the source, pulse schedule or controls.
SDK children create their own sessions, so a supplementary outer watcher
tracks descendants by PID and creation time. Any forced cleanup is a failure.

## Post-PI diagnostics

The rate arithmetic for 20 int16 channels at 25 kHz is 1,000,000 raw
bytes/s. The 64-channel forecast used for acquisition remains 3,200,000
bytes/s. After the independent PI gate, run a shadow count FIR/RLS
predictor against the saved SDK receipt trace. Fit an intercept and
single planned-pulse indicator on the first eight C1 bins, ridge 0.1 on
the slope, and update an adaptive copy with forgetting factor 0.999
only after a matching valid PI bin. Compare against frozen coefficients.
This shadow replay has no control authority. The historic V1 predictor
expects a different calibrated pA input and four-sector rate output.
