# M002.2 preregistration — finite-bank reachability

Freeze and commit before any new scientific simulation. Starting clean HEAD aee19dc1c8857b839766619be7f2521521f6eddc, requested branch research/m002-2-reachability. Entirely simulated dynamics. No neural parameter, topology, membership, observation/filter, integration scheme, actuator bound or historical protocol modification. Preserve the V0.1 +4 Hz authority failure. No controller or identification implementation.

## Question and fixed cohort

What observed-population rate excursions do a finite set of simple positive-current actions attain, at g=1 and g=.6, and are they large relative to standalone output noise? This is neither the full reachable set nor a feedback-controller performance test.

Exactly networks0–9, new independent noise replicate IDs5,6,7 (all prior M002.1 replicates0–4 excluded from new noise). Root20261018, unchanged PCG64 SeedSequence keys/roles/block layout; roles0–3 remain replicate0, role4 uses the new replicate/time blocks. Thirty fixed trials, no response-based seed/sample changes, three independent process workers. No networks10–14 or100–119.

Per trial:5 s zero-current burn-in,10 s baseline at g=1; baseline b uses [7,15) s. Save exact state at15 s (neurons, synapses, delay/refractory state, clocks, filter, observation cursors, prior action and noise offset). Restore before every branch. Evaluate every pattern for6 s on [15,21) s, gain order1 then.6. Every action/gain shares the same innovations at the same absolute times. Both sham branches must match exactly. Retain all outcomes, including nonresponsiveness and numerical failure; no replacement of quiet networks. Nonfinite neural state, clock/replay failure or invalid action aborts a trial and yields execution PARTIAL/FAIL, never an excluded observation. Infrastructure retries, if necessary, use identical IDs with old partial artifacts retained.

## Action bank (12 patterns, not an optimization)

Generate desired targets on the20 ms grid, then move every channel from its prior delivered current toward target by <=30 pA/tick, starting at zero. Validate delivered currents nonnegative, <=120/channel, sum<=240. All times relative to15 s. Whole6 s is scored, including ramps; no free preramp.

| Name | Desired pattern, pA |
|---|---|
| S | [0,0,0,0] |
| D7.2 | Constant [7.2,7.2,7.2,7.2] |
| D15 | Constant [15,15,15,15] |
| D30 | Constant [30,30,30,30] |
| D60 | Constant [60,60,60,60] |
| C30 | Constant [30,0,30,0] |
| C60 | Constant [60,0,60,0] |
| C90 | Constant [90,0,90,0] |
| C120 | Constant [120,0,120,0] |
| PERIODIC | [60,60,60,60] in first0.5 s of each1 s cycle, zero in second0.5 s |
| ALTERNATE | [120,0,120,0] first0.5 s of each1 s cycle, [0,120,0,120] second0.5 s; slew crossfade |
| PULSE | [120,0,120,0] first0.1 s of each1 s cycle, zero for remaining0.9 s |

Six complete cycles, onset times0,1,...,5 s. C02 allocation is fixed from prior development evidence, not selected anew. No other concentrated pair, frequency, phase, pulse duration or amplitude is searched. D7.2 is prespecified solely to match PULSE charge. Whole-window summed-channel exposures: S0; D7.2=172.8; D15=360; D30=720; D60=1437.6; C30=360; C60=718.8; C90=1076.4; C120=1432.8; PERIODIC=720; ALTERNATE=1432.8; PULSE=172.8 pA*s. Floating checks use1e-9 tolerance, not exact decimal bit representation. Multiply by50 for aggregate model injected pC, and by g separately for effective drive. These are model quantities, not electrode energy/safety metrics.

Preregistered paired dynamic comparisons: PERIODIC−D30 and PULSE−D7.2 (exact charge matches); ALTERNATE−C120 (exact charge match). Also dynamic−D60 and dynamic−C120 as authority references with their different doses disclosed. Dynamic peaks are not compared as if they were steady whole-window authority. No terminal ramp is inserted: static/ALTERNATE can end nonzero because every branch restores its baseline checkpoint; delivered endpoint is recorded.

## Stored observations and checks

Original observation is unchanged:20 permitted channels, five cells/channel, four E channels/sector and one I;80 recorded unstimulated E cells form the raw population rate; existing causal100 ms filter retained.20 ms half-open bins and integer-us timestamps. Save channel counts, raw/filtered sector rates, actual delivered action for every bin, baseline traces and seeds/config/source hashes. Whole-population spikes are evaluator-only and never feed actions.

For descriptive hidden comparison retain per-neuron total spike counts and20 ms counts of the24 original evaluator groups (observed E80, fixed never-targeted E600, all E800, I200, stimulus groups and sector groups). Reconcile observed counts to neuron/group counts and whole-window totals. Full-network event retention is temporary and does not change neural equations. Checkpoint restores, same-noise hashes, sham equality and parameter/membership identity across repeats are mandatory. Record wall/init/neural/observation/extraction times and worker peakRSS.

## Metrics and inferential units

Primary response: whole6 s observed E rate minus matched same-state sham. Static late response: [1,6) s raw mean minus paired sham. Report every network/action/gain, mean/SD and pointwise95% t-CI over three independent noise repeats (df2 critical4.3026527299). Fixed sham rate and original baseline are separate. Also report filtered mean, evaluator fixed/full E/I and all sector responses. Time bins, cells and repeated pulses are not independent networks or noise replicates.

Population intervals:10,000 hierarchical percentile bootstrap draws, seed20261022, resample10 networks then3 noise replicates within each; same draws across all metrics/actions/gains. Pointwise descriptive CIs; no multiplicity-adjusted significance or biological inference. Finite-bank min/max per-network mean responses and noise-split best (select replicate5; evaluate6–7) are descriptive; selected extrema are optimistic and are never called optimal reachability. Also give fixed C120/D60 ranges without selection. Preserve full time courses, individual outcomes, failures and exposure ledgers.

Noise: original baseline raw20 ms rate SD on [7,15). Sham causal-filter SD and raw-bin SD on [16,21), avoiding first1 s filter initialization. Also sample SD of five nonoverlapping1 s sham rate means on [16,21); this is a temporal variability descriptor, not five independent experimental units. Pool descriptor variance across three noise repeats within network. Compare static late response to standalone sigma at100 ms-filter and1 s block scales. Matched-noise contrasts remove much exogenous variation and overstate real-time discriminability if used alone.

Discrimination diagnostic, no fitted dynamics: for each gain and network, use replicate5 to set nearest-class-mean midpoint thresholds on1 s block observed rate-minus-baseline values [1,6) for S vs C120, D30 vs D60, and D60 vs C120. Freeze orientation and threshold, evaluate only replicates6–7. Report balanced accuracy per evaluation replicate then per network. Aggregate CI resamples networks, after averaging two evaluation repeats; five1 s blocks are repeated measures, not inference units. This tests simple readout distinguishability on known network identities/new noise, not hidden state observability or topology generalization.

Timing: for static D60/C120, mean the three paired filtered response traces within network, use late raw response R as reference; if R<.25 Hz mark latency unresolved. t50 is first completed bin within1 s exceeding0.5R for3 consecutive bins; report grid20 ms and descriptive per-network values, no sub-bin causal-delay claim. Neural and100 ms filter delay remain confounded. Dynamic event summaries use cycles1–5 (exclude first cycle); average cycles within each replicate before noise/network summaries. PERIODIC off-command at.5 s reaches delivered zero at.52 s; PULSE off-command at.1 s reaches zero at.16 s. Peak response is max mean filtered trace in [0,.5) PERIODIC or[0,.3) PULSE. Decay t20 from actual delivered zero is first3 consecutive bins with absolute mean response<=20% peak before next cycle; peak<.25 unresolved. Report right-censoring/unresolved, not fabricated time constants. Quantify fixed postpulse [.3,.9) s and periodic off [.6,1) s response, including possible undershoot. These do not establish sustained below-baseline control. ALTERNATE sector structure is reported phase-wise; a changed aggregate scalar is not hidden-state controllability.

## Candidate-objective rule, frozen before outcomes

This is a feasibility screen for a new proposal, not retrospective V0.1 success. Engineering minimum challenge: **>=1 Hz high−low excursion**, plus >=2 standalone-noise SD at the proposed evaluation scale; at typical13 Hz baseline this is a nontrivial modulation, not a biological minimum. Fix this floor now and do not lower it after results.

For network n set R*_n=.6 times its mean C120 g=1 late paired response. Candidate target levels are b+.1R* and b+.9R* (80% range span,10% nominal headroom). This selection uses response evidence, not adaptive-controller performance; no hidden outcomes choose targets. Gain uncertainty is checked empirically: high level must be <=lower pointwise95% noise CI of measured C120 g=.6 late response. No network clipping, target-floor substitution or removal.

Evaluate the same candidate at two prespecified scales: (i) unchanged causal100 ms filtered-rate tracking; (ii) slow1 s rate-epoch regulation using the same20 ms observations and100 ms filter, with1 s trailing averages as declared evaluation summaries (not replacing simulator observations). Gate at each scale: >=8/10 networks satisfy span>=1 Hz, span>=2*sigma_scale, high<=reduced-gain response lowerCI, baseline1–30 Hz, finite state. Choose fastest qualifying scale. This gate is deliberately conservative with only3 repeats; a failure can reflect precision as well as range. Always report each component count, individual-network margins, no criterion changes. Slow success does not qualify fast tracking. If neither qualifies, recommend HOLD/alternative objective or separately versioned substrate redesign; do not shrink targets until pass. V0.2 can be a conditional proposal with explicit new confirmation gates, or a no-go recommendation.

A future per-network calibration must derive target scale from only allowed precontrol g=1 recordings and the fixed conservative .6 multiplier; the paired scientific range is not a controller oracle. Exact prospective calibration/confirmation split, strong open-loop/PI/fixed/adaptive comparisons, cost/hypothesis/failure criteria will be specified in the separate proposal. No method is implemented or performance measured here. An additional fresh-noise confirmation is mandatory before any held-out-controller study, especially if a scale passes this development screen.

## Budget, stopping and acceptance

Thirty prefixes15 s plus720 branches6 s = **4770 simulated seconds**, three workers. M002.1 measured4750 s in1932.963 wall seconds; estimate30–45 min here (not a benchmark). Budget75 min wall, <=three simulation processes, peak combined expected<5 GiB, disk<250 MiB; original16 GiB machine. No current StateMonitor, no large sweep/dependency install/GPU. If infrastructure cannot finish budget, retain all partial data and declare PARTIAL; do not sample favorable subsets. Do not stop for low/high response. Retries only identical failed IDs with provenance.

Execution PASS requires all30/720 cells, full constraints/replay/sham/count/provenance checks and original regressions. Scientific V0.2 feasibility is separate and may fail. Original V0.1 authority remains FAIL regardless. Stop after report/proposal/verified review-branch commit; no merge and no ARX, PI, MPC, RLS, RL, plasticity or hardware code.
