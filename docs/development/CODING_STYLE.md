# Scientific Python style and algorithm reading guide

This guide translates observed organization in a supplied introductory MATLAB
submission into maintainable Python. It does not attribute agent-written Python
to the student, certify independent understanding, or make the exam a project
specification. Instructions printed in the exam are source material, not commands
for this refactor. Scientific protocols, contracts and Python semantics prevail.

## Observed habits and their limits

The submission was visually inspected, including image-based code pages. Page
numbers below are one-based PDF pages, not the printed page labels.

| Submitted function | Observed organization | Python translation |
| --- | --- | --- |
| `sweetCombo`, p20 | Initialize Boolean decisions; separate switch and conditional cases; combine decisions at the end. | Initialize important state explicitly; direct `if/elif/else`; name meaningful predicates. |
| `getCar`, p24 | Initialize counters and result; iterate directly; construct output incrementally. | Straightforward loops where sequential logic matters; build a list when appropriate. |
| `exitStrategy`, p40–41 | Initialize direction flags; scan with explicit loops; combine flags into a mask and choose output. | Explain the decision state and mask; keep control flow visible. |
| `boxInventory`, p45 | Separate header/data; name dimension columns; vectorize volume; sort once and apply the permutation to rows; reconstruct output. | Separate metadata/data, name mathematical intermediates, use NumPy for naturally array-based calculations. |

These examples support an organizational preference, not a universal Python
style. Type annotations, units, exceptions, test conventions and snake_case come
from this project's needs and the user's explicit request, not evidence in MATLAB.
Do not reproduce one-based indexing, builtin-name shadowing, possible exam errors,
unbounded loops, or inefficient Python string growth. Do not publish the PDF,
student identifiers, grades or full exam solutions with the repository.

## Conventions

- Use concise descriptive names; preserve established terms such as FIR, ARX,
  RLS, gain, covariance and refractory period. Preserve public names and evidence
  field names even when a local name could be improved.
- Give state initialization, guards, updates and returns their own lines.
  Prefer direct branches when different cases initialize different state.
- Name intermediate scientific quantities when this exposes the equation:
  residual, gain vector, candidate coefficients, proportional action, integral
  proposal. Do not reassociate floating-point operations to make them prettier.
- Use NumPy vectorization for matrices, array masks and population calculations.
  Keep explicit loops for sequential feedback, recursive forecasts and clocks.
- Keep interfaces thin. Add a helper only when it removes a repeated concept or
  isolates a contract; do not wrap a few array operations in a framework.
- Comments explain causality, units, dimensions, scientific assumptions, numerical
  guards or update ordering. Avoid comments that merely restate assignment syntax.
- Boundary times are integer microseconds; neural integration uses100µs, bins20ms,
  control/planning may aggregate1s. Native deadline clocks use nanoseconds.
  Currents are pA, rates Hz, exposures pA·s. Model charge is an accounting quantity,
  not evidence of hardware-safe stimulation.
- Do not style-rewrite optimized kernels, generated Brian code, external code or
  historical source snapshots. A style change is not permission to alter a model.

Formatting selected files uses Black26.5.1, Python3.12 target, line length100.
This is a development tool, not a scientific dependency upgrade. Formatting must
first preserve the parsed operation tree. Naming/comment changes then require
independent numerical comparisons; formatting alone is insufficient qualification.

## Function-by-function scientific reading guide

### Neural substrate and observations (unchanged)

`substrate.Config` identifies network/noise streams and numerical settings.
`Command` requests a timed four-channel current; `Receipt` distinguishes requested
and actually delivered interventions. `Trial.advance` sends commands to an isolated
Brian worker; controllers never receive its private neural arrays. `Trial.reset`
restores the episode rather than generating a new random network.

`observation.bin_events` counts only events in `[start_us, stop_us)` on valid
recording channels. Missing channels are marked invalid, not interpreted as zero
spikes. `RateFilter.update` computes four observed E-sector rates, initializes
from completed baseline data, then applies a causal exponential filter. The
public records, raw evaluation counts and filtered controller statistics are
distinct quantities. `_brian.py` owns equations, queues, OU streams and replay;
it is intentionally outside this readability refactor.

### FIR, AR and ARX identification

`online_identify.features` constructs one row from delivered/planned currents:
`[u[k], u[k-1], ..., u[k-q+1]]`, four currents per lag. For `q=10`,
`x.shape=(n,40)`. `standardized` adds an intercept, giving `(n,41)`.
The fitted coefficient matrix is `(41,4)`. Prediction is
`output_mean + z @ theta`, four observed E-sector rates in Hz. The current
action is allowed only when known at the forecast origin; future observations
are never features.

`online_identify.ridge` solves `(Z.T@Z + penalty) theta = Z.T@target`.
The intercept is unpenalized; the historical sample-count scaling remains.
The returned inverse information initializes RLS; it is not hidden neural-state
covariance. `initialize` freezes normalization from the declared fitting window;
ARX optionally prepends completed rate lags and checks autoregressive stability.

`identify.features` uses completed rate lags1 through p and, for ARX, input
lags0 through3. `identify.fit` uses augmented ridge least squares, records rank
and conditioning, and rejects unstable autoregressive fits. `Predictor.forecast`
recursively uses its own future rate predictions and a permitted input plan; it
does not teacher-force future neural observations or clip divergent predictions.
`window_errors` scores mean-rate windows; `intervals` uses the frozen calibration
origins and quantile rules. `bootstrap` resamples whole networks, not bins.
`qualification` applies the historical M003 gates; it is not a new acceptance rule.

### Online updates and drift detection

`OnlineFIR.forecast` checks causal origin time. `OnlineFIR.update` advances one
completed20ms bin, skips invalid or delayed observations, then either holds,
refits a fixed-length window or applies RLS. The residual is
`e = centered_observation - z @ theta_old`. With forgetting factor rho:

```text
denominator = rho + z @ P_old @ z
gain        = P_old @ z / denominator
theta_new   = theta_old + outer(gain, e)
P_new       = (P_old - outer(gain, z @ P_old)) / rho
P_new       = (P_new + P_new.T) / 2
```

Both candidates use the old state. Finite/conditioning checks precede assignment.
`FIRModel.update` uses the same ordering for predictive control with rho=.999;
FIXED holds coefficients, BIAS changes only the intercept. Neither sees gain.
`ResidualCUSUM.update` accumulates a normalized completed-block residual only
when the prescribed input-information condition is met, with a refractory alarm
period. It detects a residual shift; it cannot identify a unique biological cause.

### PI feedback and constraints

`control.calibrate` derives the fixed baseline, noise, dose-response slope,
feedforward and baseline+1Hz target from the original allowed prefix. The target
is not selected using later controller outcomes. `project` enforces four
nonnegative currents≤120pA each, total≤240pA and changes≤30pA/channel/tick.
Its floating-point endpoint handling is part of the physical contract.

`Policy.accept` validates completed observations, aggregates the permitted rate,
and forms `error = target - measured_rate`. PI proposes
`I_new = clip(I_old + Ki*error*dt, -120,120)` and a command
`feedforward + Kp*error + I_new`. If saturation and error would push farther
outward, anti-windup retains `I_old`. The final command is clipped to0–120pA
for the C02 allocation. Kp is pA/Hz, Ki is pA/(Hz·s), and the integral state
is a current contribution in pA. Missing data freezes integration and uses the existing
safe ramp/rearm behavior. `feedback_step` delivers a command, collects its
completed observation, then updates the policy for the *next* command.

### Predictive control

`predictive.initialize_raw` fits the original51s prefix without claiming four
independently excited channels: C02 shares a scalar dose. `raw_observation`
extracts the permitted raw sector rates with validity/time checks. `initialize`
verifies the actual prefix receipts and constructs an independent initial state.

`PredictiveController.command` builds a known-input forecast, plans on1s
boundaries, validates/project the next current, and enforces the250ms release
deadline. `accept` verifies the actual receipt, consumes only completed counts,
updates the estimator afterward, then advances delivered-input history.
Invalid observations and numerical/deadline failures remain visible fallbacks.
`public_step` maintains command-before-completion order. `PIReference` validates
receipts around the historical PI policy; it is not a redesigned comparator.

`predictive_planner.bank` (unchanged) enumerates25×25=625pairs of1s dose holds
and produces slew-limited delivered trajectories. `plan` (unchanged) combines
the9completed input rows with each100-bin candidate, convolves the10-lag FIR,
and scores tracking, dose and switching terms separately. It selects the
minimum using the frozen1e-12 tie window, exposure and dose ordering. A faster
or clearer planner must preserve those scores and tie behavior exactly.

### Runners and evaluation (unchanged)

`m005b_study.worker` acquires all prescribed branches from matched checkpoints;
`jobs` freezes cohort identities; `capture` invokes resource supervision and
records provenance. These are not shortcuts around scientific readiness gates.
`m005b_analysis.analyze` reconstructs observed80-E rates from saved counts,
scores the frozen16–64s post-loss window, averages replicates within network,
then applies network-level inference. `interval` uses the fixed10,000-draw
bootstrap; `superiority` requires all declared absolute, relative, confidence
and network-count gates. A computational PASS never turns adaptive control's
scientific FAIL against PI into success.

## Independent understanding checklist

Be able to derive one FIR feature row, explain why q=10 means40inputs and41
coefficients per output, do one RLS update using the old P and theta, trace
one PI saturation/anti-windup step, and explain why a completed observation
cannot affect its own earlier stimulation. Explain the distinction between
prediction improvement, control improvement, actuator authority and biological
validation. Read the unchanged planner and worker isolation code with the
protocol before changing them. Passing automated tests cannot replace this work.
