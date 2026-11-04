# M002.3 prospective calibration — frozen before neural experiments

Date: 2026-10-18. Starting HEAD a1c236e062c221523dc03e87d483301aa079e1c3, clean research/m002-2-reachability. Review branch research/m002-3-calibration. Entirely simulated instrument study; original V0.1 failure and M002.2 slow 7/10 HOLD remain unchanged.

## Resolution of proposal ambiguity

User M002.3 explicitly withholds true efficacy from calibration AND lookup. This supersedes the proposal's evaluator-known-gain q=q_eff/g assay for this mission. Primary lookup is **blind**, q=h^{-1}(target-b), frozen identically at both gains. No division by hidden gain, post-loss recalibration, oracle target, feedback or extrapolation. Eight branches remain S,C120,L,H at gains 1 and .6. This tests prospective calibration plus open-loop robustness, not the earlier known-gain assay. Failure at .6 is not proof of unreachable targets. Fixed target factor .6 is a public design assumption, never a gain input. Report this semantic change explicitly, without editing the historical proposal.

## Cohort, streams and bounded resources

All ten original training networks 0–9, exactly five new noise replicates 8,9,10,11,12, root seed 20261018; no replacement/exclusion or held-out networks. Original Config, Brian2 2.10.1, dt100us, model/topology, SeedSequence roles and time-indexed OU consumption unchanged. Network roles0–3 use replicate0; noise role4 uses replicate and absolute block. Full role definitions are inherited verbatim from existing provenance, not redefined. No randomized calibration actions. Same complete checkpoint and absolute-time innovations for all eight branches of a trial; distinct replicates independent.

50 trials x (51s prefix + 8x6s branches) =4950 simulated seconds; at most three spawned workers, one BLAS thread each. Ceiling75min scientific wall time, disk250MiB raw+curated, intended peak total worker RSS <5GiB (measure). Prior M002.2 4770s/2114.167s suggests ~36.6min; estimate only. Stop at ceiling or numerical/resource failure, preserve partial evidence, no unregistered rerun/replacement. Unit/regression checks and non-neural analysis are outside scientific wall budget. No other neural scientific probes.

## Exact causal prefix, seconds from reset

0–5 zero burn;5–15 zero baseline. b is observed unstimulated E count/(80*8s) over[7,15). Four sector baselines use20 cells each. Existing causal100ms filter retained, no observation redefinition.

15–19 zero,19–23 C02 q30;23–27 zero,27–31 q60;31–35 zero,35–39 q90;39–43 zero,43–47 q120. Holds and offsets ramp with <=30pA/channel/20ms. Score only final3s of each4s block, raw observed80E counts/(80*3s). h(0)=0; h(q)=hold mean−preceding-zero mean, q=30,60,90,120. All decisions use completed Observation counts/masks/coverage/timestamps and delivered receipts only. No future data, evaluator populations/connectivity/voltages or gain allowed into calibration. All prefix gain1 is evaluator configuration; algorithm has no gain argument. Require contiguous20ms observations, available=stop, complete valid masks/coverage and matching delivered/requested currents. Reject invalid data rather than fabricate zeros.

At47s freeze Rcal=h120, R*=.6Rcal; L=b+.1R*, H=b+.9R*, span=.8R*. No clipping/floor substitution/rescaling. Require finite positive Rcal and h[j+1]−h[j]>1e-9Hz (numerical strictness tolerance, not biological response threshold). Record all maps including failures. Piecewise linear inverse includes (0,0), no monotonic repair or extrapolation; denominator<=1e-9 or nonfinite inverse is invalid. Targets outside[0,h120] are invalid. Invalid calibration yields no lookup current; planned L/H branch runs a zero-current safe fallback, labeled invalid, and the network fails calibration/realization regardless of finite fallback output. Never relabel fallback as successful lookup.

47–51 zero washout with original slew; save full neural/queue/refractory/clock/filter/cursor/previous-command state at51s. Calibration consumes exactly prefix through47s; washout and confirmation cannot update b,h,targets,q. Prefix records preserved including ramps and zeros. Two active groups each50 cells: aggregate model charge=50*sum_channel current*time (pC); also report nominal pA*s, effective evaluator gain-scaled exposure, squared-current cost.

## Confirmation schedule

Fixed order gain1 S,C120,L,H then gain.6 S,C120,L,H. Every branch restores51s checkpoint, currents zero, runs[51,57). Desired C02 q=0,120,qL,qH respectively; slew-limit onsets, no offset after57s is included in exposure. Same qL/qH both gains. Evaluator alone sets gain; no recalibration or observed gain detection. All actions must satisfy0–120 per channel, sum<=240, delta<=30 per20ms. Invalid external command rejected atomically by existing engine; scientific fallback only as above, clearly recorded. Preserve actual requested/delivered rows and integer-us observation/action times. No retroactive action. Compare each stimulated branch with gain-matched S; S outputs must agree exactly across gains.

Report whole6s and late[52,57) means. Primary mean-output errors use raw80E late counts/(80*5s), **absolute observed rate−prospective target**, not paired-response errors. Retain raw1s epochs starting52s and original100ms filter as descriptive diagnostics. Evaluator-only population counts are permitted for audit, never action/target choice. No time bins counted as independent replicates.

## Frozen network-level joint gate (>=8 of10 required)

Across five noise replicates for each network:
1. All baselines b in[1,30]Hz, each baseline-sector mean<100Hz, finite instrument state, no timing/constraint/replay fault. Also flag any confirmation-sector6s mean>=100Hz as stability failure.
2. Mean span>=1Hz.
3. Mean span>=2sigma, where sigma=sqrt(mean_r sample_variance(five raw1s epochs of standalone S gain1 over[52,57))), ddof1. Secondary identical RMS SD of250 existing100ms-filter values, not used to choose scale.
4. Reduced headroom: m_r=(late C120(g.6)−late S(g.6))−(H_r−b_r). Mean(m)−2.7764451051977987*sd(m,ddof1)/sqrt(5)>=0 (two-sided95% t lower bound, df4).
5. Every replicate's map and interpolation valid (no repair or safe-fallback qualification).
6. For each of four gain x target cells separately, mean_r abs(late holdrate−target_r)/span_r<=.25. Invalid/nonpositive span/lookup fails, not omitted. Report low/high signed/absolute Hz errors and normalized errors per replicate and network, with t CIs (can extend below0 descriptively). No pooling or testing of bins.

Gate is conjunction; no Bonferroni reinterpretation of component engineering thresholds. Invalid calibration/nonfinite scientific values represented as null and explicit failure, not dropped. Execution faults ->executionPARTIAL/FAIL, not scientific model failure alone. All50 records and400 branches required for executionPASS, plus regressions and independently recomputed evidence. Scientific FAIL/HOLD if joint<8; retain any finite nonqualification without rescue. Thresholds never changed after outcomes.

## Analysis and uncertainty

Per-network means across five replicates are primary replication units. Report every network/replicate, all component counts and joint counts. Network aggregate pointwise95% percentile bootstrap10,000 network draws, seed20261023; resample whole networks of replicate-averaged quantities, not bins. Across-noise t CIs df4 for network summaries/headroom; five replicates have limited tail/variance precision. Qualification proportion reported with Wilson95% interval (z1.959963984540054); development networks are fixed selected training identities, interval is descriptive rather than held-out performance. No claim of independent100 observations from multiple endpoints, no posthoc exclusions, no inferential claims from100ms curves. Report paired S contrasts, dose/exposure and calibration monotonicity incidence; report delivered-budget differences among lookup holds, never equate steady current with integrated charge. No additional optimization/action bank.

## Verification and stop rules

Preserve SHA256 of every initially tracked file. Record committed prereg hash, execution source revision/status/hashes, full environment, seed keys/noise ledger, parameter hashes, complete actual schedules/counts/calibration inputs, checkpoint state digests, source files and outputs. Independently recompute b,h,targets,inverse,counts/filter/time/budgets/noise pairing/gates from saved evidence; recomputation must not simply trust saved target/gate JSON. Source review plus tests enforce pure observation-only calibration API, no true-gain parameter, frozen data separation, bad masks/timing/commands, inverse edge cases, exact math, independent role streams and exact restore. Existing46 regression tests retained. No external independent scientist or second simulator replication claimed. Preserve failures; numerical exceptions stop that trial and invalidate complete execution rather than replace it.

ExecutionPASS requires all50 trials/400 branches complete, no integrity violation, reproducible analysis and all regression/new tests passing. ScientificPASS only joint>=8. PASS applies only to slow simulated calibration/lookup instrument, not controllers, learning or biological control. If qualification fails, prioritize a preregistered stimulation-response identification objective rather than additional target engineering. No automatic next mission.
