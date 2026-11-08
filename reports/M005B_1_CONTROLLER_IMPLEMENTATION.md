# M005B.1 — adaptive predictive controller engineering qualification

**Engineering PASS. Controller readiness PASS for the qualified public-data/virtual-time contract. Scientific acquisition NOT STARTED; no adaptive-superiority claim.** A separately authorized acquisition milestone must freeze its complete runner/source and pass the original scientific acquisition preflight. No merge or automatic M005B study. Historical M005A.5 FAIL and M005A.7 finite-horizon PASS remain unchanged.

## Revisions, preservation and protocol

Starting clean `299dbc9dcfe5b5e73204362701afda72dfca6fa1`, branch `research/m005b-0-control-design`. Review branch `research/m005b-1-controller-implementation`. Authoritative [protocol011](../docs/research/011_M005B_CONTROL_PROTOCOL.md) remains byte-identical. Prospective engineering clarification `1d20678` was committed before qualification: receipt ownership, four-bin rearm, planning-release deadline, single-trial models, smoke scope and one 1,800 s continuous budget. No hypothesis, endpoint, comparator, target, cohort, stimulation bound, cost or statistical gate changed. Final revision is the commit containing this report, supplied exactly in the mission response.

All **15,004** starting tracked files remain hash-identical, including historical source, protocols, PI gains/behavior, neural trajectories, model coefficients, failures and supervisor evidence. Only new modules/tests/evidence were added. Preservation, source and full artifact manifests are retained under evidence/m005b_1.

Implementation/smoke freeze: **`6a5ca6b08d31c2e818716d48f9fc0afc84b119ac`**. Post-smoke validation review hardened receipt status/integer-time/request rejection at `90d5037`; valid-input numerical algorithms did not change. Both source versions, original169-test run, four added guard tests and final173-test run are preserved. No neural fixture was repeated or replaced: final-source controllers replayed every saved valid smoke input and reproduced all400 actions/model states exactly. This is final-source public-record replay, not a fresh neural smoke run. See ENGINEERING_REVIEW_001.md.

## Implemented interfaces and numerical correspondence

| New component | Contract |
|---|---|
| `predictive.initialize(observations, receipts)` | Exactly2,550 original-prefix bins; verifies times/trial/channel validity/actual calibration schedule; uses raw sector counts and original control.calibrate. |
| `Initialization` | Own record, information inverse, nine actual delivered rows, unchanged calibration, trial identity. Controller construction copies mutable model/history. |
| `FIRModel` | FIXED/RLS/BIAS policies; fixed normalization/output center; transactional RLS and information checks; explicit received/update/skip/failure counters. |
| `predictive_planner.plan` | All625 finite-bank plans; two-second FIR prediction; exact feasible C02 ramps; frozen objective/ties; native250 ms deadline. |
| `PredictiveController.command(now_us)` | Commands only at current public clock, one pending command; replan at integer seconds; forecast before corresponding outcome; validate/projection before release. |
| `accept(observation, receipt, now_us)` | Validate matching delivery first, update only completed available observations, keep actual history even on observation dropout. |
| `PIReference` / `public_step` | Thin receipt/command adapter around original Policy; no PI numerical/gain change and no neural/private state in controller. |

FIR: raw four-sector Hz from20 excitatory cells/sector; x=[u_k,...,u_(k−9)] in pA, 164 coefficients and41x41 covariance. Fit bins800..2349 ([16,47)s), lambda=.1, unpenalized intercept, mean/SD normalization floored1 pA. Model initialization ends before control51s; no filtered-rate labels, future observations or sham labels. C02-only reduced rank11 required; full four-channel identifiability is not asserted. Initial fixed/adaptive models are identical.

RLS rho=.999, K=Pz/(rho+zTPz), Theta+=K[(y−ybar)−zTTheta], P+=(P−KzTP)/rho with symmetrization. Initial ridge information is discounted. First/every50th received-bin information checks, finite forecast cap100 Hz and transaction-before-commit follow the protocol. FIXED never changes coefficients. BIAS freezes input coefficients and updates only intercepts; it is the required mechanism diagnostic, not a new primary comparator.

All predictive arms share exactly the625 pairs q0,q1 in{0,5,...,120} pA, two1s holds, H=100 twenty-ms bins. Original projector/legal ramps enforce C02,120 pA/channel,240 pA total and30 pA/channel/tick. Objective and tie break are exactly protocol011: two squared1s rate errors, .02 normalized delivered-current integral and .01 requested-hold switching penalty; lower exposure then q0/q1 breaks ties within1e−12. Apply only the first second and replan; no hypothetical outcome is assimilated.

Neural integration100us, observations/actuation20ms, normal decisions1s, horizon2s and suspend-inclusive wall deadline are distinct clocks. No true gain, voltages, connectivity or evaluator-only outcomes are controller arguments. Public input consists of permitted spike records, receipt-confirmed delivered currents, unchanged target and prior internal state. No Brian engine is imported or accessed by controller/model/planner modules.

## Failure and safety contract

Invalid/late/missing observations skip updates, safe-ramp on the next tick, preserve actual delivered history and use four fresh bins only to rearm. Updates reopen on the fifth fresh bin; planning resumes at the next fixed integer second. Stale observations are never inserted retroactively. Numerical/planner failure latches safe zero-ramp for the remaining episode; it does not substitute PI or a new model. Unknown/malformed delivery is fatal before changing public clock/history because actuator state cannot safely be invented. Failed original calibration produces safe zero.

The250 ms deadline includes schedule/feature/forecast/cost computation, validation and first action release. The last valid model survives a rejected update. A valid actuator state always has feasible C02 ramp candidates; an empty mathematical feasible set is not expected under these constraints. Malformed history and invalid candidate forecasts reject the whole decision, rather than selecting a favorable subset. Current safety does not prove neural stability or successful tracking.

## Executed tests and retained expected failures

- Initial full run: **169 passed**,25 existing warnings,46.24s. Final full run: **173 passed**,25 existing warnings,37.96s. All157 historical tests unchanged;16 new cases include parameterized faults.
- Known linear initialization and multistep FIR; all625 candidates versus the exact historical projector at fractional prior37.3pA; independent normalized/raw equations and stable estimation.
- RLS and intercept-only updates versus discounted batch equations; synthetic gain-loss learning under informative inputs; FIXED coefficient immutability and copied initialization/trial isolation.
- Missing/late/invalid-mask/negative-count observations, rearm/update order, future availability rejection and no clock rewind; duplicate commands/receipts; malformed delivery metadata; failed calibration.
- Negative information and invalid forecasts retain prior parameters and latch zero; injected planner timeout discards the action.
- Machine-readable failure_fixtures.json retains all requested/delivered commands, event states, skips, latch causes and rearm for seven injections. Expected failures do not count as base-case failures.
- Weak zero-input data are exactly identical under two different actuator gains and have online design rank1: kernel identification is not possible. A wrong-sign synthetic actuator with nonnegative current cannot reach the specified synthetic target; this negative analytical fixture is preserved, not tuned away.

Synthetic data and known-plant results are engineering fixtures, not neural adaptive-control endpoints. No PI superiority, M005B IAE gate, recovery/bias gate or reserved scientific outcome was calculated.

## Actual Brian2 integration smoke

Preregistered network0/noise60/root20261018, original Brian2 model and51s calibration, then three independent2s FIXED/RLS/BIAS branches from the exact checkpoint; an additional exact2s RLS replay. **59 total simulated seconds**, one neural fixture. Noise60 is outside development47/48, confirmation49/50 and secondary-fault49. No efficacy change or64s scientific run.

Actual smoke wall time **60.925192s**; worker peakRSS **1,096,941,568 bytes**, below2GiB. All branches completed100bins/two plans. RLS/BIAS each used100completed observations; FIXED used the identical stream without coefficient changes. Zero base-case skips, model/planner failures, fallbacks or constraint violations. RLS replay exactly matched all non-timing arrays, coefficients/information and OU block hashes. No clock/resource/cleanup failure.

Every smoke branch delivered199.2 pA*s nominal summed-channel exposure, including its initial ramp (replay is technical repetition, not an independent subject). The common51s calibration exposure is saved separately in prefix.npz and must be included in any future study total. Identical short-smoke actions do not imply model equivalence or control efficacy; no outcome tracking comparison was made.

## Independent numerical verification

Independent raw-unit reconstruction passed **400 model states**, **5,000 candidate scores**, **2,000,000 sector-bin forecasts**, all raw counts from events, feature/receipt alignment, current limits, exact exposure, selected finite-bank minima and state transitions. RLS covariance/coefficients were independently solved from discounted normal equations, not the inverse-update implementation. Both BIAS and FIXED were independently reconstructed. Initial raw-label coefficients and normalization were recomputed from saved prefix counts. A post-run static reconstruction verifies n0 parameter hashes against historical n0, disjoint channel membership and representative actual OU block hashes0/50/51/52. This is labeled derived evidence, not an unrecorded runtime parameter snapshot. Per-kind latency reduction reproduces the archived JSON exactly; pip check passes.

The unchanged PI plus its new public per-tick adapter reproduced **all3,200 actions,64 decision states and terminal state** from preserved n0/r45 M005A.7 data. No new64s neural PI trajectory or scientific reanalysis was performed. Final-source public replay reproduced all400 smoke commands and model states, and future-output mutation left21pre-mutation commands/states unchanged. This is in-session independent numerical implementation, not an external investigator or second simulator.

## Measured runtime — actual samples, not realtime guarantees

| Stream / operation | n | p50 ms | p95 ms | p99 ms | Max ms |
|---|---:|---:|---:|---:|---:|
| smoke / planner | 8 | 4.839021 | 5.531339 | 5.531701 | 5.531791 |
| smoke / update | 400 | 0.054104 | 0.119129 | 0.245429 | 26.651667 |
| smoke / complete_decision | 8 | 4.905083 | 5.741481 | 5.797563 | 5.811583 |
| smoke / command | 400 | 0.032938 | 0.119254 | 4.787128 | 5.611291 |
| synthetic / planner | 60 | 5.025292 | 8.646348 | 13.896147 | 18.788083 |
| synthetic / update | 3000 | 0.015459 | 0.047166 | 0.122387 | 12.217666 |
| synthetic / complete_decision | 60 | 5.115229 | 8.773148 | 14.208564 | 18.981000 |
| synthetic / command | 3000 | 0.019042 | 0.049296 | 5.063703 | 18.964959 |

Command includes per-tick validation and planning only on decision ticks; complete_decision is the preceding completed-observation update plus boundary command/planning time. First decision has no prior online update. Update includes controller validation/state handling, not neural simulation. p99 on eight smoke plans is a small-sample descriptive quantile. The60synthetic plans came from3,000 public synthetic ticks, three models, no neural acquisition.

| Smoke estimator | n updates | p50 ms | p95 ms | p99 ms | Max ms |
|---|---:|---:|---:|---:|---:|
| FIXED | 100 | 0.017688 | 0.060062 | 0.161791 | 0.215375 |
| RLS | 100 | 0.067312 | 0.219229 | 0.299445 | 0.331125 |
| BIAS | 100 | 0.039355 | 0.045585 | 0.061812 | 0.080333 |
| RLS_REPLAY | 100 | 0.061104 | 0.076641 | 0.476066 | 26.651667 |

There were **zero base-case250ms planning/release misses**. One observation-update call in the technical neural RLS replay took26.651667ms, exceeding20ms. That outlier was retained; it is not a planner deadline violation. Virtual simulation time and causal ordering remain correct, but hard20ms operating-system realtime is NOT qualified. Deliberate injected timeouts are separate visible failures, not erased from the evidence. Requested BLAS thread limits1; actual threading unverified.

Initial supervised tests+smoke+audit completed110.729238s under the original1,800s boot-scoped Mach continuous deadline. Final regressions, fault fixtures and publication inherited the SAME absolute deadline. /usr/bin/time -l recorded1,441,349,632bytes maximum resident set size for the initial supervised command tree; the smoke worker independently recorded its own high-water above. This is not a simultaneous aggregate-memory guarantee or a separate final-regression high-water measurement. Final publication checks evidence<100MiB and all process groups reaped. No deliberate physical sleep or claimed wake-time guarantee.

## Commands, source and evidence

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  MPLCONFIGDIR=/tmp/neuromancer-m005b1-mpl /usr/bin/time -l \
  /tmp/neuromancer-m004-venv/bin/python reports/evidence/m005b_1/run.py
# Child stages: pytest (169), smoke.py, verify.py
# Same inherited deadline: faults.py; pytest (173); final_replay.py; lineage.py; pip check; publish.py
```

Full supervisor argv/exit/timing/cleanup records and both JUnit runs are retained. Source, declared seed/config, OU/state provenance and a separately labeled post-run deterministic parameter reconstruction, raw prefix/spikes/observations/requests/deliveries, all400model snapshots, features/pre-update forecasts, all625candidate diagnostics at every smoke origin, errors/skips/fallbacks and deterministic replay are saved. Manifests include original and final source identity. Git commits retain both validation versions; no original stop/result was overwritten. No dependency, neural equation, inhibition, recording membership or PI parameter change.

## Decision, readiness and limitations

**Engineering PASS** for the frozen controller contract on the executed synthetic cases, short neural fixture and preserved public-record replays. Fixed and adaptive arms share initialization/model/planner/physical constraints; online updating is their primary difference. BIAS is also implemented for the preregistered mechanism check.

**Scientific acquisition remains unstarted.** Controller readiness passes the engineering gate; a separately authorized study must freeze the full acquisition runner, verify13-branch/cohort scheduling, resource forecasts, complete trial manifests and required original preflight before opening any M005B scientific trajectories. No development47/48 or confirmation49/50 study, locked100–119, gain-aware controller, adaptive MPC superiority claim, retuned PI, plasticity, RL or hardware integration was performed.

Remaining limits: only one two-second-per-arm neural fixture at stationary gain; synthetic gain adaptation is not neural compensation. Weak/closed-loop excitation and regressor endogeneity remain scientific risks. The selected short FIR may behave like a dose mapping; intercept-only gains need not identify actuator efficacy. All625-plan verification concerns the discrete bank, not continuous optimum or mathematical stability. Native-clock timing is descriptive and can suffer OS outliers; physical sleep/realtime hardware are unqualified. The final receipt guards were validated by public-record replay, not a second neural acquisition.

Next falsifiable experiment, if separately authorized: execute the unchanged M005B protocol development comparison, including competitive frozen PI, fixed predictive, open-loop, ZERO and BIAS controls, and test cumulative post-loss error plus cost/stationary/late-bias gates. Retain every failure and do not change targets or neural dynamics to produce success. Stop this mission after engineering review/commit.
