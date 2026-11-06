# M019 bounded producer-boundary plan

Base 8194810b22f6be73a31d647f4375fd118471d829. The SDK 1.0.0 public
source callbacks bracket batch generation. No documented hook exposes
producer observation of the accelerated ring request, wake-up or
scheduler dispatch. The probe uses a separate observer and private
layout knowledge solely for read-only diagnostics. No SDK code or
memory is modified.

One hosted diagnostic job per platform, Ubuntu and macOS Intel. In
fixed order run stock, custom, record, replay, PI. Each condition
starts a fresh worker with at most three sequential sessions. Each
session has sixteen 500-frame windows at 25 kHz in accelerated mode.
Stock uses the built-in source, no recording, no pulses. Custom changes
only the source to the existing seeded M016 source. Record adds SDK
HDF5 recording. Replay adds the frozen M016 PI pulse schedule at ticks
0, 2, 4, 6, 8, 10, 12, 14 without a controller. PI substitutes the
existing CountPI policy with receipt gating. Record versus replay
separates pulse traffic from controller decisions. Source and
recording are confounded with order across the suite, and observation
overhead may change failure incidence. This is a diagnostic, not a
rate estimator.

Each condition keeps its own unchanged 120 s supervision and SDK
100 ms frame wait. The hosted job is capped at 15 minutes including
setup and cleanup. The observer maps only the header O_RDONLY and
samples every 5 ms, verifying magic, version and sample rate. It
samples SDK producer PID status and process CPU time without attaching
a debugger or suspending the process. A sample can establish request
visibility to the observer and a stationary write head. It cannot
prove producer receipt or infer a scheduler wake-up from coarse CPU
counters. The independent observer is ready before tick zero and
uses its own monotonic timestamps. SDK frames have separate units.

The first failure in a condition stops that condition. Continue to
the next frozen condition only if normal worker/descendant cleanup is
verified and the outer watchdog did not intervene. Preserve partial
traces and recordings even on failure. No retry, deadline changes,
unplanned conditions or replacement runs. Local preflight is one
stock session under the same 120 s budget. Static tests may run
before it. Linux/macOS execution is a diagnostic rather than release
qualification. A repair requires separately justified evidence and
exact-head release checks.
