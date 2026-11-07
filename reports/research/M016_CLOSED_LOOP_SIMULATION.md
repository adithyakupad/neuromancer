# M016 SDK closed-loop simulation

The installed CL SDK simulator executed the complete causal PI
feedback path. The m016-pulse-v1 source generated its own synthetic
counts from committed SDK events. That fixture tests causal I/O
software with known ground truth. Biological validation was NOT RUN.

## Source, controls and observed responses

Every completed session ran 16 ticks at 50 Hz. Seed 16016 gave
background phase 192, one spike per 500 frames on electrode 8.
A commit on electrode 4 triggered synthetic spikes at offsets
100, 150 and 200 frames. Spike events and zero-valued int16 sample
frames were generated separately. The source had no refractory
dynamics. The only response was the declared pulse kernel.

| Workload | Requests | Committed pulses | Spikes | Additional spikes |
|---|---:|---:|---:|---:|
| C0 no stimulation | 0 | 0 | 16 | 0 |
| C1 response enabled | 4 | 4 | 28 | 12 |
| C2 response disabled | 4 | 4 | 16 | 0 |
| C4 changed electrode | 4 | 4 | 16 | 0 |
| C5 response delayed | 4 | 4 | 28 | 12 |
| C6 invalid and expired requests | 5 | 0 | 16 | 0 |
| PI | 8 | 8 | 40 | 24 |
| Frozen no-pulse | 0 | 0 | 16 | 0 |
| C1 repeat | 4 | 4 | 28 | 12 |

C3 was the declared offline +500-frame circular shift of C1 commit
timestamps. The nominal kernel matched zero of 12 shifted responses
and 12 of 12 original responses. C5's spikes occurred 32, 34 and
36 ms after commitment, outside the immediately following observation
tick. C1 and its repeat had identical relative commit frames and bin
counts. All source callbacks matched SDK receipts and HDF5 events.
[Raw matrix and verification](../engineering/evidence/m016/final_matrix_verification.json)

## Feedback result

The PI saw only completed 20 ms observations. It compared target
count 2 to electrode 8 activity, then proposed a simulator pulse
through a separate action gate. The integral advances on a valid
no-action tick or after a reported commit. It freezes on invalid
observations and rejected actions. Archive verification independently
reconstructed every PI decision and its integral state. Unit fixtures
tested missing and stale data, in addition to the real rejection
control. The final tick drains any outstanding receipt.

PI alternated between bins containing one and four spikes. Its
mean absolute tracking error was **1.50 spikes/bin**, versus **1.00**
for frozen no-pulse. The loop closed causally, and the chosen gains
and binary actuator failed to improve this tracking metric. No
gains were retuned.

After PI qualified, a two-coefficient count FIR/RLS shadow predictor
consumed the saved SDK receipts. It fit the first eight C1 bins and
predicted each PI bin before assimilating the valid observation.
The fixed predictor had MAE 0.09375 and RLS 0.04908 spikes/bin across
16 PI bins with 16 confirmed updates. This is offline shadow replay
on a deterministic fixture. The predictor had no stimulation authority.
The original V1 FIR/RLS model uses a pA history and four sector rates.
[Shadow replay](../engineering/evidence/m016/final_matrix_shadow.json)

Reproduction, exact timing and resource budgets are in the engineering
report and interface guide. The experiment established software
causality under one synthetic response mechanism.
[Qualification report](../engineering/M016_CL_SDK_QUALIFICATION.md) ·
[Protocol](../../docs/research/M016_CL_SDK_PROTOCOL.md) ·
[Adapter and run commands](../../docs/interfaces/CL_SDK_ADAPTER.md)
