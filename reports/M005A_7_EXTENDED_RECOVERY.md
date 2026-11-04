# M005A.7 — prospective extended-horizon PI recovery

**Execution PASS; scientific PASS; extended recovery PASS; stationary guardrail PASS. M005B HOLD. Historical M005A.5 remains FAIL.**

## Revision, preservation and preregistration

Starting clean revision `2cfc546493534f78caa1fa95fc9fa442a5fc9260`, branch `research/m005a-6-recovery-diagnosis`. Review branch `research/m005a-7-extended-recovery`. Protocol first committed at `40ee4b71f472beaef4ab3d8610a29f9d6ffc7148` before any new neural trajectory or neural regression fixture. Source/test freeze `4a1f6a59acafc558a6f08eb888fc2f48c52064ba`; passing preflight/acquisition revision `5332f4291b0a17098d047b32ea8a4b818bfe007a`. The intervening protocol edits removed an arithmetic drafting aside and clarified incremental public snapshots; no cohort, numerical endpoint, scientific gate or budget changed. Final revision is the commit containing this report, supplied exactly in the mission response. No merge.

Preservation manifests verify all starting tracked files, including M005A–M005A.6 reports, protocols, code, datasets, tests and negative findings. Existing installed source is byte-identical. Only two new thin modules were added: extended_recovery.py for evaluator stepping using the unchanged Policy/calibration/projector, and recovery_metrics.py for new finite-horizon endpoints. No PI gains, neural equation/parameter, synapse, topology, observation definition, target rule or action bound changed.

## Frozen prospective experiment

[Protocol](../docs/research/010_M005A_7_EXTENDED_RECOVERY_PROTOCOL.md): control duration 64 s after original 51 s calibration; target remains baseline+1 Hz for the whole extension. Hidden efficacy 1→.6 at relative 16 s/absolute 67 s; STATIC gain1 throughout. Primary window 48–64 s (32–48 s after loss), persistence blocks 48–56 and 56–64 s, selected from the prior diagnostic proposal before new acquisition. New target setpoints were not chosen from responses. Kp=10 pA/Hz, Ki=5 pA/(Hz*s), original feedforward/anti-windup/projection/fallback. Selection revision604302e9eecc491b8855a6ccbcaf4e195cb2adb2, SHA256076604e732e1f97d02195c6d3798f0fba1998f4e9605c9492480cf51f794da36.

Fresh noise 45/46 on every development network 0–9, root 20261018/existing SeedSequence roles. 20 independent network/noise trials, each with five 64 s branches: STATIC_PI10_5, LOSS_PI10_5, STATIC_FIXED, LOSS_FIXED, LOSS_MAX. Same exact 51 s neural checkpoint/common absolute-time noise across branches, fresh policy only at branch start. No reset at 16 s or 32 s. STATIC MAX and ZERO were omitted prospectively to limit compute: MAX authority is measured directly against the actual target at reduced efficacy, not historical MAX−ZERO. No historical response was substituted as a new reference. Total 7420 simulated seconds=1020 calibration+6400 control; all 100 branches/20 prefixes retained. No unfavorable seed replacement/exclusion, validation 10–14 or locked 100–119 access.

Clocks remain 100 us neural integration,20 ms nonoverlapping observations/legal stimulation updates,1 s completed raw-E80 count feedback and separate suspend-inclusive wall deadline. Current C02=(q,0,q,0),120 pA/channel,240 pA total,30 pA/tick slew. All current actions are selected before their neural advance, then observations update the same policy for subsequent actions. Terminal 64 s/absolute 115 s state is recorded, never delivered. Controllers receive no gain or private neural state.

## Scientific gates and aggregation

Principal replication unit is network. Average noise 45/46 within network before inference. A network must have both valid calibrations/baselines,1 Hz>=2*RMS baseline 1 s SD, raw1 s MAE<=.35 Hz and |signed bias|<=.2 Hz in the full 48–64 s window AND each disjoint 8 s block. LOSS additionally needs mean reduced-efficacy MAX−actual-target margin>=.2 Hz. No scientific-base fallback, missing observation, invalid receipt or constraint violation. At least 8/10 joint networks plus cohort late signed-bias 95%bootstrap CI fully inside [−.2,.2] Hz are required separately for LOSS and the STATIC guardrail. Full new scientific PASS requires both and globally valid base cases. PCG64 seed 20261025,10,000 paired network-bootstrap draws. These are new finite-horizon criteria, not a retroactive change to M005A.5.

Multiple disjoint 8 s means and MAE limits require sustained sampled tracking; a single target crossing or filtered fluctuation cannot qualify. Scoring uses raw counts, not 100 ms filtered activity or a selected moving-window minimum. Trailing 8 s curves and final settling descriptors are descriptive, not alternate primary endpoints. No asymptotic stability/equivalence theorem is claimed.

## Complete network-level outcomes

| Net | Regime | Late bias Hz | Block1 bias Hz | Block2 bias Hz | Late MAE Hz | MAX margin Hz | Joint pass |
|---:|---|---:|---:|---:|---:|---:|---|
| 0 | LOSS | -0.038281 | -0.021094 | -0.055469 | 0.240918 | 0.858984 | True |
| 0 | STATIC | 0.011719 | 0.007031 | 0.016406 | 0.228906 | 0.858984 | True |
| 1 | LOSS | 0.035156 | 0.040625 | 0.029687 | 0.180762 | 0.814844 | True |
| 1 | STATIC | 0.042969 | 0.077344 | 0.008594 | 0.257227 | 0.814844 | True |
| 2 | LOSS | -0.026563 | -0.113281 | 0.060156 | 0.205469 | 0.447656 | True |
| 2 | STATIC | 0.025000 | -0.036719 | 0.086719 | 0.269141 | 0.447656 | True |
| 3 | LOSS | -0.033984 | -0.023438 | -0.044531 | 0.208984 | 0.977734 | True |
| 3 | STATIC | -0.002344 | -0.014063 | 0.009375 | 0.188281 | 0.977734 | True |
| 4 | LOSS | -0.033984 | 0.028125 | -0.096094 | 0.263672 | 0.828125 | True |
| 4 | STATIC | -0.022266 | 0.037500 | -0.082031 | 0.304980 | 0.828125 | False |
| 5 | LOSS | -0.056250 | -0.095313 | -0.017188 | 0.240430 | 0.307031 | True |
| 5 | STATIC | -0.025000 | 0.032031 | -0.082031 | 0.245215 | 0.307031 | True |
| 6 | LOSS | -0.057031 | -0.053125 | -0.060937 | 0.262207 | 0.559766 | True |
| 6 | STATIC | -0.015234 | -0.006250 | -0.024219 | 0.262500 | 0.559766 | True |
| 7 | LOSS | -0.057813 | -0.032031 | -0.083594 | 0.207227 | 0.762500 | True |
| 7 | STATIC | -0.030078 | -0.008594 | -0.051562 | 0.193652 | 0.762500 | True |
| 8 | LOSS | -0.050391 | -0.036719 | -0.064063 | 0.229297 | 0.351172 | True |
| 8 | STATIC | -0.028516 | -0.039844 | -0.017188 | 0.255664 | 0.351172 | True |
| 9 | LOSS | -0.041797 | -0.015625 | -0.067969 | 0.216699 | 0.678516 | True |
| 9 | STATIC | -0.026172 | 0.028125 | -0.080469 | 0.195996 | 0.678516 | True |

Stationary network 4 fails the first-block MAE requirement (0.370703 Hz > 0.35 Hz), despite acceptable full-window MAE and bias. It remains included. Nineteen of twenty LOSS PI repeats meet the descriptive sustained-settling definition by the finite horizon; n5/r45 is censored at 48 s after loss. This does not change the frozen network-mean gate. The MAX margin column is always the matched LOSS MAX reference, including beside STATIC rows for context; it is not a STATIC gate. Complete two-repeat outcomes and every window/component are in metrics.csv, calibrations.csv, gate_inputs.json and network_qualification.csv. No network was dropped.

| Policy/regime |48–64 s signed bias Hz [95%CI] | MAE Hz [95%CI] | Whole prefix+64 s model charge nC |
|---|---|---|---:|
| STATIC_PI10_5 | -0.006992 [-0.020664,0.009141] | 0.240156 [0.218037,0.262158] | 400.799956 |
| LOSS_PI10_5 | -0.036094 [-0.049023,-0.017617] | 0.225566 [0.209902,0.240997] | 502.603393 |
| STATIC_FIXED | 0.028594 [-0.019298,0.083829] | 0.222969 [0.200683,0.245109] | 407.170659 |
| LOSS_FIXED | -0.379258 [-0.422656,-0.333984] | 0.404102 [0.367255,0.439571] | 407.170659 |
| LOSS_MAX | 0.658633 [0.520781,0.789687] | 0.669297 [0.540566,0.793413] | 887.640000 |

## Bias persistence, recovery and controller state

STATIC: 9/10 joint, biasCI [-0.020664062500000132, 0.009140624999999975], gate=True; component counts: calibration=10, noise=10, headroom=10, bias=10, block_bias=10, mae=10, block_mae=9, valid=10.
LOSS: 10/10 joint, biasCI [-0.04902343750000003, -0.017617187500000072], gate=True; component counts: calibration=10, noise=10, headroom=10, bias=10, block_bias=10, mae=10, block_mae=10, valid=10.

| Network | Fresh-cohort PI bias20–32 s Hz | PI bias48–64 s Hz | Mean terminal I pA | LOSS repeat settling delays after loss s |
|---:|---:|---:|---:|---|
| 0 | -0.072135 | -0.038281 | 15.468750 | 17 / 40 |
| 1 | -0.158073 | 0.035156 | 22.562500 | 42 / 44 |
| 2 | -0.198438 | -0.026563 | 27.968750 | 23 / 42 |
| 3 | -0.247396 | -0.033984 | 22.562500 | 22 / 24 |
| 4 | -0.250521 | -0.033984 | 28.281250 | 44 / 44 |
| 5 | -0.211198 | -0.056250 | 31.750000 | censored48 / 46 |
| 6 | -0.181771 | -0.057031 | 28.343750 | 47 / 21 |
| 7 | -0.223698 | -0.057813 | 30.781250 | 19 / 28 |
| 8 | -0.251563 | -0.050391 | 38.625000 | 28 / 38 |
| 9 | -0.198177 | -0.041797 | 25.437500 | 23 / 46 |

The 20–32 s column is a diagnostic on FRESH noise 45/46; it is not a revised estimate of the historical 41/42 result. The same controller and target continue through 32 s. All 64 one-second observations, signed errors, decisions/integrals and sector rates are in traces.csv; all 5700 trailing8 s windows in moving8.csv. Recovery.csv records first three consecutive absolute errors<=.35 Hz (first endpoint plus causal confirmation2 s later), strict sign-crossing counts and retrospective sustained settling. Sustained settling requires both 8 s halves of a 16 s post-loss window AND every later window through64 s to meet bias/MAE limits. Censor at 48 s post-loss. STATIC descriptors use the matched 16 s reference, not a fictitious gain change. These are finite observed-horizon descriptors; later divergence remains possible.

Current expenditure, current², bound occupancy, clipping/anti-windup and complete delivered four-channel histories are retained. Inactive channels 1/3 remain zero; delivered q bounds differ from Policy clipping flags (MAX is at its bound without a PI clipping flag). Model charge is 50 cells/channel times nominal current integral, including all 51 s calibration/ramp exposure; it is not extracellular biological charge/energy. Saturation is disclosed, not treated as a hidden target change.

| Policy/regime | Mean late total delivered pA | Dose-at120 fraction | Dose-at0 fraction | Decision clipping fraction | Anti-windup fraction |
|---|---:|---:|---:|---:|---:|
| STATIC_PI10_5 | 86.952081 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| LOSS_PI10_5 | 141.727862 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| STATIC_FIXED | 89.750128 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| LOSS_FIXED | 89.750128 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| LOSS_MAX | 240.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 |

Base fallback decisions=0; constraint violations=0. All branch receipts/masks/timestamps and complete markers were independently checked, not inferred from process success.

## Matched controls, authority and uncertainty

STATIC PI versus FIXED late MAE benefit=-0.017187 Hz, paired 95%CI [-0.04934667968750001, 0.014746337890625065], positive in5/10. This is descriptive; superiority over FIXED was not a primary success gate.
LOSS PI versus FIXED late MAE benefit=0.178535 Hz, paired 95%CI [0.13842773437500017, 0.21691650390625014], positive in10/10. This is descriptive; superiority over FIXED was not a primary success gate.

STATIC and LOSS share identical pre-loss observations, decisions and inputs for each policy. First possible PI response to post-loss observations is 17 s; inputs also match through the 16–17 s interval. FIXED delivered histories match throughout. The MAX branch is one global fixed admissible action, not an oracle selected per network. Headroom is finite noisy policy evidence, not the mathematical reachable set or a guarantee of arbitrary-state tracking. No gain information entered PI/FIXED; stationary controls expose harm/noise rather than assuming feedback must improve performance.

## Actual execution and resource limits

Acquisition completed in2187.636798 s suspend-inclusive, diagnostic calendar2187.726550 s, against the fixed 6600 s cap. All 20 workers completed/reaped with at most 3 concurrent workers. Peak trial RSS=1357791232 bytes (<2 GiB); maximum sampled new evidence=104144896 bytes (<150 MiB); all-M005A allocation=377491456 bytes (<500 MiB). Root clock=darwin.mach_continuous_time.ns.v1@7F7CEE11-4C83-4DAA-B9AA-1E99D6875897. Worker/per-block perf_counter timings are uptime-based on macOS and are distinct from the authoritative continuous budget clock.

Resource samples=418; measured intersample elapsed range5.158145–5.965510 s, active-clock maximum5.943589 s. The implementation requests a5 s sleep between samples; actual cadence includes resource-inspection/OS overhead and is not a hard5 s real-time bound. This is a disclosed monitoring-cadence deviation from the protocol's nominal<=5 s wording; exact completed-worker high-water RSS independently verifies the memory cap. No deadline, memory or disk allowance was enlarged. Continuous-minus-uptime offset growth over sampling=-0.000001 s; no deliberate physical sleep test or wake-time guarantee. Any natural pause consumes the original budget; boot/API failures fail closed. See resource_samples.jsonl and final resource verification for actual timing and storage.

Initial acquisition forecast used prior actual 5219 simulatedseconds/3125.495 s as a planning ratio, not a benchmark. Incremental 16 s public snapshots preserve completed data/controller state; all 360 prefix/branch snapshot segments match their completed archives. Snapshots are not independently scored trials or restored neural checkpoints. Only trial.json with all five complete branches qualifies. No stage was retried after a resource failure; no failed/unfavorable seed replacement. OS scheduling, filesystem responsiveness and process-group containment remain assumptions; deliberately escaped/uninterruptible hostile descendants are outside qualified scope.

## Tests, independent verification and exact lineage

Preflight157 passed and final157 passed, with 25 existing warnings. New tests cover 64 vs 32+32 stepping, continuity/no reset, gain boundary16 s, end 64 s, exact time ordering/constraints, missing or duplicate repeats, invalid metrics and rejection of single crossings/blockwise bias cancellation. Full historical neural/controller/supervisor failure-injection suite ran. Native 1000 sample plus child-domain preflight passed before acquisition.

Independent numerical audit PASS: 20 trials,100 branches,320000 control bins,800 metric rows,6400 one-second records,5700 moving windows,360 snapshot segments and 6400 scalar policy update checks. Event counts, original calibration, PI recurrence, all currents/receipts/constraints, matched pre-loss records, parameters/channel disjointness,115 noise-block hashes per branch (representative blocks independently regenerated), all gates and network intervals were reconstructed. Source hashes match acquisition revision 5332f4291b0a17098d047b32ea8a4b818bfe007a; starting historical hashes and frozen selection match. Independent reconstruction is within-session verification, not external replication.

Cold technical replay re-executed the original unsegmented 51 s prefix and original 32 s feedback loop for n0/r45 and matched the extended archive prefix/first 32 s, including its state at 32 s. This 83 s replay is not an extra statistical replicate; no 64 s cold neural replay is claimed. Full 64 s controller recurrence/continuity and synthetic 64 vs 32+32 equivalence are separately verified. Public-only future-observation mutation/causal safe-fallback fixtures passed. Repeated complete analysis and deterministic PNG/SVG figures match byte-for-byte.

```sh
/tmp/neuromancer-m004-venv/bin/python reports/evidence/m005a_7/run_commands.py reports/evidence/m005a_7/preflight_config.json
/tmp/neuromancer-m004-venv/bin/python reports/evidence/m005a_7/acquire.py
/tmp/neuromancer-m004-venv/bin/python reports/evidence/m005a_7/run_commands.py reports/evidence/m005a_7/verification_config.json
# Report/archive publication inherits verification_supervision/terminal.json deadline and domain.
```

Exact child commands, timestamps, exit codes, source/config/seed/OU/checkpoint manifests and all raw/partial/public snapshots are retained. Requested VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/neuromancer-m005a-mpl; actual BLAS threading unverified. Python3.12.15/Brian2 2.10.1/NumPy2.5.4/macOS arm64. No dependency installation, model training or hidden-state controller input.

## Scientific interpretation and stop

Extended recovery=PASS; stationary guardrail=PASS; full new scientific result=PASS. This decision applies only to the preregistered 64 s horizon,48–64 s endpoint, fixed1 Hz offset and fresh noise on the same ten development networks. M005A.5 remains FAIL at its original shorter horizon. Neither a late successful block nor a favorable moving-window crossing revises that history.

The new conjunction passes: all ten networks meet the reduced-efficacy recovery criteria and nine meet the stationary guardrail. Unchanged PI therefore shows sustained finite-horizon recovery in this regime. Together with positive MAX headroom and unsaturated PI, this supports slow compensation as an explanation of the earlier short-horizon deficit. It does not establish asymptotic stability, optimal control, adaptive-model necessity, biological recovery or rapid recovery within the historical horizon. Stationary PI has no demonstrated MAE advantage over FIXED; the paired interval includes zero. No gate was weakened.

**M005B HOLD.** This experiment does not authorize MPC, adaptive control, RLS control, RL, plasticity, hardware or locked-network evaluation. Next falsifiable proposal: a separately authorized frozen-controller replication on network-disjoint confirmation identities, with this same 64 s protocol and competitive FIXED/reference conditions. Failure there would limit generalization beyond repeatedly studied development networks. No next experiment was run.

Limitations: ten repeatedly studied development networks, two noise replicates, fixed channel allocation/single setpoint; bootstrap intervals are finite-sample approximations; bias tolerance is an engineering choice; reference headroom does not prove mathematical controllability; retrospective settling uses future-to-origin observations only in the evaluator, never the controller; physical wake/real-time neural hardware and biological relevance are not established.

[Loss time courses](evidence/m005a_7/analysis/loss_timecourses.png), [network bias](evidence/m005a_7/analysis/network_bias.png), [current and moving bias](evidence/m005a_7/analysis/current_moving_bias.png). Complete per-repeat outcomes and moving/settling/cost data are in evidence/m005a_7/analysis; raw observations and receipts in evidence/m005a_7/trials.
