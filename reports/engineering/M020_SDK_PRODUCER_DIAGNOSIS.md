# M020 SDK producer scheduling

**Engineering PARTIAL · Scientific NOT RUN · Release HOLD.**

M019 remains the positive failure reproduction. In recording-only
macOS Intel execution, request 4500 was visible while write head 4000
was stationary and the next source callback did not appear. M020
moved the reproducer outside the NEUROMANCER package. It uses only
SDK, NumPy and a timestamp-coded synthetic source. A disposable,
hash-checked SDK 1.0.0 shadow copy adds producer phase stamps. It
retains the unmodified 100 ms consumer wait and the existing external
120 s watchdog. Neither the installed SDK nor release code was
modified. The diagnostic copy is omitted from evidence and package
builds. [Frozen plan](RECOVER_PLAN.md)

The local arm64 preflight ran one session per arm. All five reached
sixteen windows and reopened recordings but failed to serialize the
SDK HDF5 NumPy integer to JSON. Their artifacts remain preserved.
A native-integer conversion fixed evidence export before the frozen
hosted run. No extra preflight or repeated hosted acquisition ran.

On exact diagnostic source `d3ac56bd7ae0e48c82849c82723f1c0048a0353f`,
Linux and macOS Intel each completed four unmodified and four traced
M020 sessions, 256 windows across both hosts. Each traced trial
recorded the request load, pre-callback phases, callback entry and
write completion through its sixteenth window. No frame timeout
occurred in these arms. M021's nine lifecycle sessions per host also
completed. All watchdogs reported cleanup verified. The separate
observer from M019 and the producer phase timestamps are from
different executions. They cannot be joined to infer a producer
request load during the M019 failure. OS dispatch, read visibility
from the producer, polling and pre-callback work remain unresolved
on a failed path. Trace I/O can itself affect scheduling.

A minimal upstream report can reproduce the contract with SDK 1.0.0,
Python 3.12, the standalone fixture and hosted macOS Intel. The
positive M019 failure used a different custom recording fixture.
Report both runs and their distinction. The smallest next
discriminating evidence would be a producer request-load trace
during a failed wait, correlated with OS scheduler activity. Do
not raise the timeout or claim an SDK defect based on this suite.

[Exact hosted diagnostic](https://github.com/adithyakupad/neuromancer/actions/runs/42297238288) ·
[M019 positive failure](M019_PRODUCER_BOUNDARY.md) ·
[Official SDK simulator contract](https://docs.corticallabs.com/cl/sim)
