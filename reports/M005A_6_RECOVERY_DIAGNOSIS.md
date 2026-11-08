# M005A.6 — PI recovery failure diagnosis

**Diagnostic execution PASS. Finite-horizon PI undertracking is supported despite demonstrated reference headroom. M005A.5 remains scientific FAIL (stationary PASS, recovery FAIL). M005B remains HOLD.**

## Revisions, preservation and scope

Starting clean revision `0862a6286260874414636d3de50be7471eac2eff`, branch `research/m005a-5-confirmation`; review branch `research/m005a-6-recovery-diagnosis`. Retrospective diagnostic plan committed at `37ae9171f33fd32186c1085092318f1a02492388`. Final revision is the commit containing this report, recorded exactly in the mission response; recover it with `git log -1 --format=%H -- reports/M005A_6_RECOVERY_DIAGNOSIS.md`. No merge.

Inspected original protocol009, amendments010/011, M005A–M005A.5 reports, control/substrate/supervisor sources, selection seal, confirmation lineage, complete observations/actions and verification records. The preservation manifest hashes every starting tracked file, including all negative findings. No historical file, installed source, Kp=10/Ki=5, target, model parameter or acceptance threshold changed. No controller was fitted or retuned. This is retrospective analysis of already inspected development evidence, not a new confirmatory scientific result.

All 20 network/noise pairs (networks 0–9, repeats 41/42) and160 branches were analyzed. The original three versus continuation17 acquisition sessions retain their original identities; they are one ten-network cohort. No new scientific neural experiment was needed or run. Full regression tests include the existing short neural fixtures; that is verification, not a new recovery experiment. Validation and locked-network outcomes were not opened.

## Metric definitions and why MAE and bias disagree

Output error is d=y−target, so negative bias means undertracking. Controller error is e=target−y. Use original nonoverlapping1 s raw recorded E80 rates. Pre=[8,16), immediate=[16,20), frozen late=[20,32); final=[28,32) is descriptive only. Absolute neural time starts51 s; efficacy loss occurs67 s. Average repeats inside each network before cohort inference. Bootstrap:10,000 paired network draws, PCG64 seed 20261025, percentile95% intervals. Do not count bins, sectors or repeats as independent networks. Pointwise time-course intervals are not simultaneous confidence bands.

The frozen PI reduces late-loss MAE from0.398503 Hz for FIXED to0.260456 Hz, an improvement0.138047 Hz (95%CI0.107292–0.168516), or33.899% mean paired relative improvement. All ten network MAE improvements are positive. Yet full recovery requires at least8/10 joint networks with |bias|<=0.2 Hz in addition to MAE<=0.35 Hz and other gates. Only five satisfy the bias criterion. Lower absolute error can coexist with a persistent negative mean error during this finite window; the favorable MAE does not override the failed bias gate.

| PI signed bias window | Mean Hz | Paired network 95% CI Hz |
|---|---:|---|
| Pre-loss 8–16 s | 0.017031 | [-0.016877, 0.053283] |
| Immediate 16–20 s | -0.334297 | [-0.372031, -0.296953] |
| Frozen late 20–32 s | -0.209609 | [-0.227630, -0.192240] |
| Descriptive final 28–32 s | -0.138047 | [-0.176172, -0.102889] |

## All-network diagnosis

Headroom below means MAX observed rate minus the actual calibration-derived target at reduced efficacy, not just MAX−ZERO. MAX is the same fixed admissible C02 allocation in every network; no per-network action oracle is involved. Biases and currents in this table average the two repeats. Minimum headroom is the smaller of the two observed replicate margins.

| Net | Pre bias | Immediate bias | Frozen late bias | Final bias | Min MAX headroom Hz | q16→q31 pA/channel | ΔI16→32 pA | Classification |
|---:|---:|---:|---:|---:|---:|---|---:|---|
| 0 | -0.017188 | -0.386719 | -0.232552 | -0.149219 | 0.564583 | 44.876→60.943 | 21.688 | A |
| 1 | 0.113281 | -0.271094 | -0.197135 | -0.082031 | 0.706250 | 40.781→57.261 | 17.250 | PASS_NO_FAILURE |
| 2 | 0.014844 | -0.300000 | -0.249479 | -0.228125 | 0.425000 | 49.823→69.941 | 20.969 | A |
| 3 | -0.052344 | -0.310156 | -0.174219 | -0.053906 | 0.885417 | 37.158→52.076 | 16.656 | PASS_NO_FAILURE |
| 4 | -0.060156 | -0.279688 | -0.189063 | -0.145313 | 0.783333 | 41.691→54.245 | 16.938 | PASS_NO_FAILURE |
| 5 | 0.103906 | -0.241406 | -0.239844 | -0.250781 | 0.131771 | 53.051→75.461 | 19.219 | A |
| 6 | -0.015625 | -0.414844 | -0.244010 | -0.086719 | 0.445833 | 50.270→71.509 | 22.938 | A |
| 7 | -0.008594 | -0.426563 | -0.172396 | -0.146875 | 0.598958 | 39.841→59.029 | 18.875 | PASS_NO_FAILURE |
| 8 | 0.057813 | -0.339844 | -0.212760 | -0.150781 | 0.417188 | 46.233→66.503 | 19.562 | A |
| 9 | 0.034375 | -0.372656 | -0.184635 | -0.086719 | 0.471875 | 42.313→64.957 | 18.531 | PASS_NO_FAILURE |

Frozen recovery failures are networks 0,2,5,6,8. The other five passed the recovery gates and are labeled PASS_NO_FAILURE rather than being forced into a failure mechanism category. Final-window bias is closer to zero than immediate bias in9/10 networks; network 5 is slightly worse (−0.241406→−0.250781 Hz). Networks 2 and5 still exceed the bias tolerance even in the final4 s. These selected-window descriptions cannot retroactively replace the frozen window or prove eventual convergence.

## Authority: evidence supports A for the failed networks

All 10 networks bracket the target with ZERO below and MAX above it in BOTH original repeats. Across all 20 repeats MAX−target ranges 0.131771 to 1.147396 Hz. Network-mean headroom is 0.634661 Hz, paired network 95% CI [0.5049205729166666, 0.7627083333333331]. Existing evidence is sufficient to reject observed hard-limit exhaustion as the explanation for these five failures; no new neural diagnostic is justified for that question.

A = original PI recovery failure despite both-replicate empirical target bracketing; B = demonstrated actuator-constraint infeasibility (not inferred from finite-bank nonresponse); C = failure mechanism unresolved because reference bracketing is absent/mixed. The five passing cases are separately retained. This avoids falsely calling successful networks failures.

| Class | All ten networks | Descriptive Wilson 95% fraction interval |
|---|---|---|
| A: failed PI with observed reference headroom | 5/10 (50%) | [23.7%, 76.3%] |
| B: demonstrated infeasibility | 0/10 (0%) | [0.0%, 27.8%] |
| C: unresolved failed-network reference evidence | 0/10 (0%) | [0.0%, 27.8%] |
| Original recovery pass | 5/10 (50%) | [23.7%, 76.3%] |

Among the five actual failures,5/5 support A under this operational definition (100%; descriptive Wilson 95%56.6–100%). These intervals summarize small counts under an iid approximation; the networks are a previously studied development cohort, and the failure subset is selected by the frozen outcome. They do not quantify causal certainty or future biological prevalence. Two repeats provide no reliable per-network confidence interval, so both margins/ranges are reported in trial_diagnosis.csv. Zero B cases is not proof that all targets or future states are feasible.

Finite noisy bracketing demonstrates recorded rates above the relevant target under one legal policy. It does not prove continuous interpolation, stable exact target realization, mathematical reachability or success of an implementable controller under every disturbance. MAX overshoots and is not a tracking solution. No lower target or alternate channel oracle was selected.

## Intervention, integral and saturation accounting

PI used zero delivered C02 bound ticks out of32000 LOSS ticks, zero decision clipping events, zero anti-windup blocks and zero integral-clamp attempts, including the terminal update. Overall mean replicate peak dose is 67.074128 pA/channel; largest single-replicate peak is 85.505612 pA/channel, below120. Channels1/3 are identically zero; channels0/2 match. Total current is2q and remains below240 pA. Inactive zero channels must not be counted as active-dose saturation.

| Decision origin relative time | Mean desired q pA/channel | Mean integral pA | Interpretation |
|---|---:|---:|---|
| 16 s | 44.603816 | -1.709375 | Before any post-loss observation |
| 17 s | 51.312019 | 0.605078 | First possible response to completed16–17 s bin |
| 20 s | 53.796003 | 4.976563 | Start of frozen late window |
| 31 s | 63.192488 | 16.341797 | Last delivered1 s action |
| 32 s | 66.053816 | 17.553125 | Terminal update; never delivered |

Mean feedforward is 46.078034 pA/channel. Mean integral rises by 19.262500 pA after loss; all 20 repeat increments are positive (minimum 12.062500 pA). The exact programmed identity ΔI=5Σ(target−observed rate)*1 s holds because no clamp/block occurs. During the late window alone, mean ΔI is 12.576562 pA. This shows continuing correction rather than a frozen integrator or exhausted actuator. The32 s command is deliberately not treated as delivered stimulation.

Observation delay is the frozen sample-and-hold design: the action at16 s is based on completed pre-loss observations; response to loss first becomes available at17 s. The dynamics then raise current over several feedback ticks. This accounting supports incomplete finite-horizon compensation. It does not causally establish that Ki=5, Kp=10 or the1 s cadence is uniquely responsible, or that increasing gains would be stable/better. No gains/cadence were varied here.

## Baselines and calibration

| Network | Target Hz | qff pA | STATIC FIXED bias Hz | LOSS FIXED bias Hz | FIXED evoked STATIC→LOSS Hz | LOSS−0.6STATIC response Hz |
|---:|---:|---:|---:|---:|---|---:|
| 0 | 13.786719 | 40.947 | -0.028385 | -0.426302 | 1.003125→0.605208 | 0.003333 |
| 1 | 15.535156 | 42.210 | 0.117969 | -0.308073 | 0.998958→0.572917 | -0.026458 |
| 2 | 12.901563 | 52.558 | 0.016667 | -0.383854 | 1.048437→0.647917 | 0.018854 |
| 3 | 15.716406 | 36.994 | 0.081510 | -0.342969 | 1.034375→0.609896 | -0.010729 |
| 4 | 15.926562 | 39.050 | -0.028125 | -0.408333 | 1.007813→0.627604 | 0.022917 |
| 5 | 13.342969 | 65.997 | 0.250781 | -0.238802 | 1.197917→0.708333 | -0.010417 |
| 6 | 15.033594 | 48.966 | -0.048177 | -0.436719 | 1.036979→0.648438 | 0.026250 |
| 7 | 14.137500 | 40.216 | -0.052083 | -0.413542 | 0.980729→0.619271 | 0.030833 |
| 8 | 13.571094 | 48.022 | 0.015365 | -0.375781 | 1.020313→0.629167 | 0.016979 |
| 9 | 12.333594 | 45.820 | 0.008594 | -0.398698 | 1.026042→0.618750 | 0.003125 |

All original calibrations passed their frozen validity checks. STATIC FIXED late mean bias is 0.033411 Hz; LOSS FIXED bias is -0.373307 Hz. STATIC PI late bias is -0.007578 Hz. ZERO trajectories are exactly identical across gain conditions, and all policies match their own STATIC/LOSS records before loss. Thus the gain intervention, rather than a changed target definition, accounts for the paired divergence under fixed input. Calibration at g=1 is not a verified inverse map at g=.6; no controller was given the true gain.

The evaluator-only linear heuristic qff/.6 averages 76.796724 pA/channel, whereas delivered late PI currents remain lower. This is dimensional context under a presumed linear map, not a measured required dose, controller input, fitted model or gain-aware action recommendation. Actual FIXED evoked-response scaling residuals are preserved rather than assuming exactly0.6 response attenuation. Historical calibration uncertainty, network nonlinearity and spontaneous fluctuations remain possible contributors.

## Target dependence, sectors and excitation

Every target is baseline+1 Hz. No different target offsets were randomized, so absolute-target dependence cannot be separated from baseline activity/network identity. Descriptive correlations with late PI bias are reported without p-values or feature selection:

| Network covariate | Pearson r | Spearman rho |
|---|---:|---:|
| target_hz | 0.346463 | 0.357576 |
| baseline_hz | 0.346463 | 0.357576 |
| qff_pA | -0.688777 | -0.793939 |
| slope_hz_per_pA | 0.732490 | 0.793939 |
| mean_max_target_margin_hz | 0.745508 | 0.757576 |
| integral_post_delta_pA | -0.794782 | -0.757576 |

Target and baseline correlations are identical by construction. The negative association of integral growth with remaining error is partly built into the PI update itself; it cannot establish harm from integration. Lower calibration slope and less headroom co-vary with larger negative bias, but these are confounded across only ten networks, not causal mechanism tests.

All four recorded E-sector trajectories and per-network/window rates are in timecourses.csv/windows.csv. Sector baseline deviations are descriptive, not four imposed targets. The figure below compares matched LOSS−STATIC sector responses; under PI this includes feedback mediation. These observations neither expose unrecorded voltages nor isolate excitatory/inhibitory current pathways. No inhibition ablation/current decomposition is available here, so a specific inhibitory mechanism is unsupported.

| Net | LOSS late sector0/1/2/3 above own baseline Hz |
|---:|---|
| 0 | 0.806250 / 0.904167 / 0.364583 / 0.994792 |
| 1 | 0.814583 / 0.650000 / 0.931250 / 0.815625 |
| 2 | 0.189583 / 0.969792 / 1.026042 / 0.816667 |
| 3 | 0.670833 / 0.894792 / 0.867708 / 0.869792 |
| 4 | 0.612500 / 0.892708 / 1.059375 / 0.679167 |
| 5 | 0.610417 / 0.923958 / 0.722917 / 0.783333 |
| 6 | 0.651042 / 0.935417 / 1.006250 / 0.431250 |
| 7 | 0.884375 / 1.406250 / 0.306250 / 0.713542 |
| 8 | 0.591667 / 0.830208 / 0.609375 / 1.117708 |
| 9 | 0.825000 / 0.542708 / 0.720833 / 1.172917 |

Persistent excitation was recomputed for all 320 designs. PI LOSS last16 s has rank11/41 in all 20repeats; C02 makes two inputs identical and two zero. FIXED/MAX/ZERO last16 s have rank1/41. PI qSD and positive-subspace conditioning are recorded in excitation.json; full design is rank deficient. This establishes dose variation, not independent channel identification or consistent estimation under feedback confounding. No extra excitation was injected.

## Evidence strength and causal limits

- Matched STATIC/LOSS trajectories with common noise provide simulated causal evidence of the evaluator gain intervention; FIXED has unchanged inputs. PI versus FIXED branches identify the tested policy difference, not superiority of an untested controller.
- Exact update reconstruction establishes what PI did, including error accumulation, next-tick timing and absence of saturation/blocking.
- Bias/current/slope/sector associations support a finite-horizon recovery interpretation but do not identify a unique dynamical cause. Greater gain, adaptation or MPC superiority has not been tested.
- Final-window improvement is not a steady-state experiment. Network5 does not improve in that comparison, and two networks remain beyond0.2 Hz even there. No alternate window rescues the original result.

## Verification, commands and failures

Ran the full existing suite: **144 passed,25 existing warnings,58.06 s**. Original independent verifier reconstructed20 trials/160 branches/800 primary rows from preserved events, with timing/current/slew/calibration/policy/noise checks. New independent verifier reconstructed640 diagnostic windows,5120one-second rows,2560 matched contrasts,1280 scalar PI updates, network aggregation/correlations/bootstrap, and320excitation references without importing the producer. Supplemental verification independently checked ten calibration contrasts and256 pointwise network intervals. Source/Git/selection and all starting evidence hashes passed.

One supplemental CSV verifier initially failed because it passed CSV strings to NumPy numeric comparison. The supervisor correctly recorded WORKER_FAILURE and reaped the child. Explicit float conversion corrected the verifier; only this read-only verifier was rerun under the SAME original deadline. No data, model, thresholds or numerical producer changed. Failed source, logs, terminal record and correction provenance are retained. This was not a neural/scientific retry or a resource failure.

```sh
/tmp/neuromancer-m004-venv/bin/python reports/evidence/m005a_6/run_commands.py reports/evidence/m005a_6/stage_config.json
# Exact original and supplemental child commands are in stage_config.json and supplement_config.json.
# Corrected verifier and report publication inherit supervision/terminal.json deadline and clock domain.
```

Environment: Python3.12.15, Brian2 2.10.1, NumPy2.5.4, macOS arm64; requested VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/neuromancer-m005a-mpl. Actual BLAS threading is not certified. Main1200 s supervisor stage completed in 133.752933 s with cleanup verified. Corrected verification inherited the exact same absolute deadline/boot domain. Independent reconstruction here is within-session verification, not external replication. No new scientific acquisition or locked-network test ran.

## Stronger-control decision and next falsifiable experiment

Further recovery-dynamics research is justified by demonstrated reference headroom and incomplete correction, but stronger/adaptive control is **not scientifically qualified or shown necessary**. An unchanged PI might recover with more time; alternatives might amplify noise or overshoot. The diagnosis therefore supports hypothesis A for the five failures at the finite tested horizon, with explicit empirical-reachability limits. There is no observed support for B as the dominant explanation and no failed-network C case under the prespecified bracketing rule. Unique causal attribution remains uncertain.

**M005B HOLD.** Do not implement MPC or retune PI on these outcomes. Next proposal, requiring a separate preregistration/authorization: extend the unchanged fixed-PI STATIC/LOSS experiment to64 s on all ten development networks with fresh prespecified noise, retain/report the original20–32 s window unchanged, and test whether signed bias moves toward zero in48–64 s without saturation. Keep target, Kp/Ki, calibration and constraints identical; retain matched MAX/ZERO/FIXED references. This distinguishes slow convergence from longer-lived offset and cannot reclassify M005A.5. An optional separate integral-freeze or cadence ablation would be needed to causally isolate feedback mechanisms; neither was run here.

Primary limitations: only ten previously studied networks/two repeats; final-window and correlation analyses are retrospective; MAX bracketing is noisy finite-policy evidence, not a mathematical reachable set; no long-horizon convergence/stability, gain/cadence ablation, hidden-current mechanism or biological experiment was measured.

## Deliverables

[Bias dynamics](evidence/m005a_6/bias_dynamics.png), [current/integral histories](evidence/m005a_6/current_integral.png), [authority and sectors](evidence/m005a_6/authority_sectors.png). Complete per-repeat/per-network metrics, all 32 s histories, calibrated targets, original source references, network uncertainty and independent verification are under `reports/evidence/m005a_6/`. Original raw neural observations/actions remain at their immutable M005A.5 paths; the input manifest links them by hash rather than duplicating trials.

PI LOSS last16 s delivered-dose variability and identifiable-subspace conditioning by network (means of two repeats):

| Net | q SD pA | Positive-subspace condition | Full rank |
|---:|---:|---:|---|
| 0 | 6.941141 | 53.373159 | 11/41 |
| 1 | 5.907481 | 41.903768 | 11/41 |
| 2 | 5.991031 | 66.759558 | 11/41 |
| 3 | 5.695057 | 50.679967 | 11/41 |
| 4 | 5.616912 | 45.178301 | 11/41 |
| 5 | 7.386511 | 47.417645 | 11/41 |
| 6 | 7.730022 | 92.672534 | 11/41 |
| 7 | 5.873594 | 53.730689 | 11/41 |
| 8 | 6.014326 | 66.506213 | 11/41 |
| 9 | 6.096907 | 53.685698 | 11/41 |
