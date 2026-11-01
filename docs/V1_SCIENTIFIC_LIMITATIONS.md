# Scientific scope and limitations of V1

NEUROMANCER V1 is an **in silico research platform**, not a biological computer. Its evidence consists of simulated neural trajectories and numerical verification. No living preparation, offline biological validation dataset, CL1 device or Cortical Cloud experiment underlies these results.

## What the control comparison establishes

In the frozen M005B development cohort (10 network identities, two noise replicates each), mean post-loss cumulative tracking error was 11.46875 Hz·s for PI, 13.12922 for RLS predictive control and 18.97781 for fixed predictive control. RLS improved on its frozen-model comparator but lost to PI on every network. The preregistered conjunction therefore failed. This is neither adaptive superiority nor statistical equivalence of controller families.

Independent M007 recomputation uses raw observed E-population counts, the original baseline-derived target and the full 16–64 s post-loss window. Noise repeats average within networks before paired bootstrap inference. Spike bins, checkpoints and pulses are not independent network replications. These are development networks with prior research history; new controller validation networks 10–14 and locked networks 100–119 were not evaluated. No held-out controller generalization is established.

## Mechanisms remain unresolved

Model mismatch, planner cost weights, a 180 ms input history, slow coefficient forgetting, weak closed-loop excitation, prediction uncertainty and PI feedback robustness are plausible explanations for the performance difference. No causal ablation isolated these mechanisms. A better predictor can still produce worse control. Reduced dose and lower final-window MAE do not replace the frozen cumulative-error criterion.

The full four-channel FIR representation is not independently identifiable from C02-only calibration. Some online input windows lack persistent excitation. Coefficient projections are not physical gain estimates. A hidden multiplier changing from 1 to 0.6 represents actuator efficacy loss; it is not neural plasticity or biological learning. The network itself has no STDP or adaptation rule.

## Instrument and safety scope

The substrate is a simplified recurrent E/I LIF network with exponential synaptic currents and colored noise. Physiological fidelity and transfer to real neural populations are unvalidated. Stimulation is model-injected pA per cell, not electrode current, voltage, charge density or a hardware-safe waveform. MAX/C02 measurements establish finite empirical authority, not the full mathematical reachable set.

Observation, stimulation and integration clocks differ: 20 ms public bins, 1 s controller aggregation/planning, and 100 µs neural integration. Virtual-time causality is qualified; physical hardware real-time execution is not. Measured planner latencies on one host do not establish worst-case execution bounds or CL1 compatibility. macOS suspend-inclusive timing uses qualified APIs and injected-clock tests; no deliberate physical sleep/resume qualification was performed.

DELAY/DROP diagnostics withhold due observations and discard stale data. Their identical online absence does not validate a network transport implementation, arbitrary delays or hardware buffering. POSIX process-group supervision does not contain malicious descendants that escape their group. Linux support requires actual hosted qualification; Windows is outside the qualified supervisor scope.

## Historical negative findings remain valid

- V0.1's +4 Hz authority criterion failed. Later objectives do not revise it.
- V0.2 prospective calibration qualified 0/10 networks; its failure remains recorded.
- M003.1 did not demonstrate ARX superiority over input-only FIR for the 1 s intervention contrast. It did not prove equivalence or universal lack of state information.
- M003.2 scalar state-input interactions failed the reserved response-prediction comparison. This does not imply biological state independence.
- M004 qualified specified prediction and one-sided residual-shift detection tasks under probing. Its validation causal-effect interval crossed zero, uncertainty coverage was poor and repeated alarms limited event precision. It did not qualify causal diagnosis, controller superiority or biological adaptation.
- M005A.5 short-horizon recovery failed. M005A.7's later prospective 64 s success applies only to its own horizon and conditions.
- M005B adaptive superiority failed against PI. Its successful comparison against fixed MPC cannot rescue the conjunction.

## Future work requires new authorization

Retain PI as the supported tracking reference for this task. Independently frozen replication or information-budget experiments may investigate the unresolved mechanisms. Validation and locked-network access require their own satisfied gates; M006 remains HOLD. Biological integration would additionally require documented hardware APIs, approved access, stimulation/recording characterization and a separately reviewed experimental protocol. No such integration or biological experiment is implemented or authorized by this release audit.
