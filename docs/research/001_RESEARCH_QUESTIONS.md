# Mission 001 — Three falsifiable simulation studies

Date 2026-10-18. All proposed outcomes are **in silico**. No study below has been executed. Statistical replication means independent network realization, not spike, bin, electrode or repeated noise seed. For all studies, split network identities before selecting preprocessing, model orders, controllers or target rules; within-test online calibration is explicitly permitted and identical across methods.

## Prior art and novelty limits

Primary references accessed 2026-10-18:

- [Newman et al., 2015, Optogenetic feedback control of neural activity, eLife 4:e07192](https://elifesciences.org/articles/7192): feedback rate clamping and adaptation to changing network excitability already have experimental precedent. Merely demonstrating rate tracking with PI or MPC is not novel.
- [Proctor, Brunton & Kutz, 2016, Dynamic Mode Decomposition with Control](https://epubs.siam.org/doi/10.1137/15M1013857): distinguishing autonomous dynamics from actuation is established system identification. ARX here is a transparent baseline, not a new theory.
- [Shahaf & Marom, 2001, Learning in Networks of Cortical Neurons](https://marom.net.technion.ac.il/files/2016/07/2001-J.-of-Neurosci.pdf): conditioning and stimulation withdrawal in cultured networks precede this project. A modeled weight change cannot establish the same biological mechanism.
- [Kagan et al., 2022, Neuron](https://doi.org/10.1016/j.neuron.2022.09.001): embodied culture experiments motivate stimulation/recording loops, not claims of simulated sentience or biological learning from game performance.
- [Wagenaar, Pine & Potter, 2006, BMC Neuroscience 7:11](https://doi.org/10.1186/1471-2202-7-11): culture bursting is diverse. Matching broad statistics alone is weak validation. BL-1 source's J Neurosci citation for this title is inconsistent with the original publication.

## Q1 — Where does partial observation stop supporting useful intervention identification?

**Hypothesis:** In fixed E/I LIF networks, at 10% neural recording coverage, a lagged input-output predictor trained on randomized stimulation will reduce held-out 200 ms evoked-response prediction MSE by at least 15% versus an otherwise identical no-input predictor, and fixed MPC will reduce tracking RMSE by at least 10% versus a development-tuned PI at matched stimulation cost. These are two separate claims; prediction improvement does not imply control improvement.

Motivation: population autocorrelation can masquerade as identification. Quantify the recording coverage and stimulation location at which intervention effects remain identifiable. Requires causal current injection, persistent recurrent state, fixed channel maps, masked observations, intervention/no-intervention paired replays and private evaluator access. Brian2 suffices; plasticity disabled.

Independent variables: observed fraction {5%,10%,20%}; aligned versus disjoint stimulation/recording memberships; calibration input budget {15,30,60} s; held-out targets and stimulation patterns. Mechanism parameters fixed by the V0 family. Dependent variables: one-step and 200 ms response error, causal-response contrast bias, RMSE, cost and controller failure. Randomize calibration amplitudes independently of neural noise; for held-out response probes compare injected and sham from identical model state/exogenous stream. Counterfactual differences are meaningful only inside this specified simulator.

Baselines: persistence/no-input AR, ridge ARX, linear-state fixture with known ground truth; no stimulation, fixed pattern, tuned PI and fixed MPC. Competitive fit budgets and identical causal filters. Negative controls: shuffled input timestamps, zero actuation map, replayed observations unaffected by stimulation, equal-current random channel assignment. Full-state controller is an evaluator-only upper-bound diagnostic, never a fair primary competitor.

Replication: 10 train/5 validation/20 test networks with 3 repeated noise streams each; aggregate repeats before inference. For this broader coverage study use a separate locked manifest from Q2's primary test, or label any reused test cohort as exploratory. Paired network-level bootstrap CI on MSE/RMSE differences; correction for two confirmatory claims and coverage comparisons. Do not call 60 repeats 60 independent networks.

Falsification: input model fails the prespecified MSE gain, or MPC fails the matched-cost advantage; report each separately. Failure modes: low signal, saturation, hidden recurrent state, poor excitation, latency/filter loss, direct response dominates recurrent response. The likely simpler explanation for a positive result is ordinary local input-output control. Novelty would require a reproducible observability/actuation/delay failure map across mechanisms/backends, not one favorable trace. Biological claims need known stimulus timing, artifact masks, independent preparations and held-out response recordings with real causal intervention.

## Q2 — Does online identification earn its cost under unannounced efficacy drift?

**Recommended V0. Hypothesis H1:** After a hidden 40% loss of stimulation efficacy, adaptive MPC reduces post-change tracking RMSE by at least 10% versus the stronger of development-selected fixed MPC and PI, while increasing mean absolute delivered-current cost by no more than 10%, with no constraint violations. Require positive network-level uncertainty evidence and no material stationary-regime harm. Exact paired contrast and gates in [V0 protocol](002_V0_PROTOCOL.md).

Motivation: real systems can drift, but adaptation may be redundant when integral feedback compensates. Test the incremental benefit of model updates under restricted observation, rather than constructing a task where only an adaptive controller is allowed useful feedback. Requires runtime change to a hidden input-gain parameter, matched exogenous noise, private gain logs and causal adaptation. No neural plasticity mechanism is asserted.

Independent variables: stationarity, step-down/step-up/smooth gain drift, observation dropout; fixed partial observation and held-current budget. Primary change is g:1→.6 at 30 s of test; onset and direction are unavailable to controller. Dependent variables: tracking RMSE, current cost, transient recovery, saturation/fallback and identified intervention-prediction error. Random assignment of controller order/process IDs cannot change network/noise realization. All controllers receive same calibration, targets, masks and constraints; adaptive MPC receives no extra excitation in the primary experiment.

Simple/competitive baselines: no stimulation, calibration-selected constant, fixed periodic, anti-windup PI, fixed-model MPC. Adaptive uses same MPC solver/horizon/cost and initial model; only online RLS differs. Oracle-known-gain is exploratory diagnostic. Negative controls: stationary networks; frozen adaptation with identical code path; input-time shuffle for causal model validation; zero actuation map; yoked action replay on fresh noise. Random observations/replay are software-null controls, not neural substrates.

Replication/splits: exact 10/5/20 independent network split and three test noise streams per protocol. Train selects defaults; validation chooses hyperparameters and the stronger baseline; test permits only prescribed per-network pretest calibration and causal online updates. No retraining/tuning from held-out outcomes. Network bootstrap after repeat aggregation; stationary and cost gates prevent favoring adaptation by design.

Falsification: <10% advantage, CI inconsistent with benefit, excess current cost, stationary harm or instability. A valid failure says PI suffices or local identification cannot keep up under these conditions. Strongest positive alternative explanation: extra effective gain/integral action or greater stimulation. Control these with PI, cost matching and frozen-adaptation ablation. Potential originality is a transparent quantified boundary of when online identification is worth its cost under sparse observation and limited actuation; this is not automatically a novel control algorithm. Two weeks can credibly produce positive, negative or inconclusive results if feasibility gates pass.

Before biological claims: independent authentic stimulation-response data, artifact-corrected observation, realistic recruitment/gain drift, replicated living preparations and approved prospective protocol. Offline replay cannot prove online controllability; biological recording alone cannot establish counterfactual stimulation response.

## Q3 — Can activity-dependent plasticity leave a selected functional change after stimulation ends?

**Hypothesis:** Under explicit bounded excitatory STDP, a feedback-selected stimulation schedule increases a prespecified A→B evoked-response contrast by at least 20% relative to a matched-charge yoked schedule, and this increase remains during a 60 s zero-stimulation washout/probe period, without an equivalent rise in global firing rate. Use between-condition difference of pre-to-post contrast, not acute firing during training.

Motivation: distinguish guided change in modeled synapses from transient excitability, input drive and selection of initially favorable networks. Requirements: fixed neuron groups A/B/C, bounded trace STDP (specified tau+/tau− and learning rates), saved full weight/trace state for evaluator, paired training histories, controlled probe schedule. Brian2 STDP is preferable first; qualified BL-1 later tests mechanism dependence. Homeostasis/STP are initially disabled so mechanism attribution is possible, then tested as stress mechanisms.

Proposed independent variables: STDP enabled/frozen/reversed timing rule, contingent versus yoked stimulation, input-response delay {10,20,50} ms and washout time. Dependent variables: held-out probe probability contrast P(B spike in 5–50 ms|A probe) minus corresponding C response; mean E→E weight change by group, firing rate, burstiness and retention trajectory. Training uses 300 s of <=1 Hz group-A pulses with feedback reward/withholding based on B versus C counts; controls replay an identical pulse/charge schedule from another network. Probe before/after using 100 randomized A-versus-sham pulses, independent noise streams, STDP frozen during probes. Fix target groups before inspecting activity.

Baselines: no training, open-loop regular stimulation, matched-charge random schedule and yoked replay; contingent schedule must not receive more pulses or richer observations. Negative controls: frozen weights, reversed STDP window, shuffled feedback labels and reset-to-pretraining weights while preserving other state. Acute change that vanishes on washout or persists equally with frozen weights falsifies the proposed plasticity explanation.

Replication: 10/5/20 fresh independent networks, 3 noise repeats; train chooses pulse policy and rule strengths, validation locks thresholds, test entirely unseen. This is a later standalone study, not another outcome mined from V0. Bootstrap the network-level between-policy pre/post contrast; probe trials are repeated measures, not independent preparations. Correct the two confirmatory endpoints (functional contrast and washout retention), report all firing/instability effects.

Falsification: <20% relative contingent benefit, CI includes no effect, no washout retention, global-rate elevation explains response, or controls reproduce the effect. Failure modes include runaway weights, saturation, post-selection, arbitrary accelerated learning rates, test probes inducing plasticity and regression to mean. Novelty requires robust model/rule dependence and a control objective beyond known conditioning; STDP implementing a designed association is expected. Biological interpretation needs longitudinal evoked responses, stimulation-artifact handling and pharmacological/other mechanism controls; weight matrices inferred from a model do not demonstrate synaptic changes in tissue.

## Ranking and sprint recommendation

Scores are planning judgments on a 1–5 scale, **not measured probabilities**. Chance of a credible two-week result means a properly qualified positive *or negative* finding, not likelihood of hypothesis success.

| Study | Scientific value | Feasibility | Potential technical originality | Two-week credibility | Rank |
|---|---:|---:|---:|---:|---:|
| Q2 efficacy drift | 4 | 4 | 3 | 4 (highest; conditional on feasibility) | 1 |
| Q1 observability boundary | 4 | 4 | 2 | 4 (close second, broader sweep deferred) | 2 |
| Q3 guided plasticity | 5 | 2 | 3 | 2 (lowest; timescale/mechanism burden) | 3 |

Implement only Q2 V0. Include a small randomized-identification check from Q1 as an eligibility/interpretation gate, not the full coverage sweep. Defer Q3 until acute control and prediction are characterized. If Q2's physical model assumptions fail feasibility, stop and amend the protocol before opening test outcomes; do not switch to plasticity or RL to rescue the narrative.
