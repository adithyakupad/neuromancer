# M005A.7 extended recovery protocol — version1, prospective

Starting clean revision2cfc546493534f78caa1fa95fc9fa442a5fc9260; review branch research/m005a-7-extended-recovery. Commit before any new neural execution, including regression fixtures. Filename010 is the explicitly requested mission-specific name; it does not replace amendment010_M005A_3. Protocol009 and every prior failure remain unchanged. M005A.5 remains scientific FAIL; M005B HOLD regardless of this new study's outcome.

## Hypothesis and fixed horizon

H1: unchanged PI10/5 sustains acceptable recorded E80 regulation after hidden1→.6 actuator efficacy loss when given a fixed longer recovery period. Control lasts64s after the original51s calibration; gain loss remains at relative16s (absolute67s). Primary window is **48–64s** (32–48s after loss), chosen from M005A.6's proposal before any new trajectory. Persistence windows are **48–56s and56–64s**, nonoverlapping. Target remains the SAME calibration baseline+1Hz through64s: fixed extension, not new future setpoints. Preserve/report20–32s unchanged as an early-window diagnostic on the fresh cohort; never reclassify the old failed cohort/window.

This is finite-horizon evidence, not asymptotic stability, eventual convergence at arbitrary times or biological control. All scientific thresholds below are new prospective engineering criteria for this horizon, not inherited evidence of original success.

## Cohort and fixed conditions

Networks0–9, fresh independent noise45,46, root20261018 and existing SeedSequence roles unchanged. No seed replacement or exclusion. Validation10–14 and locked100–119 unopened. One51s original calibration prefix per pair, exact checkpoint, FIVE branches in order:

1. STATIC PI10_5
2. LOSS PI10_5
3. STATIC FIXED
4. LOSS FIXED
5. LOSS MAX

All branches64s, same exact prefix state and common exogenous streams at matched absolute times. STATIC MAX adds no necessary stationary feedback/reference comparison, so is omitted prospectively to limit computation; MAX under LOSS is the primary authority reference. ZERO is not acquired: headroom is measured directly against the actual target, not MAX−ZERO. Existing historical MAX/ZERO results are not substituted as new controls. Total20prefixes/100branches, **7420simulatedseconds** (20*(51+5*64)): prefixes1020s plus control6400s =7420s. All outcome data retained.

## Frozen scientific instrument

Unchanged Brian2 2.10.1 recurrent E/I LIF dynamics, connectivity, currents, OU generation, spike memberships, units and100us integrator. Original20ms observation/stimulation bins and100ms causal filter remain archived; scoring and feedback use raw nonoverlapping1s counts (50completed bins). Original C02=(q,0,q,0),120pA/channel,240pA total,30pA/channel/tick slew. Same projection, missing-data safe fallback and anti-windup. Target fixed atb+1Hz, baseline and calibration from original51s prefix and unchanged observation-only slope/qff validity rules. Kp10pA/Hz, Ki5pA/(Hz*s), original feedforward, integral limits and conditional anti-windup. Selection frozen at604302e9eecc491b8855a6ccbcaf4e195cb2adb2; selection SHA256076604e732e1f97d02195c6d3798f0fba1998f4e9605c9492480cf51f794da36.

At each completed1s observation aggregate, update the existing policy for the subsequent1s commands; precompute legal20ms ramps only for that already-chosen held command. Never recreate/reset the policy at32s or the loss boundary. Evaluator sets gain1 or.6 before the exact second's neural advance; Policy receives no gain, future observation or hidden state. At relative64s the terminal update is recorded but not delivered. Net/policy/queue/clock/cursor reset occurs only between independent branches, with checkpoint restoration verified. No new plasticity, model fitting, online adaptation or additional excitation.

## Primary decision rules

For each network average BOTH noise repeats first. Principal replication unit=network, n=10. No bins/repeats treated as independent networks.

A LOSS network qualifies jointly if:
- Both calibrations valid; baseline in[1,30]Hz;1Hz offset>=2*RMS original baseline1s SD across repeats.
- Mean late LOSS MAX observed rate−actual target >=**0.2Hz** during48–64s. This is a finite-reference margin, chosen as a practical guard against merely touching the target; not a biological threshold or mathematical reachable set. This new rule is not an alteration of old authority gates.
- |mean signed PI bias|<=**0.2Hz** for48–64s AND separately for BOTH48–56s and56–64s.
- Mean1s absolute PI error<=**0.35Hz** over48–64s and separately BOTH8s windows. Raw counts only; no filtered/smoothed output used to qualify.
- No scientific-base fallback, missing bin, invalid receipt or constraint violation.

Scientific extended-recovery PASS requires >=**8/10** qualifying LOSS networks AND the two-sided95% network-bootstrap CI for cohort mean48–64s signed PI bias lies entirely in[-.2,.2]Hz. This is a pragmatic finite-cohort interval guard, not a formal asymptotic equivalence theorem. Multiple disjoint8s means plus MAE limits require sustained sampled tracking, not a single crossing or a filtered artifact.

Stationary guardrail: >=8/10 networks satisfy the same calibration/noise and PI bias/MAE/persistence criteria under STATIC (LOSS MAX margin is a separate LOSS feasibility condition, not a STATIC outcome). Cohort STATIC late bias CI must also be within[-.2,.2]. Full scientific M005A.7 PASS requires BOTH LOSS qualification and stationary guardrail. Original M005A.5 criteria/outcome remain separate. No requirement that PI beat FIXED is imposed: the question is sustained recovery, while competitive FIXED comparisons and harm must be disclosed.

All numerical validity/source/replay/timing and complete-cohort/resource checks are mandatory for execution PASS. Incomplete acquisition=PARTIAL, invalid causal instrument=FAIL. Completed negative scientific finding can coexist with execution PASS. No favorable early stop or exclusion. Failed calibration keeps targetb+1, original safe fallback and labeled scientific failure; not an exclusion.

## Secondary endpoints, uncertainty and descriptors

Record raw1s signed error y−target, MAE and bias in[8,16),[16,20),[20,32),[32,48),[48,56),[56,64),[48,64),[0,64). Trailing8s bias/MAE at each integer endpoint>=8; post-loss windows entirely after loss start only at24s. Include individual-sector rates as descriptive observations, not sector targets. Archive all20ms counts/events/filter/timestamps/receipts, desired/projected/delivered currents, every1s decision, integral and flags, terminal state, current/current²/exposure/model charge including calibration, bound occupancy and fallback/constraint status. MAX late target margin for each repeat and network. Compare STATIC/LOSS within policy and PI/FIXED under matched noise. No true-gain correction to FIXED or PI.

Recovery descriptor1: first three consecutive completed1s absolute errors<=.35Hz after loss; first endpoint and causal confirmation2s later; censor if absent by64s. Descriptive, not acceptance. Descriptor2: earliest completed16s post-loss window whose BOTH8s subwindows satisfy bias/MAE limits and whose EVERY later16s trailing window through64s also does. Report endpoint−16s as post-loss settling delay, right-censored at48s. This is retrospective persistence within the observed horizon, not online detection or asymptotic settling. Count crossings separately; never infer convergence from them.

Use10000paired network bootstrap draws, PCG64seed20261025, average repeats inside each network first;95%percentile intervals. Report per-network/per-repeat outcomes and component counts, PI-vs-FIXED MAE/bias/cost differences, pre/post bias change, residual negative bias, terminal integral and current saturation. Pointwise curve intervals are descriptive/non-simultaneous. No post hoc window changes or p-value feature selection. No multiplicity claim beyond frozen primary/guardrail conjunction. Two repeats and previously studied development identities limit generalization.

## Execution and resource budget

Preflight: one suspend-inclusive1200s stage including historical hashes, native clock/domain checks, full regression suite and new extended-step/continuity/boundary/gate tests. No scientific acquisition until it passes and source/protocol are committed. At most3scientific CPU workers; **single6600s acquisition deadline** from capture entry includes child imports, prefixes, all100branches, publication/collection. Prior measured17trial continuation:5219simulatedseconds/3125.495s actual suspend-inclusive (including one natural sleep). Simple planning ratio7420/5219*3125.495≈4444s, NOT a new benchmark;6600s affords bounded variability without unlimited execution. No deadline reset/extension. Worker RSS<2GiB, sampled every<=5s plus recorded trial high-water; aggregate memory not certified. New mission evidence<=150MiB and all M005A experiment/evidence/run allocation<=500MiB. Exceedance/fault stops all work, retains outputs, no replacements/retry.

Qualified boot-scoped Mach continuous deadline, native API consistency and inherited end/domain in all workers. Idle-sleep inhibitor during acquisition; never deliberately automate physical sleep. M005A.5 natural clamshell event supports observed accounting, not a controlled sleep-at-expiry experiment. During sleep user-space cannot signal; resumed code checks ORIGINAL deadline, stops if expired, never treats cleanup-only allowance as extra experiment time. .2s cooperative/.2sTERM/.4s final cleanup reserved inside deadline; at most.8s labeled cleanup-only after expiry on resume. Outer6605s watchdog cleanup-only; never permits scientific success beyond6600s. Clock inconsistency, boot mismatch, worker fault, nonfinite activity or invalid timing/receipt aborts/partial. Expected continuous-minus-uptime offset growth during sleep is not itself a clock inconsistency. Calendar clock remains diagnostic, not a fallback deadline. No reliance on responsive physical wake for qualification: expiration/noncompletion remains failure.

Atomic per-branch saves; after each16s scientific progress save a distinct incremental checkpoint artifact of the latest16s completed public bins/controller state, without changing simulation/policy state. Killed in-memory progress since last flush may be lost; no partial branch becomes complete or is resumed. All failed attempts retained. One prospective1200s post-acquisition analysis/verification stage including full numerical reconstruction, new gates, exactly one83s prefix+first32s technical replay of n0/r45 LOSS_PI against its extended prefix and first32s (not a new statistical replicate), causality fixtures, final full regressions and deterministic figure checks. Scientific horizon itself never extended beyond64s. Report/archive publication can inherit the same stage deadline, never reset it.

## Verification and stop

Tests cover synthetic extended stepping and exact32+32 versus64 continuity with unchanged policy, no boundary reset at16/32s, legal action timing and constraints, future-data causality, aggregation and independent gate cases (transient crossing must fail, persistent good data pass, missing repeat reject). Historical tests unchanged. Independent verifier reconstructs counts from events, original calibration/target/PI scalar recurrence, every receipt/current/slew, all timestamps, source/seed/OU hashes/checkpoints, matched pre-loss equality, model/controller-private boundary, all network bootstrap/gates and fallback invalidity. Publish machine data/figures/seed/config/source/resource manifests.

Stop after M005A.7. Success applies only to the new horizon/conditions. M005B remains HOLD and is not automatically authorized. Failure motivates a separately justified control-architecture or scientific-objective decision, not neural tuning, weaker targets or altered historical thresholds. No MPC/RLS control/RL/plasticity/hardware/locked tests.
