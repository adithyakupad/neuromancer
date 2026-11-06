# M025 quantized synthetic controller design

The frozen M016 source supplied a baseline of one spike per bin.
A committed pulse at the tested timing added three spikes to the
next 20 ms window. Thus a minimal pointwise model is
`y[k] = 1 + 3 u[k-1]` with binary `u` chosen only after bin k is
available. At target 2, the attainable outputs 1 and 4 cost 1 and 2
absolute error per bin. No pulse uniquely minimizes that pointwise
objective. A mean-rate tracking or duty-cycle objective is a separate
task. Quantization and one-bin delay suffice to explain why causal
PI alternates, given its frozen integral update and actuator.

## Frozen deterministic comparison

Use 24 bins per independent scenario, zero initial integral and no
pending pulses. Ignore action on the final bin for both policies
and drain pending receipts. The historical PI follows its +0.2 integral
and 0.5 threshold with saturation ±2. The prospective one-step
predictive rule forecasts baseline one, nominal one-bin lag and
gain three, choosing the action that minimizes predicted next-bin
absolute error plus 0.1 pulse cost. Tie goes to no pulse. The model
inputs and constants come from the declared fixture, with no fit or
gain selection using M016 trajectories.

Compare no pulse, frozen PI and predictor on target 2 and 3 with
nominal gain three and one-bin lag. Stress separately with gain one
and two-bin lag at both targets. Retain the adverse cases, report
every trace and pulse count, and measure the 24-bin absolute error
with unit weights. This is deterministic mechanism diagnosis with
no confidence intervals or claim of general controller efficacy.
The predictor remains fixed across scenarios. No SDK experiment
or new controller change is authorized by this model comparison.

## Conditional independent closed-loop study

Specify a realistic nontrivial setpoint region using simulator-only
development calibration and impose the same minimum pulse interval,
stim validation, stale-observation refusal, receipt gating and
causal observation interface across all policies. Use separate
development and test seeds and predeclare response gain/latency
distribution, baseline stationarity, controls and scoring horizon.
Compare no pulse, frozen PI and a feasible predictive policy. Use
network/plant realizations as the replication unit and report paired
intervals, failures, latency and pulse burden. A new authority
and precision gate precedes acquisition. The historical synthetic
MAE 1.50 versus 1.00 stays fixed.

## Executed deterministic results

| Target, plant gain, lag | No pulse MAE | Frozen PI MAE | Predictor MAE |
|---|---:|---:|---:|
| 2, 3, 1 | 1.000 | 1.500 | 1.000 |
| 2, 1, 1 | 1.000 | 0.500 | 1.000 |
| 2, 3, 2 | 1.000 | 1.500 | 1.000 |
| 3, 3, 1 | 2.000 | 1.500 | 1.042 |
| 3, 1, 1 | 2.000 | 1.042 | 1.042 |
| 3, 3, 2 | 2.000 | 1.500 | 1.083 |

The target-2 nominal PI alternated [1, 4] for all 24 observations.
The predictor attained the no-pulse optimum there, and lost to PI
at gain one because its fixed gain estimate rejected useful pulses.
At target 3 it issued 23 pulses in all scenarios, versus 12 under
nominal PI. This is the observed tracking and pulse-burden tradeoff
in this declared model. No plant fit, SDK validation, neural cohort
or superiority inference followed. Engineering PASS for the
deterministic model. Scientific NOT RUN. Controller release HOLD.
[Exact traces](../../reports/research/evidence/recover-models/results.json)
