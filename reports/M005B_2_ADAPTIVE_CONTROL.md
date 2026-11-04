# M005B.2 — adaptive-control scientific evaluation: readiness stop

**Readiness HOLD. Scientific experiment execution PARTIAL (not started); scientific qualification NOT EVALUATED. M006 HOLD.** No development, secondary-fault, validation or locked-network scientific trajectory was acquired. No scientific endpoint or confidence interval was calculated. The mandatory readiness stop was respected; this is not evidence for or against adaptive-control superiority.

## Revisions and preservation

Starting clean revision **`901fa5b71784b18bfedabca052420b86cb51460a`**, branch `research/m005b-1-controller-implementation`. Created `research/m005b-2-scientific-evaluation`. Readiness scope, prospective cohort/seed manifest and audit source were committed at **`3735967`** before the attempted preflight. Final revision is the commit containing this report, supplied exactly in the mission response. No merge or tag.

All **16,398 starting tracked files** remain hash-identical. All **1,389 M005B.1 artifact hashes** also match. Frozen [protocol011](../docs/research/011_M005B_CONTROL_PROTOCOL.md), controllers, original PI, neural model, observation/stimulation contracts and supervisor/clock source are byte-identical to the verified starting revision. No target, hypothesis, comparator, gain, lag, objective weight, cohort, statistical gate, resource limit or historical scientific decision changed. M005B.1 engineering PASS, M005A.7 finite-horizon PI PASS and historical M005A.5 FAIL remain unchanged.

## Audited evidence and readiness decision

Read protocol011, M005B.0 design, M005B.1 implementation/report/verification, relevant M004 and M005A.7 results, predictive/PI/substrate/supervisor/clock source and controller tests. Prior M004 improved predictive accuracy under prescribed probing but did not establish adaptive-control benefit. M005A.7 qualified slow PI recovery, not rapid recovery or adaptive superiority. These findings were not substituted for new M005B outcomes.

| Mandatory readiness item | Actual result |
|---|---|
| Expected revision/branch/clean start | Verified before creating review branch. |
| M005B.1 engineering evidence | Historical PASS records, final-source replay and source/artifact hashes verified unchanged. |
| Frozen controller correspondence | Same raw-label FIR initialization, C02 allocation,625-bank/two-second planner, RLS rho=.999 and PI10/5; no redesign. |
| Prospective cohort/action/noise identities | Saved exactly; zero acquisition. No random action draws: prefix and finite bank are deterministic. |
| Endpoint/analysis frozen | Protocol hash unchanged; no selection permitted. No new outcome inspected. |
| Clock/supervisor |1,000 native continuous-clock samples passed; same boot domain and unchanged qualified supervisor source loaded using an isolated stdlib-only audit namespace. No fresh failure-injection suite was executed. |
| Independent action feasibility | Stdlib scalar reconstruction checked625 candidates at priors0,37.3,120 pA:187,500 admissible transitions. Actual NumPy planner could not be freshly executed. Prior exact-projector tests remain hash-verified. |
| Resource feasibility | **HOLD:** conservative role-weighted development forecast11,278.107 s exceeds frozen10,800 s cap. |
| Fresh runtime/regressions | **BLOCKED:** prior temporary Python environment lacks NumPy, Brian2, pytest and the installed package; preflight import failed before tests/worker startup. |

Either unresolved mandatory item prevents scientific acquisition. Previous173-test success is preserved evidence, **not a fresh test run in this mission**. No gates were weakened to proceed.

## Resource mismatch — evidence and calculation

The M005B.0 planning ratio came from M005A.7:7,420 simulated seconds /2,187.636798 actual wall seconds across at most three workers, or .294829757 aggregate wall seconds per simulated second. That PI experiment advanced predeclared one-second command batches. M005B.1 qualified predictive controllers through per20ms `BrianEngine.advance`; each call runs Brian's scheduling machinery. Reusing the batched ratio for predictive execution while adding only planner latency omits this observed orchestration cost.

Archived M005B.1 smoke measurements, each two simulated control seconds, including its recorded computation/archival overhead:

| Qualified branch | Actual wall s | Wall s / simulated s |
|---|---:|---:|
| FIXED predictive |6.556544|3.278272|
| RLS predictive |5.993973|2.996986|
| BIAS predictive |3.909521|1.954761|
| RLS technical replay |4.070971|2.035486|

These are small, variable historical measurements, not standardized throughput benchmarks. The preliminary commentary's rough statement that each branch took about6.5 s was corrected after reading all four records. No new timing measurement on a reserved network/seed was made.

Role-weighted forecast, with **ideal three-worker scaling**:

- Development primary: each predictive kind has20 trials x2regimes x64 s =2,560 simulated seconds. Predictive estimate is2560*(3.278272+2.996986+1.954761)/3. Assign every primary nonpredictive branch and prefix the favorable old batched ratio:20*(51+7*64)*.294829757. Total **9,965.350 s**.
- Required secondary faults:3 trials x4 RLS branches x64 s =768 RLS seconds and768 PI seconds, plus153 prefix seconds. Use actual original RLS timing and, optimistically, the **fastest observed per-tick branch as an unmeasured PI proxy**. Estimate768*(2.996986+1.954761)/3 +153*.294829757 = **1,312.756 s**.
- Development including mandatory secondary faults: **11,278.107 s** versus **10,800 s**, excess **478.107 s /4.43%**. No additional allowance for unprofiled snapshot/reconciliation work is added.
- Conditional validation:10 trials with the same primary branch bank: **4,982.675 s**, below its5,400 s cap. Validation is nevertheless closed because development readiness failed. The initial rough suggestion that both caps would fail was superseded by this role-weighted calculation.

Protocol011 explicitly requires HOLD before acquisition if the feasibility projection exceeds the cap. It does not permit dropping secondary faults, selecting only a favorable timing observation, silently rewriting the interaction path or enlarging the budget after the fact.

Sensitivity matters: substituting the faster RLS technical replay for the original RLS timing gives a development estimate **10,211.482 s**, below the cap. Thus the analysis does **not prove that completion within budget is impossible**. It establishes an unresolved, materially variable readiness forecast: the conservative original-role projection fails, and a favorable sensitivity case is not verified end-to-end throughput. The alternative requires prospective engineering profiling/qualification rather than selecting the convenient estimate to authorize reserved acquisition. Controller/planner code, batching semantics and evidence encoding were not changed here.

[Resource forecast figure](evidence/m005b_2/resource_forecast.svg). It shows scheduling estimates only, not scientific outcomes, biological effects or confidence intervals. Exact arithmetic/inputs are retained in resource_projection.json and CSV. The independent stdlib audit separately recomputed these quantities from archived timing records and the frozen cohort counts.

## Fresh preflight environment failure

Attempted command:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  MPLCONFIGDIR=/tmp/neuromancer-m005b2-mpl /usr/bin/time -l \
  /tmp/neuromancer-m004-venv/bin/python reports/evidence/m005b_2/preflight.py
```

Actual result: exit1, **`ModuleNotFoundError: No module named 'neuromancer'`**, .05 s reported wall time. Metadata inspection confirms NumPy/Brian2/pytest/neuromancer all unavailable to this interpreter. `/tmp/neuromancer-m004-venv/pyvenv.cfg` is absent; its Python link resolves to Homebrew Python3.12.15 and reports the base prefix. A site-packages directory exists, but the qualified stack is not importable. The cause of environment loss is unknown; deletion or corruption is not inferred beyond these observations.

The failure occurred before creation of the1,200 s preflight deadline and before spawning any supervisor worker. No complete regression run, study clock budget, acquisition deadline, trial or partial neural branch was started. No budget expired or was extended. Both original launch.log and preflight_import_failure.log are preserved. No installation/download or environment repair was attempted after the mandatory stop.

A subsequent **read-only stdlib audit** loaded the unchanged clock/supervisor modules under an isolated audit namespace to avoid package initialization requiring NumPy. It sampled native clocks, verified file hashes, checked scalar constraints and recomputed scheduling arithmetic in about3.03 s under its own60 s report-audit bound. This was **not a restarted preflight or scientific budget**, did not start experimental workers and did not make the science stack usable. No new cleanup failure or orphaned experiment worker exists because none was launched.

## Cohorts, comparison and outcome completeness

Exact planned identities are preserved in prospective_manifest.json and cohort_status.csv, all labeled `NOT_ACQUIRED_READINESS_HOLD`:

| Stage | Frozen identities | Planned branches | Actually acquired |
|---|---|---|---:|
| Development | Networks0–9, noise47/48;20 trials | STATIC/LOSS x PI10_5,FIXED-MPC,RLS-MPC,BIAS-MPC,FIXED,ZERO, plus LOSS MAX;13 per trial |0|
| Secondary faults | Networks0–2, noise49;3 trials | PI/RLS x STATIC/LOSS x DELAY/DROP;8 per trial |0|
| Validation | Networks10–14, noise49/50;10 trials | Same13-branch primary bank, conditional on development gates |0|
| Locked | Networks100–119 | No access authorized |0|

Root seed20261018 and existing SeedSequence role definitions preserved: parameter roles0–3 use replicate0; OUrole4 uses network/noise identity and absolute-second block. Action schedules are deterministic; no new random action seed/draw or replacement seed was introduced. Manifest identities are **plans, not evidence of instantiated networks**. There was no controller selection or freeze based on scientific outcomes; all settings were already fixed. No validation was opened to resolve development uncertainty.

| Scientific quantity | Actual M005B.2 result |
|---|---|
| H1a post-loss IAE versus PI:>=10%,>=1.2 Hz*s, positiveCI and network count |NOT EVALUATED|
| H1b versus fixed predictive:>=5%,>=.6 Hz*s, positiveCI and network count |NOT EVALUATED|
| H2 recovery-delay benefit |NOT EVALUATED|
| H3 final bias/MAE, feasibility and MAX headroom |NOT EVALUATED|
| H4 stimulation cost |NOT EVALUATED|
| H5 stationary/pre-change guards |NOT EVALUATED|
| Absolute/relative improvements, confidence intervals, favorable-network counts |NOT ESTIMABLE: zero acquired networks|
| Prediction error, adaptation, excitation, saturation, tracking errors |NOT MEASURED|
| Scientific planner deadlines, fallback/abort/update events |NOT MEASURED; no scientific controller execution|

No numeric zeros are substituted for missing scientific errors/benefits. ZERO/FIXED/PI/BIAS/shuffled/weak-excitation and fault comparisons were not run. No claim that RLS improves prediction but fails control, or that PI/fixed control wins, is justified by this readiness stop. No model/actuator/controller-design failure mechanism can be inferred from absent scientific trajectories.

## Verification actually executed and limitations

- Verified exact starting revision/branch and clean start; new review branch created.
- Compared frozen protocol and relevant executable files directly against starting Git objects; all remain byte-identical.
- Rehashed16,398 starting files and1,389 M005B.1 artifact entries successfully. Prior173-test/final replay records remain intact.
- Fresh full regression attempt could not start. **Zero new pytest tests passed or failed; the launcher import failed.** No new JUnit or scientific raw dataset is fabricated. Historical software fixtures were not rerun.
- Independently checked625 scalar action schedules at three legal prior currents,187,500 transitions, including exact inward floating-point slew endpoints. This establishes analytic C02 feasibility for the reconstruction, **not a fresh execution of the NumPy planner**.
- Native1,000-sample suspend-inclusive clock consistency and unchanged supervisor module loading passed. Fresh process-tree failure-injection tests did not run; prior qualification is preserved, not relabeled current-stack qualification.
- Independently recomputed resource arithmetic and all planned cohort/seed counts. No actual neural throughput benchmark or statistical uncertainty estimate is claimed from this forecast.

There was no scientific resource monitor, hence no new polling-cadence measurement or deadline-miss rate. The initial import attempt used16,416,768 bytes maximum RSS as reported by time; this is not a neural-worker memory benchmark. Prior monitoring deviations/physical-sleep limitations remain disclosed in their original reports. No inference about actual BLAS threading is made. Raw/curated scientific trajectories, scientific figures and numerical model outcomes are absent because acquisition never began; readiness source, logs, manifests, arithmetic and the clearly labeled forecast SVG are retained instead.

## Decisions and minimal prospective continuation

**Readiness HOLD; scientific execution PARTIAL / NOT STARTED; scientific PASS/FAIL unassessable. M006 HOLD.** The audit itself completed, but the requested controller study did not. This is an enforced prerequisite stop, not an adaptive-control negative result and not a retroactive revision of M005B.1.

Smallest defensible next action is a separately authorized engineering readiness repair, not M006:

1. Recreate the exact pinned Python3.12/Brian2 2.10.1/NumPy2.5.4/pytest9.1.1 stack from the repository; verify installation/import/source identity and rerun all173 tests and required readiness checks.
2. Prospectively profile the qualified per-tick neural/control/recording path on a nonreserved engineering fixture, separating Brian scheduling, model/planner computation and artifact overhead. Demonstrate an adequately supported resource forecast for **all** development primary plus secondary conditions under10,800 s and validation under5,400 s.
3. Any outcome-preserving batching or storage change must first be independently qualified for exact delivered actions, causal updates, per-tick fault interruption, replay and memory/source provenance. It cannot be silently introduced inside this scientific mission. Keep controller/model/target/scientific gates fixed.
4. If the fixed caps remain unsupported, propose a separately versioned prospective resource amendment for explicit authorization, preserving this readiness failure. No new cap is enacted here.
5. Only after readiness passes, freeze the acquisition source and resume M005B.2 on the original unopened47/48 and49/50 identities. Apply the original development-to-validation gate. Do not select replacement seeds or open the locked cohort.

No next experiment, dependency repair, controller retuning, neural change, merge, release or M006 work was performed.
