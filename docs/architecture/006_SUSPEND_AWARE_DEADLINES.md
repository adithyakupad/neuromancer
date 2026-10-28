# Suspend-aware deadlines — M005A.4

Implemented for future execution only. Frozen scientific protocol009 and M005A.3 amendment010/resource-stop remain unchanged. No confirmation acquisition or automatic resume follows this engineering qualification.

## Clock and evidence

On macOS use `mach_continuous_time()` with integer `ticks*numer//denom` conversion from `mach_timebase_info`. Apple documents that this clock includes suspension, while `mach_absolute_time()` pauses during system sleep. The installed SDK declares continuous time available from macOS10.12. [Apple Kernel API](https://developer.apple.com/documentation/kernel/1646199-mach_continuous_time), accessed2026-10-28; [Apple header](https://github.com/apple/darwin-xnu/blob/main/osfmk/mach/mach_time.h). Native header hashes and an independently compiled C probe accompany the report.

The clock is monotonic elapsed time within a boot, not UTC and not process CPU time. CPython's observed `monotonic_ns`/`perf_counter_ns` on this host use sleep-exclusive Mach absolute time; they advance while a process is descheduled on an awake machine. `time.time_ns` is adjustable calendar time. Neither is the authoritative experiment deadline now.

Each read brackets the independent nanosecond API `clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW=4)` between continuous reads. It checks API agreement, nondecreasing continuous/uptime values and that continuous elapsed time cannot fall behind awake-system elapsed time. Quantization allowance is the integer ceiling of one Mach tick (42ns on the measured125/3timebase). Continuous-minus-uptime growth is expected during sleep; wall-time steps are diagnostic only. APIs share kernel timekeeping: agreement does not establish an independent physical oscillator or detect every common-mode kernel error.

A missing symbol, invalid timebase, missing boot identity, backward reading or API discrepancy raises ClockError. A failing clock instance is quarantined; no automatic uptime fallback may execute work. The read-only boot-session identity query may be denied in a restricted sandbox; that is a fail-closed initialization error, not permission to omit domain validation. Native tests needing boot/process identity ran with permitted read access.

Linux uses documented CLOCK_BOOTTIME with boot identity to keep existing Linux execution paths compatible. It is not locally qualified here. [Linux kernel timekeeping](https://kernel.org/doc/html/next/core-api/timekeeping.html). Other platforms reject initialization. No Windows or remote CI result is claimed.

## Representation and hierarchy

`Deadline(end_ns, clock_id)` requires both fields. `Deadline.after(seconds)` creates them from the selected suspend-inclusive clock. `clock_id` includes implementation/version and boot-session UUID. Bare legacy uptime integers, wrong backends and foreign boots reject. `Deadline.from_environment` verifies both `NEUROMANCER_DEADLINE_NS` and `NEUROMANCER_DEADLINE_CLOCK`; every worker inherits exactly those values.

All supervisor states and deadline comparisons use this clock. Existing timestamp keys named `monotonic_ns` now mean the clock explicitly identified in the same record, not implicitly Python uptime. Old archives retain their original meaning and values; do not convert historical timestamps using today's continuous/uptime offset. Deadlines are not reusable across boots.

The acquisition entry point inherits a supplied qualified deadline rather than resetting it. An inherited deadline beyond its original scientific stage cap rejects. A standalone entry point creates one deadline with the unchanged cap. Source/performance metadata distinguishes worker `perf_counter_ns` timings from authoritative suspend-inclusive stage elapsed time. No scientific equations or controller inputs change.

## Sleep, resume and cleanup

During system sleep no user-space code can send a signal. The hardware/OS clock continues to account elapsed time. After resume, the first scheduled supervisor check uses the original end value: if expired, launch no new job, accept no successful stage completion and request cancellation. Active polling is10ms plus scheduling/I/O overhead; no hard real-time physical wake-to-signal bound is claimed.

Normal operation retains .2s cooperative/.2s TERM/.4s final cleanup reserved inside the work budget, including20ms terminal-publication reserve. **The experiment deadline never moves.** If the machine resumes after it has already expired, cancellation skips a cooperative-work grace and sends TERM immediately, then KILL/reaping as needed. A separately declared at-most .8s post-detection cleanup allowance exists only to remove processes and persist failure; it is not extra experiment time. Metadata marks `post_deadline_cleanup`, preserves the original expired deadline and never reports COMPLETED. Cleanup finishing beyond the old deadline is expected in this case and must not be mistaken for budget success.

If the authoritative clock itself becomes unreliable, terminate work with CLOCK_FAILURE. A separate uptime stopwatch may bound emergency process cleanup only; timestamps in that fallback are labeled, untrusted experiment timestamps are null, and success is impossible. Failure to establish group absence remains CLEANUP_FAILURE. Cleanup signals are idempotent on absent owned groups. POSIX group containment still excludes descendants that deliberately detach/escape; arbitrary hostile subprocesses and uninterruptible kernel operations are unsupported.

## Qualification boundary

Executed tests cover native C/Python agreement and same-boot sharing, deterministic injected clock changes/resume/expiry, actual synthetic worker cancellation/TERM/KILL, descendants, partial writes and cleanup idempotence. Physical machine sleep was not automated: controlled access and an independently safe wake/watchdog arrangement were unavailable. Suspend semantics are supported by authoritative Apple documentation and SDK evidence, not claimed as an executed controlled sleep test. No system clock or power setting was changed.

A future scientific continuation requires a new prospective execution amendment: accept or reject the three audited complete trials without considering favorability; identify all17missing original pairs; retain PI10/5 and every original gate; declare the new clock/domain/resource policy and budget before acquisition. The old no-retry contract and resource failure are not rewritten. No new confirmation or locked-network evaluation is authorized here.
