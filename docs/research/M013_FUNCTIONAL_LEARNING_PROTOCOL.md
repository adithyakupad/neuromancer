# M013 prospective functional-plasticity pilot

Base: 05ad832c7c062ba5cdd8d1d9e38129410ecafa32 (M012 closing revision).
M012 test source724eec11 passed hosted qualification; closing-head publication is
not asserted. Original V1, supervisor and all scientific archives remain immutable.
Style guide was read from optional branch without importing its implementation.

## Mathematics frozen before implementation
Only recurrent E-to-E weights may change. Brian event-driven traces are dimensionless:
dx/dt=-x/20ms, dy/dt=-y/20ms, de/dt=-e/200ms.
At presynaptic arrival: e <- e-y, x <- x+1.
At postsynaptic spike: e <- e+x, y <- y+1.
Pre pathways precede post pathways for simultaneous events. Eligibility is evaluated
at the reward time, including decay since last event. At training minibatch end:
w <- clip(w + 0.1 pA * mean(reward * eligibility), 0pA,30pA).
No inhibitory or E-to-I weight changes. Weights change only after a completed
training minibatch, never in probe/validation/test. Reward is +1 for correct,
-1 for incorrect training prediction, not an efficacy or biological reward model.
Training decoder: online ridge least squares on completed response features,
initialized zero; predict before updating with the current training label. Distinct
standardized probe decoder replaces it for evaluation. No success is presumed.

## Cohorts, splits and task
Pilot only: new network IDs13000,13001; root seed20261104, replicate1300.
No V1 locked IDs100–119 or confirmation IDs are accessed. No confirmatory cohort
is authorized: two networks cannot support useful network-level precision.
Fixed search budget: ONE configuration, no outcome-dependent changes.
For each network pair C0–C4 share original1000-neuron realization and time-indexed
OU innovations. Neural equations,100us step,20ms bins and recording membership are
unchanged. Eligibility uses actual synaptic arrival delay matching original delay.

Trial: A40ms, silent delay40ms, B40ms, response40ms, recovery40ms =200ms.
Binary A selects channel0 vs1, B selects2 vs3. Each symbol is two20ms commands
30 then60pA; first subsequent bin ramps to30 then0. This physical ramp extends
symbol tail into the silent interval. All classes have identical timing and
requested total exposure; no target encoding. All transitions checked by original
validator. Features: four recorded E-sector response rates averaged across two
response bins; no labels/IDs/metadata supplied to prediction.
Balanced independently shuffled splits:32plasticity-training,16probe-fitting,
8validation,16reserved-test trials. Fresh split RNG roles100+, separate from V1.
Extra delay sensitivity:8test trials each at20ms and100ms delay, prospectively fixed.
No changes during any evaluation. Trials are uninterrupted with fixed recovery,
not independent neural initializations; network is unit of inference.

C0 frozen, C1 reward STDP, C2 unmodulated STDP (reward1), C3 within-four-training-
trial permutation of actual reward-to-eligibility assignments, C4 independently
permuted balanced training labels. Minibatches4 for all plastic conditions.
Training decoder and traces reset only at condition start; common initial state.
C5 memoryless linear B-only; C6 linear [A,B] and nonlinear [A,B,A*B] histories.
C7 diagnostic only: remove trial-wide population mean from four response features;
identical fitting/validation, not causal activity-matched neural intervention.

Separate probe ridge readout: intercept, feature scaling from probe-fitting only;
ridge alpha grid[0.1,1,10], validation balanced accuracy selects first maximum,
threshold0.5; reserved labels used only in final scoring. C0–C4 identical protocol.
Delay tests reuse the same frozen decoder; no refitting.

Primary: network-balanced held-out accuracy(C1)-accuracy(C0), percentage points.
Meaningful effect5pp, paired95% Student-t CI lower>0, all controls reported.
With n2 these are descriptive pilot gates, never confirmatory scientific PASS.
Report every trial and confusion matrix; no bin/pulse pseudoreplication. No exclusion
except numerical invalidity, which stops acquisition and retains HOLD.
Secondary: weight changes/bounds, response rates, decoder learning curves, delay,
separability. These do not rescue the primary endpoint. C7 is descriptive only.

## Mandatory engineering and resource gates
Mechanistic tests first: analytical pair timing, decay, reward signs/zero, disabled,
clipping, simultaneity, checkpoint, replay and frozen evaluation. Required controls
must be executable before neural pilot. No label access outside training update.
Benchmark original construction and1s simulation before pilot; count all condition/
trial durations including delay tests. Fixed900s global pilot wall budget, separate
120s mechanism/benchmark budget, <=2GiB worker RSS and <=200MiB output. Qualified
supervisor, independent outer watchdog and partial persistence, unchanged deadline
semantics. Forecast with2x measured margin plus60s cleanup/analysis; if>900s do not
launch pilot, report resource HOLD/NOT RUN. No budget extension or smaller post-hoc
study. Complete historical regression suite before final engineering decision.
No neural scientific acquisition before committed protocol and all gates.

## Prospective implementation clarification before pilot acquisition
Training and probe decoders use 0/1 labels and threshold0.5; the initially zero
training prediction chooses class0. Ridge penalizes the intercept as well as
coefficients (same for every condition). C3 permutes four actual rewards within
each completed minibatch; eligibility is retained from each trial endpoint, not
counterfactually recomputed. C4 permutes balanced training labels once. Evaluation
weights freeze after32trials. C7 uses within-trial sector-mean subtraction, not
between-condition activity matching or a causal firing-rate intervention.
All conditions carry identical non-delivering eligibility instrumentation.
Reserved split labels are read only for scoring/archives after predictions.

Executed resource probe: construction0.569703s,1s neural integration1.048650s,
32020E/E traces,4arrays*8bytes=1024640bytes trace-state estimate (excludes Brian
indices/queues), measured process peak874823680bytes on macOS. Forecast447.230s
using179.2simulated seconds across10conditions and2xmargin+60s. Forecast accepted
for fixed900s pilot. It is an estimate, not a completed-workflow benchmark.
Mechanism/task tests10pass; initial complete suite205pass. No confirmation cohort
is opened. All failed development commands remain archived, including an invalid
Brian identifier and a test comparison of NaN-initialized public filter fields;
field-wise numerical equality including NaN masks replaced Python NaN equality.

### Typed-boundary repair, before any neural trial completed
First pilot process was rejected before integration: task builder passed NumPy
float scalars where the original API requires plain Python floats. Convert scalars
without changing numeric currents, schedules or equations; retain failure. Resume
only under the FIRST pilot's original absolute900sdeadline, never a reset budget.
No features, rewards, learning or test outcomes were generated before rejection.
