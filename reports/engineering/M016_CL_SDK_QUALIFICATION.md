# M016 CL SDK qualification

**Engineering PASS for the bounded software simulator workload.**
**Hardware execution NONE. Biological validation NOT RUN.**

M016 starts from `69be977c06ff9cef32c90ed01e013103fe273e76`. The
completed SDK matrix used `f43954001327dce04c4c310080201c6e88b2a2e7`
on `research/v2-m016-cl-sdk-integration`. The final report commit is
identified in the handoff. Independent physical Git blob checks verified
all 38,602 base paths, including V1, M013, M014 and M015 code, tests,
reports and historical numerical evidence. The V1 environment was used
only for regression. Historically locked cohorts remained unopened.

## Installation and observed SDK

The isolated environment `/tmp/neuromancer-m016-sdk` used Python
3.12.15 on macOS arm64 with CL SDK 1.0.0. NumPy 2.5.4, SciPy 1.18.1
and PyTables 3.11.1 were installed there. The virtual environment
occupied approximately 477 MiB by `du -sh`. Dependency checks reported
no broken requirements. The SDK wheel was 514 kB and had SHA-256
`d83335265da344a66ea76af2661f779924e52736780e3cd169774ef0a34eec03`.
The all-wheel dependency probe resolved an older package because the
current release requires python-louvain, which was installed from an
sdist in the version-pinned installation. The older SDK was downloaded
during resolution but the runtime environment installed 1.0.0.
[Installation hashes](evidence/m016/installation_hashes.json) ·
[Dependency versions](evidence/m016/sdk_environment.txt)

The official simulator identity was true. The installed API supported
`open`, raw `read`, `loop`, `stim`, `record`, `RecordingView` and the
custom source interfaces. Installed signatures, module path and
Python version are archived. The default-source read-only probe opened
in 1.468 s, returned 2,000 × 64 int16 samples at 25 kHz and closed.
The 2,000-frame SDK read took 0.243 ms in accelerated mode, about
8.24 million frames/s for that single call. It is a short buffered
read measurement. The fixed custom matrix had a 56.4 s startup and
cleanup forecast against a 120 s cap.
[Installed signatures](evidence/m016/probe/signatures.json) ·
[Default probe](evidence/m016/probe/probe.json) ·
[Official developer guide](https://docs.corticallabs.com/)

## Boundary, timing and recording

The SDK bridge verified literal simulator identity before opening and
again before submission. Unit fixtures for false and ambiguous identity
proved that they cannot reach `open`. The isolated software session
used logical stimulation 0–3 mapped to electrodes 4–7 and logical
recording 0–19 mapped to electrodes 8–27. The SDK pulse fixture used
160 µs at −1 µA followed by 160 µs at +1 µA with 80 µs lead.
This is a simulator command qualification. A real device requires
separate authorization, physical limits and validation.
[Neural I/O contract](../../docs/interfaces/NEURAL_IO_CONTRACT.md) ·
[CL SDK adapter](../../docs/interfaces/CL_SDK_ADAPTER.md)

All 144 completed windows were exactly 500 frames and aligned to
20,000 µs. Frame duration is exactly 40 µs by integer arithmetic.
No missing or late windows occurred in the qualified workload. All
28 accepted submissions had matched callbacks, loop receipts and
HDF5 events. Four unsupported destinations and one expired proposal
were rejected before invoking SDK stimulation. The custom response
source emitted only labeled synthetic data. Nine recordings reopened
successfully, with exact event and raw-frame checks. All use 8,000 × 64
raw int16 samples with the documented 0.195 µV/sample scale.

The complete suite passed **226 tests**, 46 warnings, in 47.94 s
of pytest time. The eight added cases covered the sample clock,
overflow, boundaries, malformed and missing observations, channel
mapping, late requests, receipt-gated PI and simulator interlock.
Historical regression ran under the unchanged qualified supervisor.

## Timing and resource measurements

Latency values are milliseconds, over the completed nine-session
accelerated workload. Percentiles include all applicable samples in
that workload. Commit observation latency ends at the start of the
tick that reports the commit. The cadence deviation is absolute
distance from the median inter-tick interval within each session.
These wall measurements describe application processing and host
cadence. The SDK itself reported a jitter-detection limitation.

| Metric | Samples | p50 | p95 | p99 | Max |
|---|---:|---:|---:|---:|---:|
| Application processing | 144 | 0.0486 | 0.1432 | 0.1997 | 0.2568 |
| Accepted submit call | 28 | 0.0218 | 0.0803 | 0.1151 | 0.1270 |
| Rejection processing | 5 | 0.0041 | 0.0144 | 0.0160 | 0.0164 |
| Submit to observed commit | 28 | 0.1239 | 0.3580 | 0.3745 | 0.3788 |
| Inter-tick wall interval | 135 | 0.1088 | 0.3749 | 0.4763 | 4.8726 |
| Inter-tick cadence deviation | 135 | 0.0158 | 0.1560 | 0.2772 | 4.5740 |

All observed commits equaled their SDK intended frames, so commit
jitter was zero frames on this fixture. Synthetic response offsets
were 4, 6 and 8 ms on the frame clock, distinct from host latencies.
The delayed control used 32, 34 and 36 ms. The experiment provides
desktop accelerated timing evidence.

The matrix used **5.065 s** supervised wall time for 2.88 simulated
seconds, 0.144 s SDK worker application CPU over the session bodies,
about 6.375 sampled CPU seconds across tracked tree processes,
64,569,344 bytes peak worker RSS and 266,616,832 bytes sampled peak
tree RSS. Tree CPU is a sampled lower bound. RSS sum can include
shared pages. Recordings occupy 15,272,148 bytes. Matrix artifacts
occupy 15,398,753 bytes including ledgers and supervisor logs, within
the 25 MiB cap. Every real SDK stage completed or failed with verified
supervised worker cleanup. The successful matrix had zero forced
descendant cleanup and zero live tracked descendants after closure.
[Verified metrics](evidence/m016/final_matrix_verification.json)

## Failures and process containment

Three earlier sessions acquired raw evidence and failed during reporting.
The first smoke used a dictionary as a recording path. The first
matrix opened the path, then looked for application metadata at the
wrong HDF5 level. The second attempt encountered NumPy integer
dimensions during JSON serialization. The final matrix uses the
observed path, metadata namespace and native integer dimensions.
The recorded controls, seed, pulse design and 120 s matrix budget
were retained. Failed attempts, traces and recordings are preserved.

The SDK launches some descendants into new process sessions. The
supplementary outer watchdog tracks observed descendants by PID and
creation time. A bounded synthetic escaped-child fault exercised
the cleanup path. The worker status was DEADLINE_EXCEEDED, the
watcher forced cleanup of one tracked escaped child, found no live
tracked descendants and returned failure. The polling watcher does
not establish containment of an unseen process that escapes between
samples. The original OS deadline and cleanup implementation remain
in use.
[Fault evidence](evidence/m016/escaped_child_fault_descendants.json)

## Reproduce

The interface guide gives the dedicated SDK environment setup and
exact acquisition, archive verification and shadow replay commands.
For historical regression, run `PYTHONPATH=src python -m pytest -q`
from the repository root in the original environment.
[Reproduction commands](../../docs/interfaces/CL_SDK_ADAPTER.md) ·
[Closed-loop results](../research/M016_CLOSED_LOOP_SIMULATION.md)
