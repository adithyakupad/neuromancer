# CL SDK simulator adapter

The verified implementation uses Cortical Labs CL SDK 1.0.0 on macOS
arm64 and Python 3.12.15 in a dedicated virtual environment.
The bridge resolves the installed distribution and module file and checks
that the official `cl.is_simulator()` returns literal `True` before
`cl.open()`. It checks simulator identity again at submission. Absent,
ambiguous or false identification produces a hardware-unqualified result.
There is no hardware execution route. The process supervisor and
suspend-inclusive clock retain their original roles.
[SDK reference](https://docs.corticallabs.com/cl)

## Wiring

`cl_adapter.SimulatorSession` uses context-managed sessions, checks SDK
channel count and frame rate, and accepts only the qualified fixture
destinations. The fixture maps stimulation to electrodes 4–7 and
recording to electrodes 8–27 out of 64. The source response targets
electrode 8 when electrode 4 is stimulated. Mapping provenance and pulse
phases are present in the source configuration and trial ledgers.

`cl_response_source:create_source` is imported in the SDK subprocess.
`set_simulator_data_source` receives validated JSON-compatible
configuration. The source uses `SimulatorDataSourceMetadata`,
`DataSourceBatch`, `DataSourceSpike` and the `DataSourceStim` callback.
The installed inherited `on_stims` dispatches to `on_stim`. Only
committed events schedule synthetic responses. Read ranges are
contiguous and half-open, pending responses are bounded, and lifecycle
and commits are written to a source ledger. The recorded raw samples
are explicitly zero-valued int16 fixture frames, independent of spike
events. The SDK recording may materialize zero waveform placeholders
for spike events supplied without waveforms.
[Custom source API](https://docs.corticallabs.com/cl/sim)

The runner reads completed `LoopTick.frames` and `LoopTick.analysis`,
uses `neural_io.bin_frames`, calls `Neurons.stim` with a `ChannelSet` and
explicit `StimDesign`, then verifies the next reported `Stim`. The
recording closes before reopening via `RecordingView(recording.file['path'])`.
The installed metadata nests caller attributes under `application`.
Recording event timestamps are relative to the recording start, so the
archive verifier adds `start_timestamp` before comparison with the
session ledger. The verifier also checks raw sample dtype, dimensions and
scaling. The installed signatures and versions are archived.
[Developer guide](https://docs.corticallabs.com/)

## Run and verify

From the repository root, set `PYTHONPATH` to its absolute `src` path so
the child process can import the source. Use a dedicated environment with
`cl-sdk==1.0.0` and its dependencies. The environment and download hashes
are archived separately from V1 requirements. Output paths must be new.

```sh
python3.12 -m venv /tmp/m016-repro
/tmp/m016-repro/bin/python -m pip install cl-sdk==1.0.0
export PYTHONPATH="$PWD/src"
/tmp/m016-repro/bin/python scripts/m016_watch.py /tmp/m016-replay 120 /tmp/m016-repro/bin/python scripts/m016_run.py /tmp/m016-replay matrix
/tmp/m016-repro/bin/python scripts/m016_verify.py /tmp/m016-replay
/tmp/m016-repro/bin/python scripts/m016_shadow.py /tmp/m016-replay
```

The default-source startup probe is `scripts/m016_probe.py` and uses
`cl.open(take_control=False)` after simulator verification. The custom
matrix runs in accelerated time with visualization disabled. The watcher
samples identities of escaped SDK children independently of the
qualified supervisor. This provides evidence for observed descendants
and a bounded fault fixture, with a polling limitation for processes
that escape and disappear between samples.
[SDK project](https://github.com/Cortical-Labs/cl-sdk)
