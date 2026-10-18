# M002.1 preregistration — allocation diagnosis

Frozen before new scientific runs. Starting revision b946c8a0b461567f2132642383462492c7b2d24b; branch research/m002-1-authority-diagnosis. M001/M002 artifacts, all 38 original tests, the neural model and V0 protocol remain unchanged. This document and the diagnostic runner will be committed before execution. No held-out network is evaluated.

## Cohort, random streams and stopping

Exactly ten training networks (IDs0–9), exactly **five** independent noise replicates (IDs0–4), root20261018 and unchanged M002 SeedSequence/PCG64 roles/block layout. Parameter/membership roles0–3 always use replicate0. No response-dependent seed replacement or sample-size change. Replicate0 is also a prespecified reproduction of M002, not independent of that historical evidence. Replicates1–4 provide new independent noise within each fixed network.

Each network/replicate has the original5 s zero-input burn-in and10 s baseline at gain1; baseline statistic uses [7,15) s. There is no identification/calibration fitting. Save the exact baseline endpoint including neural/refractory/delay state, clocks, current command state, observation/filter cursors and noise offset. Restore it before every branch. Evaluation window is [15,20) s,5 s including ramp. Gain0.6 primary, gain1 secondary; same exogenous innovations at every simulated time across all branches/gains. Run all16 branches (including both shams, whose identity is a check).

Use at most three independent simulation worker processes. Based on measured M002 costs, the full design is computationally feasible (800 five-second branches plus50 baselines); this is a resource estimate, not a new benchmark. Freeze all five replicates now. Infrastructure failures are logged and may be retried at identical IDs with failed artifacts retained; persistent failures lead to PARTIAL, not dropping observations. No outcome-based early stopping. If runtime/resources prevent completion, report incomplete cells; never redefine the cohort retrospectively.

## Intervention bank and exposure

Fixed order: S=[0,0,0,0]; D=[60,60,60,60]; C01=[120,120,0,0]; C02=[120,0,120,0]; C03=[120,0,0,120]; C12=[0,120,120,0]; C13=[0,120,0,120]; C23=[0,0,120,120], in pA. Gain order0.6, then1. Each action is a fixed, implementable open-loop allocation, not a controller.

Generate250 commands at20 ms intervals, starting from zero. Each channel approaches its target by at most30 pA/tick. Enforce nonnegative/current<=120/sum<=240/slew<=30 before execution, then independently recheck actual receipts. D starts [30,30,30,30], then reaches target at20 ms. Concentrated active channels follow30,60,90,120, reaching target at60 ms. The5 s window includes this ramp; no uncounted preramp or compensatory extra pulse is allowed.

Channel-summed exposure Q=sum_ticks sum_channels u*0.02 s is1197.6 pA*s for D and1192.8 for every C. Thus concentrated schedules deliver4.8 pA*s less (about0.401%); equal steady current is not equal window exposure. Multiplying by50 stimulated neurons/channel gives59880 and59640 pC of aggregate model-injected charge (59.88/59.64 nC). These are intracellular-equivalent model quantities, not electrode safety/energy measurements. Record channel-wise Q, current traces, slew, total current, time stamps and g*Q as a separately labeled effective model drive; receipts themselves remain unscaled by gain.

Secondary ramp sensitivity: compute responses and exposure only over the common fully ramped [15.06,20) s (4.94 s), without replacing the primary5 s gate. Every nonzero condition then has1185.6 pA*s exposure. Keep initial transient/history differences explicit; this is not a clean randomized charge-matched intervention.

## Outcomes and evaluator groups

Primary rate: exactly M002's raw observed unstimulated E count/(80 neurons*5 s), equivalent to averaging the four sector rates. No altered channel memberships, direct recordings, smoothing/window selection or hidden-state objective. Retain channel counts and existing causal filter output separately; do not switch the gate to a filtered endpoint.

Evaluator-only outcomes:

- Fixed full unstimulated E: the600 E neurons outside all four stimulation groups, constant across allocations (includes recorded80).
- Action-specific full unstimulated E: all E outside the active stimulation channels (600 for D,700 for C). Sham comparisons use the **same action-defined membership**, not all800 as a mismatched denominator.
- Directly active E:200 for D,100 for C; use identical cells in its paired sham. Sham has no directly stimulated cells, so this label is unavailable there rather than zero firing.
- All I:200 cells. Also all800 E and all1000 cells for descriptive checks.
- Sector rates: observed20 E/sector, fixed never-stimulated150 E/sector, all200 E/sector, and50 I/sector.

Record per-neuron whole-window spike counts,20 ms observed channel counts and sector rates. For each nonsham condition calculate intervention-minus-sham contrast within the same network/replicate/gain; then aggregate replicates. Record replicate SD, failures, constraints, initialization/simulation/analysis runtime and seed/source/protocol identities.

Mechanism: evaluator-only20 ms StateMonitor samples of I_E and I_I on all1000 cells; save aggregated time traces and means for the above groups/sectors, with total recurrent current=I_E+I_I. Sampling grid/timing is identical in sham and interventions. These decompositions are observational diagnostics, not causal inhibitory ablations. No pathway/model changes are authorized in this mission. Observed-only actions are frozen, so hidden data cannot choose them.

## Analysis and hierarchy

One observation is a complete5 s branch. Time bins and individual neurons are never independent replication units. Five independent-noise replicates are nested within each network, with common random numbers preserved across conditions and gains.

A/B: for D and each of six C allocations, report every network's mean paired response, sample SD across five replicates and pointwise95% Student-t CI (df4, critical2.7764451052). The unchanged gate is >=4 Hz in at least8/10 network mean responses. Also show lower-CI>=4 counts as a stricter uncertainty diagnostic, not a silently substituted gate. CIs depend on approximate normality and are imprecise with five replicates.

Across-network mean effects and C-minus-D differences:10,000 two-level bootstrap resamples, analysis seed20261021. Resample ten networks with replacement, then five replicate identities within each selected network. Use the same replicate indices across conditions/gains/groups for pairing. Percentile2.5/97.5% CIs are descriptive, pointwise; no multiplicity-adjusted significance claim or generalization to biological preparations. Report per-network results, not only pooled means.

C global implementable strategy: choose **one nonsham allocation** using observed E outcomes from replicates0–1 of all ten training networks, primary gain0.6 only. Maximize count of network calibration means>=4; tie maximize overall mean observed response; final tie fixed bank order D,C01,...,C23. Freeze that allocation and evaluate it on independent noise replicates2–4 (same training networks), df2 t critical4.3026527299. Report the resulting >=8/10 gate separately. This tests fixed-policy transfer to new noise, not unseen-network generalization. No hidden activity is used in selection.

D oracle upper bound: independently choose each network's largest observed mean over all five replicates, among seven nonsham actions. Report its selected identity, point estimate and gate count. This is evaluator-only hindsight selection; ordinary selected-action CIs are selection-biased and are not called confirmatory. Also show a split-noise per-network choice using replicates0–1 and evaluation2–4 as a diagnostic, without claiming an implemented calibration/identification method. Neither oracle result establishes an attainable future controller.

Report g1 by the same fixed allocations; the globally selected strategy remains selected at g0.6. Inspect response vs requested gain and current recruitment, but two positive amplitudes on different cell sets cannot identify a saturation curve. Weak recorded response, broad indirect limitations, competing inhibitory recruitment and saturation remain distinct possible explanations. Positive response alone is insufficient for tracking.

## Decision rules and boundaries

Diagnostic execution PASS requires all800 branches and50 baseline states, constraints/replay/sham checks and original regressions. Scientific authority PASS requires >=8/10 at>=4 Hz under a specifically named fixed or global split-noise-tested allocation. If none qualifies, retain V0 authority FAIL even if an oracle looks better. Missing cases yield PARTIAL; no model adjustment rescues the gate. A global strategy on training networks still requires an explicit protocol amendment because frozen V0 names D.

Propose, but do not execute, any next inhibitory-path ablation or amended target/actuation study. Do not implement identification, PI, MPC, RL, plasticity, hardware integration or a simulator rewrite. Stop after the report and review-branch commit.
