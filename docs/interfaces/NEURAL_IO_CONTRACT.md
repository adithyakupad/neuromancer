# Neural I/O contract

The MEA adapter uses a session-local frame clock. At 25,000 frames/s,
one frame is exactly 40 µs and a 20 ms observation contains 500 frames.
A `FrameClock(session_id, origin_frame)` maps frame `f` to
`(f - origin_frame) * 40` relative µs. The inverse rejects any remainder
after division by 40. Frame indices and relative µs use nonnegative signed
64-bit bounds, with checks before values cross the boundary. The SDK
simulator advances the frame clock independently of the host clock in
accelerated mode. Relative sample time can describe simulated elapsed
time without identifying the SDK epoch with a Brian2 simulation epoch.
The existing suspend-inclusive OS `Deadline` governs process lifetime.
Frame expiry governs electrode scheduling. No affine device-to-host
calibration or physical timing model is assumed.

## Records and ordering

| Record | Meaning |
|---|---|
| `SampleFrames` | Explicit electrode IDs, frame indices and raw signed int16 samples with scale in µV/sample unit |
| `SpikeEvent` | Frame and electrode ID, optional 75-sample waveform in µV |
| `SpikeBin` | Causal mapped counts, per-channel validity, missing-frame total and completion frame |
| `ElectrodeRequest` | Logical destination, originating observation, expiry, lead time and µs/µA pulse phases |
| `StimDecision` | Local rejection or SDK submission acceptance with electrode and submission frame |
| `StimReceipt` | Matched SDK committed event with electrode, frame and originating request ID |
| `SessionState` | Closed, verified open simulator, or hardware unqualified |

A bin covers `[start, stop)` and becomes usable at or after `stop`.
The binning routine checks exact adjacency to the previous boundary.
Missing sample frames mark the whole bin invalid while retaining counts
for diagnostics. An arrival one bin or more after completion is late
and invalid. Earlier-than-completion availability, discontinuous
windows, zero length, duplicate frames, out-of-order frames, duplicate
same-electrode spikes and spikes outside the bin fail validation.
Same-frame spikes on distinct electrodes are allowed. The spike list
must be ordered by frame. The final frame of one bin precedes the first
frame of the next bin. Event processing handles commit receipts before
the current observation produces another action.

Samples and spikes are independent records. The sample scale describes
unit conversion and does not infer spikes from voltage or voltage from
spikes. No waveform is created by NEUROMANCER. A missing waveform may
remain absent. SDK materialization of synthetic waveforms is disclosed
in the simulator report.

Channel maps are explicit tuples from logical stimulation 0–3 and
recording 0–19 to electrode IDs. The map validates range, uniqueness,
the allowed stimulation set, disjoint fixture memberships and optional
finite, unique 2-D coordinates in µm. Recording channels denote
electrodes, not simulated neuron indices. The existing `Command`,
`Observation` and `Receipt` remain the V1 Brian2 contract with pA and
simulation-relative µs.

## Action and controller semantics

The qualified action allows only a negative-first symmetric
160 µs/±1 µA biphasic fixture pulse and an 80 µs lead. An outstanding
command blocks another. A stale or foreign-session observation,
unsupported destination, invalid pulse or invalid frame bin blocks
submission. SDK submission alone records acceptance. A distinct
timestamped commitment is required before the PI commits the integral
update for a pulse. On invalid observation or rejection the integral
freezes. A missing or mismatched commit fails the session. The fixture
stores counts and errors in spikes per completed bin and uses a binary
pulse decision, independent of V1 PI gains.

The boundary supports reusable recording conversion and validation.
Physical authorization, limits and validation are outside the
qualification of these records.
