# V0 protocol — Partial-observation rate control under efficacy drift

Protocol version 1, designed 2026-10-18; **not run or empirically qualified**. Research category: **entirely simulated neural dynamics**. Primary question Q2 in [research questions](001_RESEARCH_QUESTIONS.md). Freeze this document, executable config, splits and analysis before test execution. Any post-test change starts a new protocol version and labels previous tests as development evidence. No physiological or hardware-safe limits are inferred from these parameters.

## Hypotheses and estimands

H1: after g:1→0.6 stimulation-efficacy loss, adaptive MPC improves mean per-network post-change RMSE by >=10% over one competitive baseline selected on validation (PI or fixed MPC), with mean current-cost increase <=10%, no delivered constraint violations and no primary trial aborts. Positive benefit CI must exclude zero. H2 guardrail: stationary adaptive performance is noninferior to the same baseline within 5% relative RMSE, using an upper 95% bootstrap bound. If H1 passes but H2 fails, reject the combined benefit claim.

Primary estimand is tracking the **observed, unstimulated excitatory-neuron population rate** of this simulator family, not all hidden state. Full unobserved E-population tracking is a secondary evaluator-only outcome that tests whether success generalizes beyond recorded units. Neither constitutes biological computing, learning, clinical efficacy or tissue control.

## Neural substrate and parameters

All numeric constants below are **engineering defaults** selected for a small interpretable current-based SNN. Leak/threshold/time-constant orders are conventional modeling choices, not measurements of CL1 or a particular culture. The .8 E fraction, connectivity and input amplitudes are not fitted biological values. See the ecosystem audit and cited modeling literature; no claim of published physiological calibration attaches to this parameter set.

| Quantity | Frozen default |
|---|---|
| Population | N=1000, 800 E +200 I, no plasticity/adaptation |
| Topology | Directed independent Bernoulli p=.05; no autapses, one edge/pair. Presynaptic E positive, I negative; recurrent connections across all groups. |
| Partition | Four arbitrary sectors, each 200 E/50 I. They are channel-membership labels, not a measured spatial MEA. |
| Membrane | C=200 pF; tau_m independently Uniform(18,22) ms per neuron; R_i=tau_m_i/C. E_L=-65 mV, V_reset=-65 mV, V_threshold=-50 mV, refractory=2 ms. |
| Initial state | V independently Uniform(-65,-50) mV with exclusive upper endpoint; I_E=I_I=0, OU deviation=0; recurrent delay queues empty. |
| Synapses | Current exponential E tau=5 ms, I tau=10 ms. Per-edge E jump independently Uniform(12,18) pA; I jump Uniform(-72,-48) pA. Delay per-edge Uniform choice {1.0,1.1,...,2.0} ms. |
| Background | I_bg=180 pA + eta_i; independent OU eta, stationary SD=40 pA, correlation tau_noise=5 ms. Same mean and SD all cells. |
| Integration | Fixed dt=.1 ms, explicit Brian clock. Update OU first, then deterministic linear V/I equations using exponential Euler; threshold, delayed events and reset in Brian's explicit recorded schedule. During refractory V is held at reset but synaptic/OU states continue. |
| Stim channels | Four disjoint groups of 50 E cells, chosen uniformly without replacement inside each sector. These cells are excluded from recorded neurons. All cells in a group receive identical positive held current. |
| Recording | Each sector: 20 of the remaining E and5 I, selected without replacement, fixed for a network. E split into four disjoint 5-cell channels, I into one 5-cell channel: total20 virtual channels, 100 neurons (10%). |
| Observation | .02 s nonoverlapping bins; all spikes detected perfectly in base case. Masked/dropout stress is separate. No analog/raw waveform or electrode physics. |
| Control | Every20 ms; current held for20 ms. Four currents u_j>=0 pA, <=120 pA/channel, sum<=240 pA, abs(u_j-u_previous_j)<=30 pA/tick. Start u_previous=0. |

Neural equations, for nonrefractory cells:

\[
C\dot V_i=-\frac C{\tau_{m,i}}(V_i-E_L)+I_{E,i}+I_{I,i}+180\,\mathrm{pA}+\eta_i+g(t)\sum_{j=1}^{4}M_{ij}u_j(t),
\]
\[
\dot I_{E,i}=-I_{E,i}/5\mathrm{ms},\quad
\dot I_{I,i}=-I_{I,i}/10\mathrm{ms},\quad
I_{s,i}(t^+)=I_{s,i}(t^-)+w_{i\ell}\quad\text{on presynaptic spike arrival.}
\]

M is a fixed binary neuron×stim-channel matrix. Reset/refractory implements spikes at threshold; g is private actuator efficacy, initially1. OU update at each step is exact for that process:

\[
\eta_{i,n+1}=a\eta_{i,n}+40\,\mathrm{pA}\sqrt{1-a^2}\epsilon_{i,n},\quad a=e^{-.1/5},\quad\epsilon_{i,n}\sim N(0,1).
\]

Declare OU ordering explicitly in tests; switching white versus colored noise or changing integration method is a model change. For dt-convergence tests use nested Brownian/OU-consistent streams where possible; exact spikes need not match after dt changes, so compare aggregate rate and evoked-response statistics with uncertainty.

No stimulation-triggered artifact in base case, and no measurement noise beyond spike-count sampling. This favors identification relative to biological MEA experiments; do not imply noise realism. A spike in a channel is a model event from known membership, not a sorted extracellular waveform. Disjoint stimulation and recording prevents counting directly injected cells as the primary success signal, but recurrent transfer is still a simplified model.

## Observation, estimation and predictor

For channel c with5 neurons and full bin duration Delta=.02 s, rate=count/(5Delta) Hz. Pool the four E channels per sector: z_{j,k}=total E count/(20Delta). Base-case mask all true. Causal filter r_k=alpha r_{k-1}+(1-alpha)z_k with alpha=exp(-Delta/.1s); initialize to baseline sector mean once baseline phase ends, use actual prior bins thereafter. No centered filtering. The scalar tracked rate is y_k=mean_j r_{j,k}. Online controller receives no neuron identity/voltage, true gain, connectivity or future observations.

Fit a four-output ARX:

\[
\hat r_{k+1}=c+\sum_{l=0}^{3}A_l r_{k-l}+Bu_k.
\]

Features are four sector rates at current and3 previous bins plus four current actions, plus intercept:21 coefficients/output. Index action by **delivered** hold on [t_k,t_{k+1}); r_k contains completed data up to t_k. One-step training target r_{k+1} therefore never leaks into u_k. Means/SD of features fitted on identification training prefix; SD floor1 Hz for rate and1 pA for current. Center output using training sector means, do not standardize using test future. Intercept unpenalized, ridge penalty chosen from {0.1,1,10} in standardized units. Maintain the same scaling for fixed/adaptive models throughout test.

Uncertainty: save residual variance and covariance per output and empirical90% residual intervals from held-out calibration. Report coverage/width on reserved pulse responses and test; colored counts/model mismatch mean these are diagnostics, not certified probabilistic guarantees. If intervals fail calibration do not call the controller uncertainty-aware. V0 MPC does not optimize an uncertainty bound.

Adaptive model: recursive least squares initialized from ridge normal-equation inverse (intercept numerical regularizer1e-6 only for inversion) and coefficients; update after each eligible transition with forgetting factor chosen on validation from {.995,.999,1}. Equation P+=(P-P phi phi^T P/(lambda+phi^T P phi))/lambda, theta+=theta+P_old phi*(target-phi^T theta)/(lambda+phi^T P_old phi). Symmetrize P each update. Nonfinite, nonpositive denominator or eigenvalue below -1e-8 triggers logged freeze to last valid model and constrained ramp-to-zero fallback; repeated failures follow system-design abort policy. No online feature rescaling or hidden access. Fixed model coefficients never update; both compute predictions and log the same diagnostics.

## Phases and calibration

For every network/noise replicate, generate a common prefix once, checkpoint after calibration, and restore **all** neural state, delay/refractory queues, monitor cursor and exogenous-stream index before each controller. If checkpoint conformance fails, recreate a fresh process and replay the entire prefix. Never reuse a state left by another controller.

1. Burn-in5 s with zero current, excluded from metrics.
2. Baseline10 s zero current; baseline b_j is the sector E rate count over the last8 s, b=mean b_j. Do not derive target from later control outcomes.
3. Identification30 s. Every100 ms choose a new four-channel proposal independently from {0,30,60} pA per channel, uniform, using calibration stream. All sums<=240. Enforce slew by moving each20 ms tick toward proposal by at most30 pA, so changes from60 to0 take two ticks. Include zero vectors. First24 s fit, last6 s untouched chronological validation for ridge/predictor checks. No random bin split.
4. Reserved pulse-response check8 s:20 blocks of400 ms; first20 ms pulse on one channel, remainder zero, with30 pA slew limiting (pulse amplitude30). Cycle balanced channel IDs in a frozen random permutation; paired sham replay of the same8 s begins from the calibration endpoint and identical background noise. This probe is evaluation of identification, not additional fitting. The control branch resumes its own actual pulse-check endpoint (same across controllers); no control model refit from probes. Separate evaluator-only sham branch never supplies future controller information.
5. Test60 s, first target b+2 Hz, then alternate b+4 and b+2 every10 s. Formula is known at start; no clipping based on controller success. MPC knows future target schedule, PI uses current target (standard setpoint tracking). Give PI optional target feedforward from its calibration map; tune fairly. At test30 s, hidden g changes for designated condition. Freeze analysis at60 s.

Every phase boundary is on the integration/observation grid. Keep controller filter history from the common prefix, seed lag buffers with completed bins; no arbitrary zero padding. Calibrating on a held-out network is permitted deployment-like identification, not tuning global hyperparameters. Record its exact duration and inputs.

## Controllers and tuning

All methods obey identical current, total and slew bounds. On missing observations or controller failure, use the feasible action nearest zero: decrease each prior current by at most30 pA/tick until zero (at most80 ms from120 pA). Log every fallback tick; base-case PASS requires none. After dropout, resume only after four complete observation bins, using normal slew from the last delivered action. No emergency exception bypasses constraints.

- **Zero:** u=0.
- **Constant:** choose q in {0,30,60} pA, u_j=q, by smallest absolute difference of calibration conditional mean to b+3 Hz (tie lower current); slew into q. Baseline for mean performance, not target-specific feedback.
- **Fixed periodic:** equal channels alternate q=0/60 each1 s, initial phase fixed0. A patterned open-loop control; never select phase on test.
- **PI:** e=target-y, scalar total command s=clip(s0+Kp e+Ki integral,0,240), equally allocate s/4; use same Euclidean projection as other actions. s0 from constant calibration (4q). Integrate error at20 ms only if unsaturated or error would move the command back into admissible range; reset integral on dropout. Optional feedforward uses calibration least-squares steady-state mean-rate versus total current with slope floor1e-3 Hz/pA and constrained inverse; whether enabled chosen on validation. Gains Kp in {5,15,45} pA/Hz and Ki in {1,5,20} pA/(Hz s). Grid=18 if feedforward flag varies, same tuning budget limit disclosed.
- **Fixed MPC / adaptive MPC:** identical ridge-initialized ARX, receding horizon H=10 bins=200 ms. Decision vector10×4 future actions. Target scalar mean; no requirement that individual sector means equal target. Minimize
  \[
  J=\sum_{h=1}^{10}\left[(\mathrm{mean}(\hat r_{k+h})-y^*_{k+h})/4\mathrm{Hz}\right]^2
   +\rho_u\sum_{h=0}^{9}\|u_{k+h}/120\mathrm{pA}\|_2^2
   +.05\sum_{h=0}^{9}\|(u_{k+h}-u_{k+h-1})/30\mathrm{pA}\|_2^2.
  \]
  rho_u in {.01,.1,1}; constraints box/sum/slew each step. Solve convex quadratic with SciPy SLSQP, analytic objective gradient and linear constraints, ftol1e-8/maxiter100; warm start shifted prior solution, first solve constant feasible prior current. Check returned feasibility to1e-6 pA and success; on failure constrained ramp-to-zero fallback, do not silently project a failed optimizer result and claim optimal MPC. Cost and model are fixed for the solve, no neuron oracle. Fixed and adaptive both log unconstrained predictions; do not clip negative forecasts invisibly. Adaptive adds only causal RLS updates, no extra dither/exploration.

All action algorithms use one shared Euclidean projection onto feasible four-dimensional box/L1/slew constraints (SciPy optimization or tested direct projection); receipt uses delivered values. Zero/constant/periodic/PI proposals are projected, while MPC solves with constraints and is verified. Fallback ramps remain explicit and fully constrained. An optimizer wall time>20 ms is a reported simulated real-time miss, not backdated delivery; V0 virtual time still advances after solve. A future real-time protocol needs a separate deadline policy.

Training networks choose sensible numerical defaults and check implementation. Validation networks select PI gains/feedforward and MPC rho/forgetting factor by mean normalized tracking MSE +.1 mean sum(u/120)^2 across **stationary and gain-down conditions equally weighted**. Fixed/adaptive choose shared MPC rho by mean of their two validation scores; choose lambda for adaptive separately. Tie lower mean current, then simpler (PI feedforward off, lambda1). Pick stronger primary baseline (PI or fixed MPC) by lower validation post-change RMSE with tie PI. Freeze it globally before test, not per-test-network. Preserve all candidate scores and disclose unequal parameter-grid counts; no additional adaptive trials. Test comparison includes both baselines regardless of selected primary.

## Cohorts, streams and pairing

Network IDs0–9 train,10–14 validation,100–119 test. Root seed20261018, NumPy SeedSequence spawn_key=(network_id, role_id, replicate_id). Roles:0 membrane/init,1 connectivity,2 synapse weights/delays,3 channel map,4 OU innovations,5 calibration actions,6 observation masks. Network parameter roles use replicate_id0; OU/calibration/masks vary across three test replicates0,1,2. Hash and save realized topology/parameter/channel arrays. Simulator Brian seed fixed from a separate role7, but exogenous noise is explicit and action-independent.

Generate OU innovations in fixed1 s blocks indexed by (network_id,replicate_id,block_index) using a derived spawn_key, never by number of spikes, action values, callback count or controller branch. All conditions/controllers get identical base innovations and masks at each simulated time. Store generator algorithm/version/block boundaries and precomputed-block hashes. Gaussian draws and stream consumption remain unchanged after g changes. Checkpoints store the exact innovation offset; no controller can consume the substrate stream. Common random numbers reduce variance; they are not physical biological counterfactuals.

Test:20 networks×3 repeats×conditions×controllers. Run these as short trials with a projected resource budget after M2; this is a planned sweep, not authorized work in Mission001. If insufficient budget, freeze a smaller manifest *before* test with a documented precision reduction; do not select favorable seeds. No replacement of failed/quiet/unreachable test networks.

## Perturbations

Primary condition: g=1 until30 s, then.6 globally. Controls/stress: (a) stationary g=1, (b) step increase to1.4 at30 s, (c) smooth g=1-.4(t-20)/20 for t in[20,40] s clipped to[.6,1], (d) stationary gain with all20 observation channels masked for200 ms every5 s beginning test25 s. No mask-induced zero counts; controller uses defined fallback. Conditions b–d secondary/exploratory, no claims selected from whichever improves adaptive performance. Perturbation schedule is evaluator configuration, absent from controller input; target schedule is intentionally known.

Optional after the primary lock: observation thinning, recurrent-weight drift and AdEx model stress. These require protocol amendments, not hidden substitutions for a failed gain-drift result.

## Negative controls and identifiability/authority gate

Development gate on all10 training networks, reporting every network: at least8/10 have baseline E rate between1 and30 Hz, maximum sector rate<100 Hz, no nonfinite state, and under independently randomized allowed currents a positive pooled unstimulated-E response (paired pulse/sham contrast95% CI above0). On development only, a declared maximal-budget all-channel60 pA hold must raise mean observed rate by at least4 Hz even at g=.6 in at least8/10. Compare separate paired5 s holds after common burn-in. This tests some control authority, not arbitrary-state controllability. Do not require it of test networks to retain them. Fail this gate → diagnose/amend parameters on train only and version protocol, stop before test.

Identification gate: across development reserved pulse responses, ARX pooled mean response MSE at200 ms improves by>=10% versus no-input AR at same lag/ridge; report error on intervention-minus-sham contrasts, not just high baseline R². Report normalized design-matrix rank/singular values and intervention-response slope CI. No controllability matrix of a fitted ARX proves controllability of hidden spiking dynamics. If predictors fail but PI works, run may support a PI benchmark, not the prespecified adaptive-MPC scientific claim.

Negative controls: zero actuation M=0 (reinitialize same streams, command receipts still logged); shuffled input alignment (circular shift>=1 s within identification prefix, fixed seed and no test-fit); frozen RLS lambda/update ablation; replay observations independent of action; yoked adaptive action schedule applied to fresh noise for a feedback-specific exploratory check. Zero-M must show no paired response, and reactive controller changing commands cannot alter replayed observations. Any violation fails pipeline qualification. A true-input ARX should beat the shuffled-input model on held-out randomized response; failure blocks causal-identification language. Do not require an arbitrary p-value in every individual low-power network.

## Metrics and statistical analysis

Primary post-change window [30,60) s; also report pre-change[0,30), stationary full60 s, and transient30–35 s. Evaluate y as defined causal filtered pooled E rate; also raw-bin pooled rate (noise-sensitive) and full hidden-E rate separately. Do not switch primary filter after results.

Per trial RMSE=sqrt(mean(y-target)^2) Hz, MAE, overshoot Hz, saturation fraction, time within±2 Hz, recovery time (first1 continuous s with absolute error<=2 Hz after drift; censored at30 s), current cost mean(sum_j abs(u_j)) pA, integrated injected charge=sum over50 targeted neurons/channel of current×duration (pA·s=pC), and squared current cost separately. Energy is **not** inferred without voltage/impedance. Report command→delivery simulated latency (base exactly0), decision compute median/p95/max ns and >20 ms fraction; simulation throughput separately. No hardware latency claim.

Prediction metrics: one-step/10-step MSE, input-vs-sham response bias,90% interval coverage/width, residual autocorrelation; time-resolved gain/model error evaluator-only. For dropout stress, observation-based tracking metrics use only common complete-coverage bins and disclose the excluded duration; evaluator-only full-E tracking includes the missing interval and is reported separately. Failures: aborts, ramp/zero fallbacks, budget violations, missing coverage, numerical errors, and constraint saturation as an outcome. Output all networks, not just typical raster plots.

Average each metric over3 repeats within network first. For RMSE relative improvement d_i=(RMSE_baseline_i-RMSE_adaptive_i)/max(RMSE_baseline_i,.1Hz); report mean and paired network bootstrap95% percentile CI,10,000 resamples with analysis seed707. Cost relative increase computed similarly per network with1 pA denominator floor; average across20. Report absolute differences too; floors and baseline near-zero cases explicit. Bootstrap does not create more than20 independent networks. H2 stationary relative RMSE increase uses same .1Hz floor and upper95% bound. No optional stopping. Secondary condition/metric intervals descriptive; any confirmatory secondary testing requires Holm correction across the declared family.

This is a practical precision design, not a proven power calculation. After train/validation estimate variance and report expected CI width without using test. Failure to resolve a10% effect is inconclusive, not evidence of equivalence. Any missing/aborted primary trial prevents H1 PASS; report available descriptive data plus abort rate and reason, never silently drop it or impute success.

## Explicit gates

| Gate | PASS | FAIL / interpretation |
|---|---|---|
| Software validity | Exact same-environment replay, chunk/continuous with delays, distinct-trial isolation; malformed inputs rejected, no future/privileged-state access | Stop; scientific metrics invalid |
| Numerical/model feasibility | Development authority/response gate above; dt=.05 vs.1 ms mean-rate and pulse-contrast relative differences<=5% (absolute floor.5 Hz) on3 training seeds; bounded cost | Amend train-only protocol or stop; no test selection |
| Identification | Development held-out response>=10% MSE advantage over no-input predictor and correct zero-M/replay controls | No causal system-identification qualification; diagnose |
| Execution | All20 test networks retained, all3 repeats complete in primary/stationary conditions, no constraint violations or fallback ticks there, frozen configs/splits | HOLD; do not report H1 PASS |
| H1 efficacy | mean d>=.10, bootstrap lower95%>0; mean relative cost increase<=.10; no primary abort/violation | Negative if effect absent/adverse; inconclusive if CI too wide; distinguish cost failure |
| H2 stationary | upper95% stationary relative RMSE increase<=.05 | Combined adaptive-benefit claim fails even if H1 succeeds |
| Scientific reporting | Full cohort, all baselines and nulls, complete evidence lineage and limitations | HOLD, even if attractive traces exist |

Feasibility and identification gates assess the experimental instrument; H1/H2 assess the hypothesis. A negative H1 result can be scientifically credible after instrument PASS. **None of these gates was executed in Mission001 except the smaller Brian API probe documented in the audit.**
