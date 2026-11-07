# M005A.5 — complete reserved PI confirmation

**Execution PASS; scientific FAIL; stationary PASS; efficacy-loss recovery FAIL; M005B HOLD.**

## Preservation and revisions

Starting clean revision `bb1a7bc056cd6a36414cb2ca74d74059801de7f9`, branch `research/m005a-4-suspend-clock`; review branch `research/m005a-5-confirmation`. Prospective amendment011 committed `2781aa8556e77494598ac5a6dc37d4421cacdd7e` before new neural execution. Acquisition/preflight freeze revision `8802ed2029bb8658118fc62553d14f158f63eaa0`. Final publication revision is the commit containing this report, supplied exactly in the mission response. No merge/release.

All 9071 starting tracked files remain byte-identical, including prior failed authority, calibration, model-necessity and resource studies. No installed source changed in this mission. Protocol009, amendment010 and original stop decisions remain immutable. M005A and M005A.3 execution PARTIAL are not retrospectively relabeled. PI Kp=10 pA/Hz and Ki=5 pA/(Hz*s) remain frozen at selection revision `604302e9eecc491b8855a6ccbcaf4e195cb2adb2`; selection SHA256 `076604e732e1f97d02195c6d3798f0fba1998f4e9605c9492480cf51f794da36`.

## Continuation and exact scientific experiment

Reused original n0/r41, n0/r42 and n1/r41, after independent archive/provenance requalification. New acquisition contains exactly17missing identities: n1/r42, n2/r41, n2/r42, n3/r41, n3/r42, n4/r41, n4/r42, n5/r41, n5/r42, n6/r41, n6/r42, n7/r41, n7/r42, n8/r41, n8/r42, n9/r41, n9/r42. No trial/seed replacement, favorable exclusion or reselected gains. Aborted historical prefixes remain abort records and are not complete evidence. Reused and new sessions form one ten-network cohort with two noise repetitions, not two independent cohorts.

Every trial uses the original51 s observation-only calibration, baseline+1 Hz fixed target, eight32 s branches ZERO/FIXED/MAX/PI10_5 × STATIC/LOSS, 1 s completed raw E80 count feedback,20 ms observations/legal action ticks and100 us Brian2 integration. LOSS changes evaluator-only gain1→.6 at relative16 s. Exact prefix restoration and common absolute-time exogenous noise compare controllers/conditions. Original120 pA/channel,240 pA total and30 pA/tick slew apply. All calibration exposure is counted. No new neuron/topology/inhibition/target/controller definitions. Full evidence:20 prefixes/160 branches/6140 simulatedseconds; continuation:17 prefixes/136 branches/5219 simulatedseconds. Technical83 s duplicate replay is separate verification, not a statistical replicate. Validation10–14 and locked100–119 were not opened.

## Resource execution

New fixed deadline4800 s from capture entry, including imports, all17jobs and publication, maximum3workers. Actual suspend-inclusive duration **3125.495390 s**, diagnostic calendar duration **3125.483724 s**. Historical542.862513065 s plus new calendar duration is **3668.346237 s**, below original5400 s. This was a prospective remaining-work budget, not an extension of the old deadline. Clock `darwin.mach_continuous_time.ns.v1@7F7CEE11-4C83-4DAA-B9AA-1E99D6875897`; native consistency/boot identity qualified before acquisition. No intentional physical sleep, power-state test, clock reset or boot mismatch. No resource failure or abort in this acquisition.

Supervisor COMPLETED, all17worker leaders/group lifecycles REAPED; measured peak concurrency3. Peak completed-worker RSS1269956608 bytes; maximum sampled M005A allocation197038080 bytes; 555 resource samples. Worker<2 GiB and evidence<=500 MiB limits passed. Aggregate RAM not qualified. Idle sleep inhibition does not prevent forced clamshell sleep. Cleanup remains bounded per M005A.4; no post-deadline execution was accepted.

An unplanned clamshell suspension occurred during acquisition: OS logs record15:25:10–15:28:32, approximately202 s. The monitoring gap was203.910284125continuous seconds versus204.061189175calendar seconds; continuous-minus-uptime offset grew198.583518334 s between the preflight and recorded post-resume sample. Different sampling/rounded power timestamps are not equated. This naturally observed resume is not a deliberately controlled sleep test. Native clock checks continued to agree; boot ID and original absolute deadline were unchanged. Suspend time consumed the4800 s budget; no resumed work received a fresh allowance. Neural virtual time and deterministic noise streams do not advance during CPU suspension. Read-only OS logs and timing_gap_audit.json preserve this event; historical M005A.3 stop remains unchanged.

## Original frozen gates

Principal replication unit is network: average noise41/42 within each of10 networks before inference. PCG64 seed20261025,10000 paired network bootstrap draws, percentile95% intervals. Stationary[8,32)s and loss[20,32)s evaluated separately. Joint per-network gate requires both calibrations/baselines valid,1 Hz>=2*RMS baseline1sSD, lateMAX−ZERO>=1.2 Hz, PI MAE<=.35 Hz, |bias|<=.2 Hz and>=30%MAEbenefit vsZERO. At least8/10 joint plus positive cohort ZERO-benefit lower95% bound. Recovery additionally requires PI versus FIXED>=20%mean paired relative,>=.1Hzabsolute, lower95%bound>0 andpositive>=8/10. No fallback in base scientific cases. These rules were not changed after outcomes.

## Complete numerical results

All per-trial/window numerical values are in [metrics.csv](evidence/m005a_5/confirmation_analysis/metrics.csv), all 40network/noise/regime primary comparisons in [per_replicate_errors.csv](evidence/m005a_5/per_replicate_errors.csv), all1 s trajectories in traces.csv, and all 20calibrations/latencies/costs in secondary.json. No omitted failed or unfavorable network. Tables below average two noise repetitions within each network.

| Network | Regime | PI MAE Hz | FIXED MAE Hz | ZERO MAE Hz | PI bias Hz | Authority Hz | Baseline SD Hz | Joint pass |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | LOSS | 0.320703 | 0.452474 | 1.031510 | -0.232552 | 1.756250 | 0.274001 | False |
| 0 | STATIC | 0.261393 | 0.197982 | 1.051302 | -0.001563 | 2.850000 | 0.274001 | True |
| 1 | LOSS | 0.271224 | 0.348828 | 0.880990 | -0.197135 | 1.691146 | 0.255866 | True |
| 1 | STATIC | 0.354818 | 0.245443 | 0.879948 | 0.044010 | 2.786458 | 0.255866 | False |
| 2 | LOSS | 0.257812 | 0.383854 | 1.031771 | -0.249479 | 1.479688 | 0.325849 | False |
| 2 | STATIC | 0.145052 | 0.225521 | 0.989062 | -0.003385 | 2.310937 | 0.325849 | True |
| 3 | LOSS | 0.263151 | 0.342969 | 0.952865 | -0.174219 | 1.969271 | 0.281109 | True |
| 3 | STATIC | 0.232161 | 0.227214 | 0.983073 | -0.012240 | 3.224479 | 0.281109 | True |
| 4 | LOSS | 0.257812 | 0.426302 | 1.035938 | -0.189063 | 1.828646 | 0.242419 | True |
| 4 | STATIC | 0.200391 | 0.182812 | 1.012760 | -0.014583 | 2.910937 | 0.242419 | True |
| 5 | LOSS | 0.270833 | 0.334635 | 0.947135 | -0.239844 | 1.212500 | 0.274307 | False |
| 5 | STATIC | 0.212305 | 0.368620 | 0.898177 | 0.043490 | 2.092188 | 0.274307 | True |
| 6 | LOSS | 0.280208 | 0.438932 | 1.085156 | -0.244010 | 1.556250 | 0.268280 | False |
| 6 | STATIC | 0.193945 | 0.201237 | 1.087500 | -0.030208 | 2.469271 | 0.268280 | True |
| 7 | LOSS | 0.212500 | 0.422396 | 1.032813 | -0.172396 | 1.761458 | 0.196822 | True |
| 7 | STATIC | 0.230339 | 0.227604 | 1.052083 | -0.003385 | 2.987500 | 0.196822 | True |
| 8 | LOSS | 0.251562 | 0.408073 | 1.004948 | -0.212760 | 1.486458 | 0.238575 | False |
| 8 | STATIC | 0.228255 | 0.213997 | 0.961719 | 0.020573 | 2.524479 | 0.238575 | True |
| 9 | LOSS | 0.218750 | 0.426562 | 1.017448 | -0.184635 | 1.625521 | 0.209148 | True |
| 9 | STATIC | 0.194987 | 0.227409 | 1.024479 | 0.011979 | 2.577604 | 0.209148 | True |

| Policy | Stationary MAE Hz [95% CI] | Loss late MAE Hz [95% CI] |
|---|---|---|
| ZERO | 0.994010 [0.953385, 1.031354] | 1.002057 [0.965154, 1.034427] |
| FIXED | 0.231784 [0.207819, 0.265144] | 0.398503 [0.372355, 0.422773] |
| MAX | 1.662292 [1.466945, 1.850507] | 0.644609 [0.524140, 0.766250] |
| PI10_5 | 0.225365 [0.196028, 0.260911] | 0.260456 [0.243007, 0.278997] |

## Gate outcomes and interpretation

STATIC: **9/10 joint networks**, ZERO-benefit95%CI [0.7009505208333333, 0.8229171549479166]. Passing component counts: calibration_baseline_valid=10, noise_valid=10, authority=10, error=9, bias=10, zero_benefit=10.
LOSS: **5/10 joint networks**, ZERO-benefit95%CI [0.6998955078125, 0.7790237630208334]. Passing component counts: calibration_baseline_valid=10, noise_valid=10, authority=10, error=10, bias=5, zero_benefit=10.

PI versus FIXED late-loss advantage: mean absolute **0.138047 Hz**,95%CI [0.10729166666666676, 0.16851595052083337]; mean paired relative **33.899%**,95%relativeCI [0.2783813792257054, 0.40171868544311007]; positive in **10/10**, denominator floor activated0 times. Additional recovery gate: True.

Invalid calibrations: 0; adjacent dose reversals: 1. Base fallback decisions: **0**; receipt/current/slew constraint violations: **0**. Complete counts, validity and policy records are independently reconstructed, not inferred from a successful process exit.

Stationary PI versus well-calibrated FIXED is descriptive, not a frozen superiority gate:
- STATIC: PI−FIXED mean MAE difference -0.006419 Hz; PI has higher MAE on 6/10 networks.
- LOSS: PI−FIXED mean MAE difference -0.138047 Hz; PI has higher MAE on 0/10 networks.

All ten networks pass calibration, baseline noise and finite MAX−ZERO authority checks in both regimes. Stationary network1 misses the MAE limit (.354818 Hz). After loss, networks0,2,5,6,8 miss the signed-bias criterion: every failure is negative undertracking, while all ten pass the late MAE criterion. Thus the failed qualification concerns finite-horizon realization, despite demonstrated reference authority and a meaningful PI benefit over FIXED. This is consistent with incomplete recovery; it does not establish permanent steady-state bias or its mechanism.

## Current cost and excitation

| Policy | Regime | Mean calibration+online model charge nC | Mean online exposure pA*s | Decision-clipping flag fraction |
|---|---|---:|---:|---:|
| ZERO | STATIC | 120.000000 | 0.000000 | 0.000000 |
| ZERO | LOSS | 120.000000 | 0.000000 | 0.000000 |
| FIXED | STATIC | 267.416355 | 2948.327096 | 0.000000 |
| FIXED | LOSS | 267.416355 | 2948.327096 | 0.000000 |
| MAX | STATIC | 503.640000 | 7672.800000 | 0.000000 |
| MAX | LOSS | 503.640000 | 7672.800000 | 0.000000 |
| PI10_5 | STATIC | 262.534714 | 2850.694284 | 0.000000 |
| PI10_5 | LOSS | 283.127214 | 3262.544284 | 0.000000 |

Delivered bound occupancy is separate from the decision-clipping flag above: ZERO is at zero current for100%of online ticks; MAX reaches120 pA per active channel /240 pA total for99.8125%of online ticks, following its three-tick ramp. FIXED and PI have zero online ticks at either C02 dose bound in this cohort. The two inactive channels are identically zero and are not counted as C02 dose saturation. All160branch occupancies are in delivered_bound_occupancy.csv. These descriptive measures do not change any acceptance gate.

Charge is50stimulatedcells/channel times delivered current integral, an intracellular-equivalent model quantity, not an extracellular biological safety charge. Calibration is the same51 s procedure for every policy; total cost includes it. No injected exploratory stimulation. C02 keeps two channels zero and two identical, so41-feature four-channel FIR design is structurally deficient; positive-subspace conditioning does not prove independent persistent excitation.
- ZERO, LOSS last16 s: ranks [1]/41; qSD median 0.000000 pA; positive-subspace condition median 1.000000; changed-tick median 0.0.
- FIXED, LOSS last16 s: ranks [1]/41; qSD median 0.000000 pA; positive-subspace condition median 1.000000; changed-tick median 0.0.
- MAX, LOSS last16 s: ranks [1]/41; qSD median 0.000000 pA; positive-subspace condition median 1.000000; changed-tick median 0.0.
- PI10_5, LOSS last16 s: ranks [11]/41; qSD median 6.186478 pA; positive-subspace condition median 53.198794; changed-tick median 15.0.

## Verification and actual commands

Environment: /tmp/neuromancer-m004-venv Python3.12.15, Brian2 2.10.1, NumPy2.5.4, macOS26.5.2arm64. VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/neuromancer-m005a-mpl requested throughout; actual BLAS thread behavior is not certified.

```sh
/tmp/neuromancer-m004-venv/bin/python reports/evidence/m005a_5/run_commands.py reports/evidence/m005a_5/preflight_config.json
/tmp/neuromancer-m004-venv/bin/python reports/evidence/m005a_5/acquire.py
/tmp/neuromancer-m004-venv/bin/python reports/evidence/m005a_5/run_commands.py reports/evidence/m005a_5/verification_config.json
/tmp/neuromancer-m004-venv/bin/python reports/evidence/m005a_5/finalize.py
```

Exact child commands/deadlines/exit codes are archived in configuration and supervisor records. Preflight144 passed; final144 passed, including full neural/controller regression and independently watchdog-bounded supervisor failure injections. Both shared1200 s stages completed. Native1000 samples plus child verify consistent boot scope/API readings. Independent historical re-audit preceded neural acquisition. Final independent verifier reconstructed all 20 trials/160 branches/800metric rows from spike events, causal rates/calibration/PI/projection/receipts, matched condition prefixes, representative exogenous noise blocks and parameter identities. This is independent numerical reconstruction within the same session, not external replication. Source hashes verified against respective acquisition Git revisions; scientific sources remain identical. Missing old partial branches are never scored as complete.

Independent supplementary verification reconstructed320excitation spectra,160charge totals and8network-bootstrap model intervals. Public-only causal mutation replay confirmed future observations cannot change earlier commands, earlier completed observations can affect later commands, and missing observations trigger safe next-tick handling. Exact cold n0/r41 prefix+LOSS_PI10_5 technical replay passed25 numerical-array comparisons in116.599730167 s; no new noise replicate or statistical trial was created. Repeated analysis/figures match byte-for-byte except summary runtime. Final verification records include explicit deadline/lifecycle closure, not just unit-test results.

## Scientific decision, limitations and next experiment

Execution **PASS**. Stationary **PASS**. Efficacy-loss recovery **FAIL**. Full scientific control qualification **FAIL**. M005B **HOLD**. This decision applies only to unchanged simulated instrument and fixed1 Hz regulation; it does not rehabilitate historical V0.1/V0.2 failures, establish biological control/plasticity or prove adaptive-MPC superiority. No next mission is automatically authorized.

Ten development networks were previously studied; confirmation reserves new noise, not new network identities. Two repetitions provide limited stochastic precision. Percentile intervals reflect the finite network sample; nonsignificance is not equivalence. Only finite MAX/ZERO reference authority is observed, not mathematical reachability. Gain loss is an actuator perturbation, not biological learning. The two-session chronology and previously observed three outcomes are explicitly retained; there was no reselection or changed decision rule. Physical sleep was not deliberately tested; qualified platform suspend semantics and actual clock records apply. Process groups exclude deliberately detached hostile descendants; filesystem/OS responsiveness remains an engineering assumption.

If full scientific qualification fails, the next falsifiable study should examine the failed original components with an independently preregistered research-direction decision, not reduce targets, tune neural parameters or begin adaptive MPC. If it passes, a separately authorized, network-disjoint replication with frozen PI would test generalization before any claim of adaptive-controller advantage. A concrete next falsifiable proposal is a separately preregistered64 s fixed-PI loss diagnostic: retain gain loss at16 s and the original20–32 s failed-window result, then test whether |network mean bias| over48–64 s falls below.2 Hz in at least8/10development networks with unchanged PI10/5, target and bounds. It would distinguish slow recovery from longer-lived offset; it could not reclassify M005A.5 or authorize MPC. This is a proposal requiring separate authorization, not an extension executed here. No such experiment ran here.

Figures: [network errors](evidence/m005a_5/confirmation_analysis/network_error.png), [loss time courses](evidence/m005a_5/confirmation_analysis/loss_timecourses.png), [actions and costs](evidence/m005a_5/confirmation_analysis/actions_and_costs.png). Complete source/configuration/seed/session/hash manifests and all raw outcomes are retained under evidence/m005a_5.

Final archival resource check: 261296128 allocated bytes across all M005A experiment/evidence/run directories before final inventory sealing, below524288000bytes. Preflight supervision took68.717198834s; the main verification stage took251.397506250s. Publication stages inherited the same absolute verification deadline. See final_resource.json for lifecycle records.
