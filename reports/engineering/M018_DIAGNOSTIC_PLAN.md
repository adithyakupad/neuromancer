# M018 — Prospective SDK FROZEN frame-stall diagnosis

Baseline: `70e976c1e990db2fbbc88f786b5d7c06a691aa70`.
Engineering branch: `engineering/m018-sdk-frame-stall`.

Historical failed macOS Intel SDK job: https://github.com/adithyakupad/neuromancer/actions/runs/42172116497
Seven sessions passed before `FROZEN` stalled waiting for frame 5500. Supervisor returned WORKER_FAILURE with verified cleanup. The exact prior source/transport/consumer cause remains unknown. Do not relabel failed CI.

## Frozen bounded design
1. Add opt-in timestamped JSONL source records: open/close; read begin/end, frame range and number; stim callback begin/end. Host monotonic timestamps and SDK frame indices are distinct clock domains. Avoid logging individual spikes or frames.
2. Add opt-in client records only for FROZEN: next-tick request, tick returned, frame start/stop, recording stop begin/end and session exit. Write request marker before blocking call.
3. Write diagnostics into existing case output directory for existing unconditional CI artifact upload; do not write into historic scientific evidence.
4. Preserve all nine sessions, 16 ticks each, 25kHz, 500 frames per 20ms bin, SDK 1.0.0, original 120s supervisor/12min CI, stimulation/safety contracts and watchdog.
5. No retries, adjusted deadlines, omitted failing case or new neural acquisition. Run once on branch CI; analyze both macOS and Linux.
6. Existing frozen scientific and numerical code is immutable; modifications confined to optional logging hooks and diagnostic report. If instrumentation alters outcomes, disclose overhead.

## Interpretation
- Source read begun but no end: likely source callback stall, not yet proven.
- Source records completion through target and client blocked: possible SDK delivery/consumer issue; SDK internals unavailable.
- Client read received target but processing blocked: inspect application binning/recording.
- Neither source nor client advances: unresolved scheduler/transport issue.
- Clean CI alone does not explain the original failure.
- Any subsequent correction requires a separately reviewed diff, same timing and exact-head CI on Linux/macOS.

Release HOLD until explained and qualified. No merge, tag or publication.
