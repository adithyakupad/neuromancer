# ADR 001 — Brian2 first, small experimental boundary

Status: **selected design; implementation and scientific efficacy unexecuted**. Date 2026-10-18. Evidence: [ecosystem audit](001_ECOSYSTEM_AUDIT.md). Scope is entirely simulated dynamics. Offline biological identification and prospective living-preparation experiments require separate protocols and evidence labels.

## Decision and alternatives

Choose **C in a deliberately narrow form**, implemented initially as **B: Brian2 runtime backend**. One Python package, one process per trial, one backend and ordinary functions. Define only the three operations needed by an experiment: initialize a fresh trial, advance causally with a bounded command, close. Separate observation from privileged evaluator diagnostics. No plugin discovery, backend registry, server, frontend, universal signal schema or hardware-shaped core. A second backend must demonstrate a concrete mismatch before expanding the contract.

| Criterion | A: own simplified neural engine | B: established engine only | C: thin experiment contract, Brian2 first |
|---|---|---|---|
| Scientific credibility | Must independently qualify integration/events/RNG; high error risk | Mature solver and scheduler evidence | Same evidence, with explicit observation restrictions |
| Biological interpretation | Explicit equations but no automatic validation | Flexible published model families | Same initially; compare model dependence later |
| Engineering complexity | Own dynamics, delays, plasticity and control | Smallest first script | Slight boundary cost; three operations only |
| First validated experiment | Delayed by engine qualification | Fastest | Nearly B if abstraction stays small |
| Maintenance | Highest for neural numerics | Mostly experimental code | Moderate if extensions remain deferred |
| Reproducibility | Entire burden local | Engine seeds/checkpoints; global state still managed | Adds run identity/stream/split ownership |
| Performance | Unknown, likely NumPy first | NumPy/Cython/C++ choices; measure runtime feedback | Minimal wrapper overhead; engine dominates |
| Hardware portability | Requires new interface later | Brian-specific controller leakage possible | Units/clocks/receipts explicit; hardware remains a separate adapter |
| Model diversity | Expensive to add mechanisms correctly | Equations accommodate LIF→AdEx→STDP | External engine later only when needed |
| Overbuilding risk | Building another simulator demo | One-off coupling | Universal abstraction risk, actively limited |

Reject A for V0: our contribution is causal identification/control methodology, not an ODE integrator. A tiny analytical linear plant is a software fixture, not our primary neural substrate. Do not rebuild Brian's synaptic events, monitors, units or checkpoint machinery.

Reject full general C now: Brian2 and NEST cannot promise identical snapshot semantics, wall-clock operation or RNG behavior. An offline dataset cannot implement counterfactual advance. Hardware cannot restore a neural preparation. Keep optional capabilities explicitly absent rather than faking universal support. NEST trials use fresh processes/replay, not mandatory Brian-style snapshot APIs.

## Model selection

| Model | What it adds | Role / reason to defer |
|---|---|---|
| Linear state space | Known identifiability, controllability, Kalman/LQR assumptions | M3 analytical fixture and fitted local predictor, insufficient neural substrate |
| Nonlinear latent system + point-process observations | Nonlinear hidden dynamics and spike likelihood | Useful if validated linear predictors fail; confounding/nonidentifiability and fit cost require justification |
| Independent LIF | Threshold/reset/refractory and input nonlinearity | Single-cell unit tests; lacks recurrent indirect stimulation effects |
| Recurrent E/I current-based LIF | Recurrent excitation/inhibition, partial access, delays, saturation and stochastic drive | **V0 substrate**, smallest model that tests network-mediated intervention and gain drift |
| Adaptive IF / AdEx | Adaptation-driven history dependence and excitability drift | First mechanism stress test after frozen V0; distinguish adaptation state from prescribed efficacy drift |
| Plastic spiking network + STDP | History-dependent synaptic efficacy | Q3 only; requires trace/weight tests, frozen/reversed-rule controls and post-stimulation retention |
| Conductance HH/compartments | Voltage-dependent channels, morphology and electrotonic filtering | Only if question depends on waveform, compartments or field effects; parameter burden exceeds V0 need |

E/I label and a .8 excitatory fraction do not demonstrate a balanced asynchronous regime. Rate/excitation/inhibition distributions must be reported in the feasibility gate. Prescribed input-gain drift is **not synaptic plasticity**. The point of V0 is to quantify a boundary of control under sparse recordings and constrained *model current*; it does not model extracellular electrical stimulation physics.

## Controller selection and fairness

1. No stimulation and identification-selected constant current are essential reference behaviors. A fixed periodic pattern controls for patterned delivery without feedback.
2. PI with saturation and anti-windup is the main competitive simple comparator. Tune it on the same development networks and objectives as MPC. It may handle gain drift adequately and make adaptation unnecessary.
3. LQR is a diagnostic on the fitted augmented linear state only when stabilizability/detectability and unconstrained operating range hold. Clipped LQR does not solve constrained optimal control; no V0 success claim depends on it.
4. Fixed-model constrained MPC separates prediction/planning benefits from model updates.
5. Online adaptive MPC differs from fixed MPC only through causal parameter/covariance updates. Same estimator, target, horizon, cost, solver, stimulation bounds and calibration data.
6. Uncertainty-aware/information-seeking control is later: first validate prediction intervals and excitation tradeoffs. An uncertainty penalty alone is not robust stability.
7. RL/deep learning deferred. Admit only after a prespecified simpler-model failure that the additional nonlinear representation can address, with matched data/action budgets and held-out networks. Do not use game score as a surrogate for causal control evidence.

## Dependencies and extension policy

M1: Python 3.12, Brian2 2.10.1, NumPy, pytest; record exact resolved versions. M3 adds SciPy for ridge/optimization and statistics only. No JAX, PyTorch, GUI, database, Docker, MPI, NWB, cloud client or SDK requirement for V0. Use stdlib JSON metadata and numerical NPZ chunks (`allow_pickle=False`); append-only event JSONL. Add plotting only for the scientific report. Keep existing repository .venv untouched during this mission; implementation agent creates/qualifies an agreed environment later.

Apple Silicon CPU and Linux CPU implement identical experiment semantics, but numerical tolerance/trajectory equivalence is measured rather than bitwise assumed across platforms. No requirement for Metal/CUDA. If runtime mode is too slow, profile the actual loop, then qualify Cython; standalone acceleration changes feedback semantics and needs a separate design decision.

## Critical self-review and ranked unresolved risks

| Priority | Challenge / strongest simpler explanation | Mitigation / stop condition |
|---|---|---|
| 1 | Sparse observations and positive-only current may not control or identify target rate; direct stimulation can dominate | Randomized calibration, held-out pulse tests, record unstimulated E neurons, preregister reachable targets. Fail feasibility without selecting only responsive networks. |
| 2 | Gain-loss perturbation was designed to favor adaptation; PI may explain any apparent benefit | Include stationary, gain increase, smooth drift and observation-dropout conditions; matched tuning, PI and oracle diagnostic. Claim novelty only for a mapped failure boundary. |
| 3 | Paired noise breaks if action changes RNG consumption; snapshots omit hidden state | Exogenous innovations indexed by trial/time/neuron, action-independent streams; test replay/chunking including synaptic queues; trial processes isolated. |
| 4 | Fitted ARX appears predictive from autocorrelation, not identified intervention effects | Input-shuffle/replay controls, held-out randomized pulse responses and no-input predictor; distinguish forecast from causal identification. |
| 5 | LIF and current injection omit culture bursting, artifacts, extracellular recruitment, neural drift biology | Narrow simulation claims; later AdEx and independent engine/model tests, then separate authentic-data protocol. |
| 6 | One rate target is too easy and control theory reproduction lacks novelty | Publish a null if tuned PI matches MPC; report cost/performance frontier and observability/delay limits. A two-week result may be a rigorous benchmark, not a novel algorithm. |
| 7 | Positive results reflect privileged state, leaked tuning or subset selection | Controller receives masked past bins only; splits and parameter choices frozen before test; all networks/failures reported. |
| 8 | Conditional calibration targets restrict generalization | Predetermined target formula and eligibility; report full cohort plus eligible descriptive strata. No claim for arbitrary neural states. |
| 9 | SDK callback timing, license constraints and tissue limits remain unknown | Optional later conformance gate; no biological/cloud access implied. |
| 10 | Plasticity claims based on acute rate change or broad summary fits | V0 disables plasticity; Q3 requires explicit rule ablations and post-washout retention. |

No requirement here needs an event bus or reusable controller superclass. Runtime state belongs to the substrate, estimator/controller state belongs to the trial, split/model-selection state belongs to the experiment configuration. The evaluation remains meaningful if adaptive MPC fails: identify when PI suffices, when identification fails and when targets are unreachable. Those are valid negative outcomes.

Mission architecture review can accept this design without claiming that controllability, physiological validity, MPC benefit or biological portability has been demonstrated. The roadmap gates are required experiments, not accomplishments.
