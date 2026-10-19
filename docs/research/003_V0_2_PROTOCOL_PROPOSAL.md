# V0.2 protocol proposal — noise-aware, asymmetric rate regulation

**Conditional proposal, not an executed controller experiment.** The frozen V0.1 is [002_V0_PROTOCOL.md](002_V0_PROTOCOL.md); its +4 Hz authority gate FAILED in M002/M002.1 and remains failed. No file or result in that historical protocol is amended here. All claims are restricted to entirely simulated dynamics. The M002.2 report will state whether this proposal passes its development reachability screen or remains HOLD.

## Scientific objective and decision boundary

Investigate whether constrained feedback can regulate a partially recorded **unstimulated E population** between two positive excursions above baseline when actuator efficacy decreases, and whether online model updates add anything beyond strong feedforward/integral feedback. Positive-only stimulation provides no presumed ability to suppress below the natural zero-input baseline. This is an asymmetric rate-regulation question, not arbitrary hidden-state control or plasticity.

M002.2 preregisters a minimum high−low span of1 Hz and at least two standalone-noise SD at the selected evaluation timescale, plus lower-confidence reduced-gain headroom on >=8/10 development networks. The fastest of100 ms-filter tracking and1 s rate-epoch regulation that satisfies **all** those rules may be proposed for confirmation. If neither qualifies, this document is **HOLD**; do not shrink the minimum, remove weak networks or implement a controller to rescue it. Passing this screen is not controller qualification. A1 Hz floor is an engineering choice (~8% of a typical13 Hz baseline), not a universal biological threshold. The two-SD rule is a prespecified challenge screen, not a theorem bounding closed-loop noise suppression or mathematical controllability.

A slower objective changes the scientific claim and evaluation bandwidth, not the20 ms recording interface or100 ms causal filter. For the slow candidate, raw counts summarized over nonoverlapping1 s epochs are the explicit rate statistic; the existing filtered signal remains the causal controller input and a mandatory diagnostic. M002.2 standalone1 s noise is measured from those raw count epochs. A continuously updated trailing1 s summary may be logged, but primary epoch scores use fixed nonoverlapping boundaries. Never substitute the smoother after inspecting controller performance.

## Unchanged substrate, interface and policy scope

Use precisely M002 Brian2 2.10.1, N=1000 (800E/200I), original topology/weights/delays/OU, dt=.1 ms, original four stimulation groups and20 disjoint recording channels. No inhibitory ablation, adaptation, STDP, neuron selection, observation thinning or extracellular-field model. Currents remain0–120 pA/channel, total<=240 pA, slew<=30 pA/channel per20 ms. Physical observation stays20 ms counts with validity, coverage and integer-us timing; scalar y is the mean of the four original causal100 ms-filtered E sector rates. Only delivered actions and available past observations may enter predictors/controllers.

To avoid an unnecessary spatial optimization problem, **all primary policies use the same fixed C02 mix** u=(q,0,q,0),0<=q<=120 pA, |Delta q|<=30 pA/tick. This is an explicitly restricted implementable policy class within the original actuator bounds, not a modification to those bounds. C02 was selected on prior development data; it is not retuned per held-out network. Equal-channel D60 remains an evaluator-only response reference during development, not a privileged competitor. Later spatial control requires a separate protocol; no claim of optimal allocation.

This common mix also avoids treating two perfectly correlated active channels as independently identified inputs. A future scalar-input predictor is sufficient; no new substrate abstraction or software architecture is required.

## Target construction and calibration allowance

Everything defining a target must precede control and use permitted recordings, never evaluator-only activity, true current gain, held-out control outcomes or the best hindsight action.

For each network/noise trial:

1. Burn5 s at zero, baseline10 s at zero, b from the final8 s exactly as V0.1. Preserve sector/count/filter state.
2. At g=1, run **32 s** static calibration: alternating4 s zero and4 s C02 holds with q=30,60,90,120 in this order. Every onset/offset uses ordinary slew; score the final3 s of each block. Compute h(q) as that hold's raw observed E mean minus the immediately preceding zero block's final3 s mean; h(0)=0. No sham noise oracle is available to the controller. Use h(120), never a maximum over outcomes, as R_cal. Record the complete nonmonotone map; do not isotonic-fit away a failure. Require positive R_cal and strictly increasing h at the sampled dose levels for calibration qualification; a flat or nonmonotone map is a recorded failure without replacing the network.
3. Freeze R*=.6 R_cal. Fixed conservative factor.6 is a declared design-range assumption, not online access to hidden g or its change time. Targets are L=b+.1R* and H=b+.9R*. No clipping, floor substitution or upward rescaling to reach1 Hz. Record span=.8R*. A small span is a failed minimum-challenge gate, not a valid easier trial.
4. Four-second zero-current washout. Then30 s randomized identification on C02: proposals q in{0,30,60,90,120} every100 ms, uniform from original role5 calibration stream; slew-limit every20 ms. Initial24 s fit, final6 s chronological reserve; no random time-bin splitting.
5. Eight-second reserved probe: eight1 s cycles, desired q=120 first100 ms then zero, with unchanged slew and recovery. This is evaluation, not refitting or target construction. A separate paired-sham evaluator replay uses identical state/noise, absent from policy input. Four-second zero washout follows. Carry filter/lag state causally; no retrospective baseline update.
6. Checkpoint common control start, then restore it before each policy/condition. At this point all targets and model-selection choices are fixed. Prefix totals93 s (15+32+4+30+8+4). Log any nonqualification, even if the simulated trial remains finite.

Global hyperparameters may be selected only on validation networks after development confirmation. Per-network precontrol calibration is deployment-like conditioning, not global tuning. This prospective target rule differs from M002.2's paired scientific response estimator: M002.2 is a screen, **not evidence that this exact single-prefix calibration is reliable**. The next experiment must test that gap explicitly before controller implementation.

## Mandatory fresh development confirmation

Before opening validation/test networks, use all training IDs0–9 with five new noise replicates8–12. Do not reuse the M002.2 noise5–7 to confirm the data-informed scale choice. Run the exact permitted static calibration above and evaluate fixed sham, C120 and calibration-derived L/H lookup holds at g=1/.6; no feedback controller or ARX fitting is necessary for this next gate. The later identification/probe prefix is deferred during target-calibration qualification: its prefix is51 s (15+32+4).

For each noise replicate construct targets from the actual g=1 preceding-zero calibration. From its exact common checkpoint run eight6 s branches (S, C120, L lookup, H lookup at each gain), reporting full and final5 s. Lookup uses q_eff=piecewise-linear inverse of the permitted g=1 h map at the target excursion, then q=q_eff/g under the evaluator-known experimental gain. This known-gain lookup is an evaluator-only reachability assay, never a fair blind-controller competitor. Ramp normally; if q>120 or the map is nonmonotone, record infeasibility without clipping targets or replacing the network. These actual low/high holds also test unmeasured low C02 currents and interpolation; endpoints alone do not validate a continuous reachable interval. Network confirmation uses paired differences across the five noise replicates. Require >=8/10 networks simultaneously to have:

- baseline1–30 Hz, sector means<100 Hz, finite states and no timing/constraint/replay failures;
- mean target span>=1 Hz and >=2×standalone SD at the **locked** evaluation scale;
- lower95% t-CI of (reduced-efficacy late response − target high excursion)>=0;
- no calibration-map qualification failures among its five replicates;
- mean across noise of |final5 s rate−target|/that trial’s span<=.25, separately at each L/H and each gain, reporting every error and its across-noise CI. This is mean-output calibration, not feedback tracking under noise.

No target clipping or network exclusion. Report all component counts and every network. A borderline/inconclusive gate calls for a separately preregistered precision study, not an automatically enlarged favorable sample. If it fails, HOLD and revisit the scientific objective or separately version the substrate; do not open test cohorts. Confirmation never converts V0.1 into a pass.

## Hypotheses and minimum meaningful challenge

Only after confirmation and implementation qualification:

**H1 (feedback utility):** Under hidden gain1→.6 loss, anti-windup PI reduces mean per-network post-change RMSE by>=10% relative to the validation-selected strongest target-aware open-loop baseline, with mean absolute-current cost increase<=10%, benefit CI excluding zero, and <=5% stationary RMSE harm by an upper95% bound. This tests useful feedback before claiming adaptive-model novelty.

**H2 (incremental adaptation):** Adaptive-model MPC reduces mean per-network post-change RMSE by>=10% versus the stronger validation-selected comparator among PI and fixed-model MPC, at <=10% mean current-cost increase, no primary constraint violations/aborts, and <=5% stationary RMSE harm. Same initial model, solver, horizon, cost, observations and actuation as fixed MPC; only causal parameter updates differ. H2 failure is a credible null even if H1 passes. The cost guard makes H1 a joint resource-efficiency claim: if feedback needs more current to correct an underdriving open-loop policy, report the tracking improvement and dose increase separately rather than calling feedback ineffective. Preserve the full open-loop scaling cost/error frontier, including the higher-current candidates. Do not claim novelty merely because the target is scaled to an observed response.

Run60 s control: alternate L/H in10 s blocks, starting L; hidden gain drops at30 s in the primary condition, stationary g=1 control. Targets remain identical across conditions and policies; the gain change time/direction is absent from policy input. Every plateau is nonzero above baseline; recovery to baseline and below-baseline suppression are not mislabeled symmetric control.

If fast scale qualifies, primary outcome is RMSE of existing y at20 ms. If only slow scale qualifies, primary outcome is RMSE of raw observed E counts/(80×1 s) on fixed1 s epochs over the60 s control window; target constant within each epoch. Policies still use the same20 ms y feedback. Report y-RMSE, raw20 ms RMSE, epoch RMSE and transition response in every case. Slow success does not imply precise100 ms tracking. A no-input baseline, optimal fixed policy and cost/noise floors must be shown, not just an attractive trace.

## Competitive baselines and model comparisons

All receive the same prefix, target trajectory and constraints. No policy knows hidden gain or future observations. All target-aware policies may know the declared future setpoint trajectory, including PI feedforward.

- **Zero:** q=0, exposing the nonzero-excursion challenge.
- **Constant:** q selected from{0,30,60,90,120} using calibration map closest to(L+H)/2−b; tie lower current. One q throughout, ordinary slew.
- **Target-aware open loop:** piecewise-linear inverse of h(q) at current target excursion, clipped to0–120 then slew. Nonmonotone map is a calibration failure, not silently repaired. Multiplicative feedforward factor in{1,1.3,1.6}, selected globally on validation balanced across stationary/gain-down conditions. Include an optional scalar1 s precomputed target lead in{0,.2} s on the same validation grid; no phase selection on test. Preserve all candidates. This is stronger than a fixed constant or generic periodic baseline.
- **Fixed periodic:** the prespecified pulse/periodic pattern with best development mean performance-cost diagnostic can be retained as a secondary baseline only after its identity is locked before validation; it cannot replace target-aware open loop if weaker. Its exact identity and score must be documented, or omit it from confirmatory claims.
- **PI plus target feedforward:** e=target−y; q=project(q_ff+Kp e+Ki integral) to[0,120] intersect prior±30. Integrate at20 ms only when unsaturated or error moves back toward feasibility; no hidden integrator windup. Kp in{2.5,7.5,22.5} pA/Hz, Ki in{.5,2.5,10} pA/(Hz s); same feedforward scaling/lead choices as open loop. Choose on balanced validation criterion, not gain-loss alone.
- **Fixed/adaptive MPC:** one-output scalar-input ARX with four rate lags: y_(k+1)=c+sum_(l=0..3)a_l y_(k−l)+b_q q_k. Six coefficients; action is delivered q on[t_k,t_(k+1)), output becomes available only at t_(k+1). Fit first24 s randomized calibration with rate/action scaling from that prefix, floors1 Hz/1 pA; intercept unpenalized, ridge in{.1,1,10} chosen on reserved6 s. No privileged state or online feature rescaling. Validate200 ms and1 s intervention forecasts against no-input AR, persistence and shuffled-input null; >=10% response-MSE reduction is required on development reserved probes before model-control claims.

Fixed/adaptive share1 s horizon (50×20 ms), the same scalar q constraints and causal y targets. Objective sum_h[(predicted y−target)/max(H−L,1 Hz)]² +rho(q/120)² +.05(Delta q/30)², rho in{.01,.1,1}. Using a1 s horizon is a proposal choice to cover the slower target window; no performance has been measured. Use a qualified convex quadratic solver with analytic objective/constraints, SLSQP ftol1e−8/maxiter100 as existing design default; infeasible/unsuccessful solve is logged fallback, not silently projected optimal MPC. Both log predictions and latency. Select shared rho by mean fixed/adaptive validation score; forgetting factor{.995,.999,1} only for adaptive. Its causal RLS update and covariance/denominator/freeze rules are exactly specified in V0.1, with dimension6 instead of21; no extra adaptive excitation. A future implementation must qualify numerical solver/model stability before any held-out run.

Validation score is primary-scale tracking MSE/(max(span,1 Hz))² +.1 mean(q/120)², equally weighted stationary/gain-down. Ties lower delivered current, then simpler method/no lead/lambda1. Report unequal tuning grids explicitly. Pick primary H1 open-loop and H2 stronger PI/fixed comparator globally on validation, ties simpler policy. Report all baselines regardless. No RL/deep model is authorized as a fallback.

## Cohorts, uncertainty and cost

Keep original network split:0–9 development;10–14 validation;100–119 test. None outside0–9 were evaluated by M002.2. Test three new noise repeats13,14,15 per network; roles0–3 remain replicate0, all exogenous innovations use unchanged time-indexed OU. Calibration role5 follows the same replicate IDs and freezes proposal arrays before running. Never let spikes/actions alter random consumption. Each policy/condition restores a common prefix state and matched noise. New calibration is allowed on held-out networks, but no tuning after their outcomes.

Do not exclude unreachable/failed test networks or report only an eligible subset. Report each failure and primary feasibility failure for the complete cohort. Simulator numerical/timing faults invalidate instrument qualification. A finite but unreachable calibrated target invalidates the planned controller efficacy claim; it is not a missing data point. No favorable replacement seed.

Record nominal/effective summed current, aggregate model charge, squared-current cost, saturation and slew activity separately; no energy claim. q commands imply summed channel current2q and aggregate model charge50×sum_j u_j Delta t. All policies have identical0–240 pA total budget and no charge exemption during ramps, calibration or fallback. Compare current costs over the same primary [30,60) s window. Relative current-cost guard uses max(reference,1 pA) denominator and reports absolutes. Costs from prefix are equal across methods and reported separately.

Primary analyses average three repeat metrics within each network, then paired network bootstrap10,000 draws seed20261024. Never pool20 ms bins or60 trials as60 network units. Relative RMSE improvement uses max(reference RMSE,.1 Hz) denominator, with absolute changes and floor incidences reported. H1/H2 benefit claims form a family: Holm correction of two paired network sign-randomization tests (100,000 fixed draws, seed20261025); also report descriptive pointwise95% bootstrap intervals. Require the prespecified magnitude, benefit interval lower>0, corrected p<.05 and both cost/stationary guards. No confirmatory claim if tests/intervals disagree. Effects near noise floor remain a null/inconclusive result, not an incentive to change smoothing.

Report pre-change[0,30), post-change[30,60), stationary60 s and transition30–35 s; full-window scores include all transients. Secondary: MAE, tracking of full fixed hidden E evaluator-only, epoch error, overshoot, fraction within±span/4, recovery after drift first2 consecutive1 s epochs within±span/4 (censored at30 s), prediction bias/MSE/coverage, fallback/abort, latency and >20 ms decision fraction. These are descriptive unless separately multiplicity-qualified.

## Negative controls, failures and next step

Require existing replay/chunk/timing/isolation/g=0 regressions; zero effective coupling must yield exact same neural response for all schedules. Input-time-shuffle >=1 s and no-input/persistence baselines must challenge identification. Replayed observations independent of actions must defeat causal-control claims. Frozen-update adaptive ablation must match fixed-model behavior within solver tolerance. Stationary control, balanced tuning, matched input costs and anti-windup PI guard against a benchmark constructed to favor adaptation. Yoked schedule on fresh noise is exploratory feedback-specific evidence, not a replacement for the primary baselines.

Missing observations, invalid outputs or solver failure use the unchanged bounded ramp-to-zero; log every tick. Three consecutive fallbacks abort. No primary successful-controller claim with any delivered violation or abort. No fabricated zero spikes for dropout. Base experiment does not add dropout/artifacts; those require a separate stress protocol.

**Next authorized mission, if requested, is calibration/target confirmation only**, not controller implementation. If neither scale passes M002.2, prioritize a separately preregistered dose-response/evoked-response identifiability question or a separately versioned substrate whose biological/modeling motivation is explicit. Do not raise weights/current, change recorded membership or lower the minimum span merely to rehabilitate V0.1. Substrate redesign would create a new model family and preserve this family's negative result.

The proposed confirmation budget is50×(51+8×6)=4950 simulated seconds, with the same three-worker/75 min ceiling as M002.2; it must receive its own preregistration before execution. It is not run here.

Future full test resource plan must be separately locked. With seven policies×two conditions×20 networks×three repeats,60 s branches alone total50,400 simulated seconds, plus93 s prefixes×60=5,580 s. At M002.1 CPU throughput this is roughly6.3 h on three workers (planning estimate, not a new benchmark); include calibration/probe replay and contingency before approval. No such run is performed by M002.2.

## Measured M002.2 disposition

Development screen: **HOLD**. Fast scale 3/10, slow scale 7/10 (required >=8/10). Selected scale: **none**. Component counts and uncertainty are in [M002.2 report](../../reports/M002_2_REACHABILITY.md). No target floor, model or constraint was changed to improve this result.

**Do not adopt V0.2 for controller benchmarking.** Preserve it as a conditional design. Prioritize a separate stimulation-response/evoked-effect identification objective, or the explicitly preregistered calibration/precision confirmation if that unresolved gap warrants the cost. If the research goal requires larger/faster excursions, a separately motivated and versioned substrate redesign is needed; do not tune this model to rescue its historical result.

M002.2 diagnosis suggests a **new slow1 s calibration/precision confirmation**, explicitly still HOLD. If that follow-up is requested, lock slow scale before its outcomes rather than rerun a fastest-passing-scale search. All ten point-mean reduced responses exceed their candidate highs, while networks6/7/9 fail the lower-confidence-bound gate; network9 misses by.000456 Hz. This is a reason to test calibration/precision with fresh noise, not to round the present gate into a pass.
