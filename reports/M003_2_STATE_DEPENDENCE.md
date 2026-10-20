# M003.2 — State-dependent stimulation-response identification

**Execution PASS; scientific superiority FAIL. Retain input-only FIR as the intervention-response reference.** The origin-rate interaction worsened reserved1s response prediction on all10 development networks. This result does not establish universal neural state independence, invalidate M003, rescue a control protocol or demonstrate a controller.

## Preservation, revisions and scope

Started clean on `research/m003-1-model-necessity`, exact revision **fd003766d2dc1774e4ba2fce086f092e2736d41d**. Created `research/m003-2-state-dependence` from that revision. All1253 historical tracked files remain byte-identical, including M001 architecture, M002/M002.1 authority failures, M002.2 conditional screen, M002.3 calibration failure, M003 positive ARX-versus-AR evidence and M003.1 FIR-versus-ARX negative finding. No historical scientific protocol, simulator, fixture or result was edited.

Preregistration commit **7c82912** precedes new neural acquisition. Acquisition implementation revision **1ce720e**; complete selection/scoring source revision **c15b477**. Source hashes, actual CLI, environment, working-tree evidence and protocol digest accompany every stage. Exact evidence/final publication revisions are recorded in the closure below and final mission response. Entirely simulated research; no new acquisition/selection on IDs10–14 or locked100–119, no controllers, adaptation, plasticity, neural tuning, hardware integration or merge.

The complete frozen specification is [007_M003_2_STATE_DEPENDENCE_PROTOCOL.md](../docs/research/007_M003_2_STATE_DEPENDENCE_PROTOCOL.md). The [pre-scoring design review](evidence/m003_2/DESIGN_REVIEW.md) identifies limitations before reserved outcomes were scored.

## Frozen hypothesis and causal information

Primary H1 required STATE to beat frozen-form FIR(q10) on reserved1s mean intervention-minus-sham MSE by **>=10% mean paired relative benefit, >=.04Hz² mean absolute benefit, positive paired whole-network95% lower CI, and positive benefit in>=8/10 networks**. STATE must also beat the shuffled-state interaction with positive paired CI lower bound. These are new M003.2 engineering decisions, justified before acquisition by practical effect size and continuity with M003.1 magnitude standards; they are not retroactive acceptance criteria for M003. Relative denominator floor.04Hz² was never activated. Ten networks, not spike bins or restored branches, define replication.

Three claims remain separate: observations predicting future activity; observations modifying predicted intervention effects; state-informed decisions improving outcomes. Only the second is primary. ARX absolute-rate forecasts address a secondary part of the first. No experiment here tests the third.

For each trial, the original zero-input neural trajectory runs0–35s. Original causal rate filter initializes15s. Calibration[15,25)s supplies496 trailing100ms averages of the four completed20ms filtered E sector rates. Their25th/75th percentiles define prospective LOW/HIGH thresholds. At predetermined200ms boundaries25.2–35.0s, select the first completed scalar below/equalLOW and above/equalHIGH. Selection never reads hidden voltages, connectivity, true gain, future activity or counterfactual sham.

**Both origins have zero preceding stimulation over the entire backbone.** At each selected origin, evaluator saves exact neural/filter/delay/refractory/clock/monitor/prior-input state, runs all7 branches from it, restores it and resumes the zero trajectory. Branch outcomes cannot influence later selection. The fixed35s backbone is completed even after both strata are found. All106 origins were found; none required scan extension, threshold change or replacement.

Reserved LOW scalars ranged10.5097–14.4437Hz, HIGH12.1314–15.8733Hz across networks/repeats. These marginal ranges overlap because thresholds are local to a trial; each trial's HIGH is above its LOW. Reserved LOW origins occurred25.2–26.8s and HIGH25.2–28.4s. All preceding delivered exposure was exactlyzero. Sector and elapsed-time distributions, every candidate, thresholds, scalar and full histories are preserved in raw evidence and `origins.csv`. These are observational strata, not experimentally randomized neural states.

## Executed design and mathematical correspondence

Only networks0–9; fresh noise26/27 FIT,28 selection/empirical intervals,29/30 RESERVED. Full-prefix zero-effective-coupling fixtures networks0–2/noise31. Root20261018 and frozen parameter/OU/action SeedSequence roles unchanged. Parameter roles0–3 use replicate0, OU role4 is keyed by absolute1s blocks, action role5 uses newblock32. All53 parameter hashes and memberships match historical M003.1 instances. The unchanged substrate has1000 recurrent E/I LIF neurons,100us integration, original current/delay/noise distributions,20 recording channels and four original observed E sector outputs. The80 recorded E and20 recorded I cells remain disjoint from200 directly stimulated E cells; only the four observed E rates become model outputs/features.

Each origin receives seven2s branches: sham; four90pA single-channel holds with requested durations100/400/200/600ms and prospectively rotated allocations; two120pA pair pulses requested[0,.1) and[.6,.7)s; four500ms random slots from the original16-vector bank, with100ms zero guards. All patterns appear in both strata with identical desired/ramped/delivered histories. Original0–120pA/channel, total<=240pA, slew<=30pA/tick constraints remain unchanged. All actual receipts matched the predeclared ramped requests; **zero violations/fallbacks**.

Single-channel total exposures are9/36/18/54pA*s; paired pulses48pA*s, including tails. Random exposures are recorded individually rather than inferred from steady-state amplitudes; terminal pulses need not include a subsequent tail beyond2s. Nominal model charge=50×exposure pC, effective charge=g×nominal (zero for null fixtures). Desired scientific holds are proposals; actual command requests are the admissible ramped schedules. No model uses desired currents in place of delivered training inputs. Planned future commands are equally available to all forecasts, and execution verifies delivery equality.

Completed53 trials =1855 backbone seconds +742 restored branches×2s =**3339 simulated seconds**. There are106 origins; primary confirmation contains40 origins×6active patterns, repeated within10 independent networks. Per network, fitting has24active episodes but only4origins/two noise streams. Half-data fitting has12episodes/two origins/one noise stream. No poorly responsive case was excluded.

For origin o, action a and future bin k, training effect is

\[
 d_{o,a,k}=r_{o,a,k}-r_{o,S,k},\qquad
 x_k=[u_k^\top,\ldots,u_{k-9}^\top]^\top,
\]

with exactlyzero input history before origin. FIR predicts `x B`. STATE predicts `[x,z_o x] B`, where `z_o=(a_o−FIT mean a)/max(FIT SD a,.1Hz)` and a is the trailing100ms observed scalar. No intercept: a zero plan has exactlyzero effect. No future observation or sham outcome is an input. This explicit interaction can express effect modification that additive ARX contrasts structurally cannot.

**Training uses completed paired simulator counterfactual labels for both primary families.** This is a deliberate model-necessity study, not a demonstrated online biological calibration method. Fitting and selection open only26–28 outcomes. Reserved origin histories/plans are separate archives; all forecasts were finalized and hash-sealed before the evaluator opened29/30/31 branch outcomes. For descriptive absolute-rate prediction FIR/STATE add the same last completed sector-rate vector; ARX recursively uses its declared four completed observed lags. No future sham is available to any predictor.

## Models, budgets and conditioning

All direct-effect models fit the same2400 rows/network, same response labels,10input lags/200ms support, fit-only RMS scaling with floor1, no feature centering/intercept. STATE adds only one scalar×input interaction, not a neural network. Ridge candidates .0001/.001/.01/.1, globally selected using noise28 equal-weight1s validation effects; ties within1e−12 choose larger penalty. ARX(p4,q4) is secondary and fits2800 absolute rows/network including sham, with original centered/scaled ridge form and unpenalized intercept; its penalty uses validation absolute error. Its different response/fitting information is explicitly secondary, not a primary matched comparison.

| Model | Features | Coefficients | Selected penalty | Standardized rank | Condition range |
|---|---:|---:|---:|---:|---:|
| FIR |40|160|.01|40|100.57–207.47|
| STATE |80|320|.1|80|112.00–228.97|
| STATE_SHUFFLED |80|320|.1|80|112.00–228.97|
| FIR_SHUFFLED |40|160|.0001|40|100.57–207.47|
| ARX |32+intercept|132|.1|33|66.73–101.26|

All200 candidates and50 half-data fits were finite and valid; no candidate/family fallback, unstable selected recursion or ill-conditioned interpolation. No coefficient clipping. Every coefficient, scale, singular value, rank, penalized condition and ARX radius is archived. Direct FIR/shuffled FIR receive no state argument; STATE receives just the causal scalar. Future plans enter every family equally. No optional sector-specific interaction was fitted given the small number of independent origins.

## Complete primary numerical comparison

MSE inHz² of the **first1s mean effect**, averaged over4sectors,6active actions,2strata,2reserved noise repeats within each network. This is not mean per-bin error. STATE benefit=FIR−STATE, so positive would favor STATE.

| Network | FIR | STATE | State shuffled | Input shuffled | ARX | STATE benefit |
|---:|---:|---:|---:|---:|---:|---:|
|0|.125410|.149701|.119943|.220654|.124850|−.024292|
|1|.086870|.140900|.129212|.284014|.105053|−.054029|
|2|.081270|.092553|.083783|.230899|.081156|−.011283|
|3|.092345|.095840|.095724|.173187|.096234|−.003495|
|4|.222441|.236529|.215588|.343251|.189024|−.014088|
|5|.104331|.120135|.098812|.199005|.111151|−.015804|
|6|.105748|.119726|.122426|.172820|.098843|−.013977|
|7|.136417|.144438|.140154|.223699|.141311|−.008021|
|8|.073016|.078300|.075079|.184344|.070290|−.005284|
|9|.169015|.195734|.164463|.452042|.194250|−.026719|
|Mean|**.119686**|**.137386**|.124518|.248391|.121216|**−.017699**|

Absolute benefit **−.0176992537Hz²**, paired whole-network bootstrap95% CI **[−.0275434214,−.0102333682]**. Mean paired relative benefit **−16.2858%**, CI **[−27.7552%,−8.7556%]**; no denominator floor. Positive networks **0/10**, required8/10. STATE also loses to shuffled-state: improvementCI **[−.0198969199,−.0059262712]Hz²**. Every frozen scientific guard fails; this is **FAIL**, not a positive result with a nonsignificant interval.

Every noise replicate/action/stratum/sector is retained: `results/analysis/{episodes,sectors,networks,network_replicate}.csv`, full predictions under `results/models`, and machine arrays `results/analysis/data.npz`. No bin/pulse was treated as an independent neural network. Bootstrap10000 whole-network draws, seed20261102, paired models/actions/noise kept together.

## Secondary endpoints and negative controls

| Mean effect MSE Hz² |20ms|200ms|1s|2s|
|---|---:|---:|---:|---:|
|FIR|.060976|.198181|.119686|.073473|
|STATE|.059975|.213179|.137386|.079327|
|State shuffled|.058967|.210474|.124518|.076562|
|Input shuffled|.101452|.351650|.248391|.155966|
|ARX|.057941|.195291|.121216|.074255|

The tiny20ms STATE point advantage does not pass or rescue the1s hypothesis;200ms/2s are worse. FIR beats input-shuffled FIR at1s by.128705Hz²,95% CI[.094803,.170462], supporting useful stimulation-history information. The stratum-swap state control performs better than STATE on reserved data, despite slightly worse validation loss; it does not support useful observable-state interactions. This permutation can invert rather than destroy information, as preregistered, so it is not interpreted as a universal independence test.

Actual pooled HIGH−LOW1s paired response difference=**−.040663Hz**, network95% CI[−.111269,.032718]. Per-network pooled effects are .006966,.179248,.038410,−.142603,.009576,.045974,−.117846,−.245735,−.092223,−.088395Hz (networks0–9). Sector-specific effects/intervals are preserved; one sector has a negative descriptive interval, not a prespecified corrected confirmatory claim. Heterogeneity and a nonsignificant pooled contrast do not establish hidden-state independence.

Mean1s absolute-rate MSE: FIR1.213159, STATE1.230070, ARX.168762Hz². ARX can predict baseline relaxation much better than adding a constant origin rate to a direct-effect kernel, while not improving intervention contrasts. That distinction is central: predicting absolute activity is not demonstrating state-dependent intervention responsiveness.

Validation-derived nominal95% empirical effect intervals had reserved1s coverage93.33% FIR,91.77% STATE,93.44% ARX; mean halfwidths .6564,.6501,.6610Hz. Biases −.03886,−.04727,−.04394Hz respectively. Noise28 serves both selection and interval calibration, with dependent origins/actions/sectors; these are descriptive, not certified/conformal coverage. All horizons, residual lag1 correlations within branches and scalar-mean replacement ablations are in the archives.

With half fitting data,1s MSE rises to.147593 FIR and.266337 STATE (full .119686/.137386). Half-minus-full95% CIs are[.010147,.048958] FIR and[.023819,.311101] STATE. This is limited sample-efficiency evidence with only one versus two fitting noise streams, not a scaling law or an outcome-driven calibration extension.

Zero-coupling fixtures produced **exactlyidentical spikes, counts, filtered rates and whole-population totals across all actions and sham**. Actual effectzero, demonstrating the measured causal response depends on physical coupling. Frozen g1 predictors, not informed ofg0, still forecast nonzero effects: FIR1s false-response RMS .6216–.8790Hz, STATE .5175–.9258Hz, ARX .6052–.8447Hz. Thus zero-coupling prediction generalization fails; it is not silently called correct because the instrument control passes. No model is claimed to detect an unobserved gain loss.

No-input sham effect forecasts are exactlyzero. Shared initial-input histories give identical FIR effects in LOW/HIGH; state labels/history mutation affect only the declared feature. Future input mutation cannot change earlier forecasts, and unreadable reserved future-outcome files do not affect the origin-only loader. Every reserved random sequence is freshly seeded and preserved, without selection on performance.

## Verification and actual resources

Actual commands and stage status/timers: `evidence/m003_2/{commands.md,stages.json}`. Full regression suite: **83passed,25existing deprecation warnings,49.50s**; the historical74 tests remain unchanged. Initial81-test run and9-test targeted run are also retained. `pip check`:no broken requirements; compilation succeeds. Existing CI automatically runs the new tests. No installation/download or dependency change.

New tests cover scalar causality/history mutation; independent bilinear ridge recovery and zero-input behavior; FIR future-input mutation/no state access; all fixed schedules and constraints; exact network-gate replication units; ARX timestamp/recursion alignment; exact neural restoration and receipts/membership; reserved-outcome loader separation; fitting/state-shuffle boundaries. Independent preselection count/filter/timing audit passed255 FIT/validation archives without opening reserved responses.

Independent post-acquisition verification passed all**53trials,795observation archives,250coefficient sets,460seven-action common-origin forecast sets** (3220individual2s forecasts), parameter/membership preservation, event-to-count binning/filter mathematics, threshold/first-crossing state selection, all receipts/exposure/noise identities, selected penalties, scores/intervals and network-bootstrap gate. A further106 actual neural-prefix checks confirm that R and sham have identical observations during their shared first100ms zero input, despite different future commands. Exact replay is additionally executed by regression fixtures, rather than inferred solely from state hashes. This is separately implemented analytical verification in this session, **not external investigator or alternate simulator replication**.

Deterministic reanalysis reproduced15 regenerated numerical/CSV/PNG/SVG artifacts byte-for-byte and all scientific comparisonJSON fields; only measured runtime differs. The curated committed-layout copy was independently verified again; the extended audit including106 neural-prefix and secondary-statistic checks passed in9.271s. Full raw35s backbones and every branch/event/count/receipt, plans, labels, origin histories/checkpoint hashes, realized parameter/noise hashes, coefficients, forecasts, source/environment/configuration manifests and all outcomes are preserved. Neural checkpoint payloads are in-memory Brian stores during acquisition; seeds, complete zero backbone and source reconstruct them, with hashes/assertions verifying restoration.

Acquisition **1618.0285wall seconds** (26.97min) for3339simulated seconds, aggregate2.064simulated seconds/wall second across3workers. Initialization range .015714–.078659s; peak recorded workerRSS **1339768832bytes** (~1.248GiB), not measured simultaneous aggregate memory. Fitting/selection/intervals/sealed forecast subprocess6.819s; evaluator1.709s; deterministic figures15.407s (font/cache costs included); independent verifier8.746s. All preregistered stage caps respected. Scientific analysis internal timer1.386s; process startup/IO explain its difference from subprocess wall.

Environment: Python3.12.15, Brian2 2.10.1, NumPy2.5.4, Matplotlib3.10.8, pytest9.1.1, macOS26.5.2 arm64; full CPU/memory/build identity in environment.json. Apple Accelerate BLAS, requested VECLIB/OMP/OPENBLAS limits1, actual threading unverified. Concurrent local tests/IO and warm caches mean these are actual workload costs, not isolated single-thread benchmarks. Final inventory/disk accounting is in verification_manifest.json; no large sweep beyond the frozen53trials.

## Scientific interpretation, limits and next experiment

**Execution PASS; scientific FAIL.** A transparent interaction with the causal global recorded-origin-rate scalar did not improve reserved1s intervention-response prediction; it worsened all10 networks and failed the state-label control. Retain FIR(q10, globally selectedpenalty.01 in this new direct-effect study) as default for this tested response task. Keep ARX as a secondary absolute-rate predictor. M003.1's different fitting design/penalty and prior results remain unchanged.

Main limits: only four fitting origins/network; one scalar masks sector/synchrony/history information; one-second averaging hides fast effects; ten previously studied development networks and two reserved noise repeats do not establish new-network/biological generalization; observational strata do not randomize hidden state; paired counterfactual training is simulator-specific; short validation/interval calibration and stratum-swap controls have declared limits; fixedg1 models cannot diagnoseg0 without evidence. No claim of full state independence, optimal FIR, biological relevance, controllability or better decisions follows.

Next falsifiable experiment: preregister network-disjoint confirmation of a FIR learned from **observation-only randomized calibration, without paired-sham training labels**, scoring evaluator-only held-out intervention contrasts on fresh noise. Test whether the simple kernel retains useful prediction under that deployable information constraint and stationary versus hidden efficacy change. Freeze cohort, meaningful errors and controls first; do not add controllers or retrospectively engineer another target. This experiment is proposed only, not started.

M003.2 stops here. No merge or automatic follow-on implementation.
