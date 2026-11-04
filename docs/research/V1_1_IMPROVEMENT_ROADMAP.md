# V1.1 scientific improvement roadmap

2026-11-04. Research design only. No new controller study preregistered or acquired.
Baseline release source `abd811a0`; final publication review `7d63b1f5`.
Design branch `research/v1-1-proposals`, separate from performance implementations.
All future experiments need complete prospective cohort/seed/endpoint/budget freezes.
Locked100–119 remain closed; development failure does not authorize M006.

## Evidence and claim boundary

Frozen M005B: PI11.46875, adaptive RLS13.12921875, fixed MPC18.9778125 Hz*s.
Adaptive beats fixed prediction-based control, loses to competitive PI. This establishes
an empirical ordering for this development task, not its mechanism, biological relevance
or independent-network generalization. Preserve V0.1/V0.2 failures, M003.1/M003.2 model
superiority failures, M004 distinct identification/detection results, M005A.5 failure and
separate M005A.7 finite-horizon success. Never retune on M005B reserved outcomes.

## Ranked smallest useful studies

| Rank | Proposal | Expected benefit / scientific value | Effort / failure risk | Reproducibility risk | Hardware independence / relevance |
|---|---|---|---|---|---|
| 1 | Bias/disturbance rejection factorial | may explain PI advantage; benefit unknown | small–medium / medium | medium, changes controller | simulated; relevant to both culture stimulation and drifting electrode readouts |
| 2 | Held-out multistep calibration/uncertainty audit | tests whether planner trusts wrong horizons | small / low as diagnostic | low if replay-only | entirely hardware-independent |
| 3 | Excitation identifiability audit with dose-matched probes | separates poor identification from planner limitations | medium / medium | medium, new input/noise protocol | independent; relevant to stimulation budgets |
| 4 | Missing/delayed/channel-failure robustness | quantifies graceful degradation beyond existing faults | medium / medium | medium, corrupted observations need separate seeds | independent; broadly useful for implant/culture recordings |
| 5 | Supported compiled runtime backend qualification | potentially largest measured runtime opportunity; unmeasured gain | medium–high / high | high, changed float/codegen paths | independent; no hardware throughput inference |
| 6 | Nonlinear but transparent dose/kernel model | addresses saturation if held-out residual evidence warrants | medium / high | medium; avoid complexity fishing | independent; no neural-net default |
| 7 | External stimulation-annotated MEA validation | tests response kinetics/recording assumptions | high / high | high, data rights/annotation/units | public-data dependent; closer to cultures, not living closed-loop evidence |
| 8 | Second simulator / independently justified plasticity | tests model-family generalization / a different question | high / high | high | no device needed, biological claims still unqualified |
| 9 | Official CL SDK simulator adapter | interface portability, no automatic scientific benefit | medium / medium | medium, SDK/version/sample clocks | official contracts/access required; no Neuralink API assumed |

No accuracy/speed gain is assigned a number without measurement. Priorities1–4 should
precede larger model/backend/hardware efforts. Performance P0 identified frequent Brian
setup/GC rather than PI/RLS arithmetic as the largest stepped-path cost. Branch
performance/v1-1-baseline contains profiles; no scheduler bypass is proposed as qualified.

## Competing explanations for PI superiority

| Explanation | Existing evidence | Simplest falsifying experiment |
|---|---|---|
| Baseline/model bias and error integration | PI integrates error; FIR/RLS has different disturbance representation; no causal proof | prospectively fixed shared planner with/without a bounded integral-disturbance term, fixed/adaptive model factorial; same initial data/dose and frozen PI reference. Reject explanation if bias-corrected model control does not reduce error with useful uncertainty |
| Planner objective mismatch | two one-second forecast means plus dose/switch costs differ from48s post-loss IAE | before new neural acquisition, compare archived planner surrogate rankings to independently scored future errors, acknowledging selection bias; then independently preregister one aligned objective vs original under same planner/candidate bank. No current performance refactor changes objective |
| Inadequate closed-loop excitation | C02 restricts independent channel identification; reduced design rank11 vs full41; input variation depends on feedback | report singular values/innovation residuals by chronological window without choosing favorable thresholds; new dose-matched external probe factorial vs unprobed controls. Refute if well-conditioned probing fails to improve response identification/control |
| Adaptation timescale | fixed forgetting factor .999,20ms updates; approximately20s e-folding is algebra, not measured optimality | preregister a small forgetting-timescale grid using new development noise, freeze selection before any disjoint confirmation; include frozen model and PI; no retuning historical result |
| Forecast uncertainty/long-horizon mismatch | point forecasts drive finite planner; M004 interval limitations do not establish M005B mechanism | held-out200ms/1s/2s forecast calibration and prospective coverage, respecting network units; refute if forecasts are calibrated yet planner loses comparably |
| Horizon or feedback robustness | M005A.5 failed short horizon, M005A.7 passed longer; neither isolates MPC mechanism | fixed task/setpoints with prospectively chosen horizons/cost weights as separate scientific factors; no selecting windows after trajectories |
| Actuator authority | constrained indirect control and MAX headroom evidence; neither proves all actions reachable | prescribed shared MAX/sham reference under same targets/gain; distinguish reachable reference from oracle controllability; report controller failure despite demonstrated headroom separately |

Each new study needs a minimum absolute and relative effect, network-level paired CI,
stationary/cost/safety guards, all failures, independent noise within network and a staged
confirmation gate. No bins/pulses as independent networks. Development IDs0–9 only until
new design explicitly qualifies progression;10–14 are not freely reusable reserved data.

## Robustness design, not execution

Prespecify observation faults: masked channels, extra delivery delay, nonnegative spike
corruption, sector dropout. Separate sensor corruption from actuator channel failure and
response-latency changes. Include stationary, abrupt efficacy magnitudes and gradual drift
with externally fixed schedules, matched noise, sham and unchanged PI/fixed MPC. Disallow
true-gain or hidden-state access. First analyze nominal predictive calibration before adding
new E/I families. New families/parameters require separately versioned scientific substrates;
no performance-only adjustment to weights, inhibition, timestep or thresholds.

## Model audit

FIR remains the simplest supported intervention-response family. M003.1 did not show a
meaningful ARX advantage; M003.2 did not show scalar-state interaction superiority. They
do not prove global state independence. First assess chronological baseline intercept drift,
amplitude-stratified residuals, causal kernel latency and multistep uncertainty. A linear
intercept correction or piecewise-linear dose map is a smaller justified experiment than a
neural network. Independent input channels are not identified by C02-only calibration.
Any reduced11-feature representation can change floating arithmetic: qualify it as a new
model representation unless exact predictions/updates/actions are demonstrated.

## Biological and hardware boundary

Obtain stimulation-annotated data with license, units, artifact blanking, recording membership,
timing and preparation metadata. Validate spontaneous/evoked kinetics and held-out response
uncertainty, not just firing-rate similarity. Offline fit is not online biological control.
STDP/plasticity requires an independently motivated mechanism and measured validation, not
an added learning rule to claim biological learning.

Official [Brian2 2.10.1 computation documentation](https://brian2.readthedocs.io/en/2.10.1/user/computation.html)
describes compiled runtime and standalone options. Standalone external Python feedback and
checkpoint lifecycle are not a drop-in replacement for this engine's explicit NumpyCodeObject,
20ms decisions and time-indexed noise. No alternative backend throughput was measured here.

Official [CL simulator source contracts](https://docs.corticallabs.com/cl/sim) describe custom
sources with stimulation-event reactions, stable frame metadata and SDK sample-clock
requirements. These are simulator-only integration opportunities; synthetic frames/spikes
must not be labelled measured MEA voltage. [CL developer guidance](https://docs.corticallabs.com/)
distinguishes built-in random/replay simulation from responsive models and biological access.
Any adapter must separately specify sample-grid conversion, units and causality; SDK parity
is not biological/hardware safety qualification.

[Neuralink's official overview](https://neuralink.com/) concerns decoding neural signals for
external device use. Recording robustness, drift and latency methodology may be relevant;
this simulated stimulation-regulation benchmark is not a Neuralink decoder or validated
implant interface. No public/authorized hardware API or collaboration is assumed.
Primary documentation accessed2026-11-04; none changes the pinned scientific environment.

## Next falsifiable step

Preregister a public-record-only multistep forecast/bias audit on fresh development noise,
with the original controller/task held fixed. Ask whether post-loss forecast bias explains
planner surrogate/error divergence. If it does not, reject the proposed mechanism before
adding integral MPC, new models or probes. This is a proposal, not authorization/acquisition.
