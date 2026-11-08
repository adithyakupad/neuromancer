# Research methods and limits

## What is measured

NEUROMANCER studies constrained intervention-response identification and regulation in a partially observed **simulated** recurrent E/I LIF population. Stimulation enters the current equation and causally changes subsequent activity. Recurrent dynamics, original colored noise, numerical integration and channels remain fixed throughout the identification/control series. The observed E cells and stimulated cells are disjoint: regulation relies on indirect network recruitment.

The complete numerical model is frozen in `docs/research/002_V0_PROTOCOL.md` and qualified in M002. The model has1,000 neurons (800E/200I), Bernoulli directed recurrent connectivity without autapses, exponential excitatory/inhibitory currents, heterogeneous18–22ms membrane constants,200pF capacitance,−65mV rest/reset,−50mV threshold and2ms refractory period. Integration is0.1ms; public observations and held-current changes are20ms; PI and predictive planning use completed1s observations. These distinct clocks must not be conflated. No STDP, adaptation mechanism, extracellular voltage synthesis or biological validation is implied.

M005B keeps original four-actuator constraints (0–120pA/channel,240pA total,30pA/channel/tick) and uses only C02 equal allocation(q,0,q,0). This restriction is substantive: calibration cannot identify independent channel effects because only the C02 subspace is excited. Full ridge estimation does not restore missing independent information.

## Prospective comparisons

A shared original51s calibration prefix supplies every controller identical public data. The target is baseline+1Hz; it is not chosen from future controller performance. Six deployable/reference methods are compared: ZERO, calibrated FIXED, frozen PI10/5, fixed FIR predictive, full-RLS predictive and bias-only predictive. MAX is a separately labeled authority reference. Fixed/adaptive methods share initial model,625 feasible plans,2s horizon and objective; adaptive updating is the intended distinction.

Control lasts64s. The hidden actuator multiplier changes from1 to.6 at16s in LOSS, with STATIC controls. The multiplier is withheld from predictors. This is actuator efficacy loss, not simulated biological plasticity. Common-time exogenous noise and exact checkpoint restoration pair arms at their causal origin. Each controller then creates its own neural trajectory. Online algorithms do not receive sham recordings, future neural observations, hidden voltages or connectivity.

Primary cumulative error includes all48s after loss. A favorable late bias cannot erase poor early recovery. Conversely a failure at the old short horizon remains a failure even if later regulation succeeds. Adaptive superiority requires meaningful improvement against both PI and fixed predictive control, independent-network uncertainty and mandatory cost/stationary/feasibility/safety guardrails. Secondary recovery and predictor metrics cannot substitute for the primary conjunction.

## Replication and uncertainty

Independent sampled networks are the replication unit. Two noise streams within a network are repeated stochastic observations, averaged first. Paired percentile bootstrap resamples whole networks10,000times with fixed PCG64 seed20261105. It does not turn bins, pulses or simulation checkpoints into independent preparations. Development has10networks; conditionally admitted validation has5 and limited precision. These identities have earlier development/model-family history; validation is fresh controller evidence, not a never-inspected model family. Locked100–119 remain excluded unless a separate protocol authorizes them.

Prequential prediction, same-origin counterfactual contrasts and realized closed-loop tracking are different estimands. Shadow predictors run on already observed FIXED/ZERO data and do not demonstrate alternative realized control. Ordinary rate prediction improvement does not prove causal kernel recovery. Intercept compensation, closed-loop regressor endogeneity and weak excitation are explicit competing explanations for adaptive effects.

## Scientific limits

The model is simplified and lacks many biological mechanisms. Published simulation APIs and a reproducible substrate do not validate biological fidelity. No result here establishes living-neuron control, intelligence, neural learning, clinical utility, plasticity, asymptotic stability or a full reachable set. MAX/C02 headroom is finite-bank empirical evidence, not proof of optimal control authority.

A finite-bank predictive optimum minimizes a linear surrogate under its enumerated actions, not the true neural objective globally. FIR support is180ms of past input; for1s holds most forecasts behave as a dose mapping. Full RLS can compensate baseline shifts without identifying the physical gain. No gain-aware correction, RL or neural-network model was introduced to rescue results.

Wall-clock timings are measurements on the reported local host under the saved software stack. Requested BLAS thread limits and soft planner deadlines do not establish hard real-time performance. macOS continuous-clock behavior is grounded in qualified APIs and injected boundary tests; this study does not deliberately suspend the machine and cannot guarantee cleanup while physically asleep.

Every scientific gate is retained even for negative results. V1 claims must be read from the final research report and its complete numerical evidence, never inferred from successful installation or passing software tests alone.
