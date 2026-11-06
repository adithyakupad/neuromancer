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

## Prospective amendment: unexpected C2 frame stall

The first instrumented CI attempt on macOS Intel (run 42179696188) failed in C2, not FROZEN. Worker log: SDK timed out awaiting frame 8000. Its completed C2 ticks extend through 7500 frames; same job's C0/C1 sessions completed. Original source trace hooks were restricted to FROZEN, so this result cannot be localized. The supervisor returned WORKER_FAILURE and verified cleanup. The complete artifact was downloaded and inspected; it remains historical failed evidence.

**Before broadening the next diagnostic source:** apply the already-designed source/client opt-in boundary traces to ALL nine existing SDK cases, not only FROZEN. Keep the identical case roster, order, 16 ticks, 120 s supervisor deadline, SDK version, and controls. Log in separate diagnostic files, never in the stimulation commit ledger. No additional iterations or outcome-based test selection. The amendment addresses the direct evidence that stalls can affect C2. It does not erase the FROZEN stall or claim a root cause.
