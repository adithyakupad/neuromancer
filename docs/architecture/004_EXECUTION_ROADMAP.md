# Mission 001 — Execution roadmap and architecture review

Date2026-10-18. **Stop after this design mission. M1 is a next coding brief, not work performed here.** The two-week sprint is conditional on M1–M3 instrument gates. Calendar allocation is a planning budget, not measured execution performance.

## Milestones and dependencies

| Milestone | Small deliverable | PASS gate | FAIL response / dependency |
|---|---|---|---|
| M1 (days1–2) | Minimal Brian substrate and exact timing/observation/stimulation records; one fresh trial/process; no controllers | Single-cell analytical decay/refractory, E/I sign, 20 ms step/bin endpoints, exact receipt, validation atomicity, delay-queue chunk equivalence, same-seed replay and independent-trial isolation all pass | Stop/fix neural/time boundary; do not move to controller stack |
| M2 (days3–4), after M1 | Frozen 1000-cell family, randomized calibration, paired sham response and resource probe | All development networks reported; >=8/10 physiology-like activity/authority criteria and3-seed dt convergence pass; measured60 s run fits budget; saved complete prefix replay | Parameters may be amended on train only, with protocol version increment. No favorable test-seed selection. |
| M3 (days5–6), after M2 | Causal rate/lag estimator, ridge ARX, known-linear fixture and reserved evoked-response evaluation | Known model recovered within numerical fixture tolerance; no-input/shuffle/zero-M/replay controls pass; held-out intervention response MSE benefit>=10% | Diagnose excitation/model/observation insufficiency. May publish identification failure; no adaptive claim. |
| M4 (days7–8), after M3 | Zero/constant/periodic/PI/fixed MPC plus tested solver/fallback paths | Shared constraints, correct anti-windup and causal availability; no privileged-state imports; development loop completes; record all tuning | If PI works and MPC fails, retain failure; no RL substitution |
| M5 (days9–10), after M4 | RLS adaptive MPC, equal-budget tuning, stationary/gain-direction controls; freeze test manifest | Same initial models, no extra adaptive exploration, numerical covariance tests, fixed-versus-update ablation; all configs/hyperparameters/primary comparator frozen | Do not inspect test; revise numerical design only on development |
| M6 (days11–13), after M5 | Execute locked held-out cohort and network-level analysis | Complete provenance and full cohort, exact protocol gates applied, all primary outcomes including failures reported | Failed H1 is a negative scientific result, failed instrument is HOLD. Insufficient precision is inconclusive. |
| M7 (day14), after M6 | Research report with matched plots, uncertainty, simpler explanations and reproduce command | Independent replay of a selected saved trial, metric fixture checks and report/source consistency | Preserve prior report; append corrections, no cherry-picking |
| M8 (later), after V0 review | NEST independent implementation on qualified Linux environment | Same linear/single-cell/event/channel tests, comparable rate/response distributions across engines with justified tolerance | Numerical implementation comparison only; do not force spike-for-spike equality across algorithms |
| M9 (later), after license and V0 need | BL-1 qualification or official SDK custom-source adapter, separately scoped | BL-1 complete state continuation + licensing/calibration resolved; SDK callback clock/queue/sample/HDF5 conformance measured | Remain prior art/interface plan if unresolved |
| M10 (separate research approval) | Offline biological response-identification protocol; later approved living-preparation study | Authentic dataset/acquisition/units/artifact/stim metadata, preparation-level splits; online access/protocol qualification | Never relabel simulated or replay evidence as prospective biology |

Do not implement M8–M10 merely to claim extensibility. They answer different risks. Q1 coverage sweeps and Q3 plasticity are later protocols. No UI, remote scheduler, cloud job, deep model training or platform rewrite belongs to this roadmap's V0.

## First implementation milestone — precise coding brief

Implement M1 only after a new implementation instruction. Preserve Mission001 and existing .venv. Add Python3.12 package metadata with Brian2 2.10.1 and NumPy core, pytest dev; exact environment lock/resolution saved. Use existing src/neuromancer and tests paths. Create the minimal contracts and Brian backend from system design, without an abstract base-class hierarchy, registry or optional engine dependencies.

Input is one explicitly validated config matching V0 constants plus stream manifest. Output is a20 ms step with partial spike events/counts/masks, integer-microsecond boundaries and actual stimulation receipt. Neural state and diagnostic state must not be in the controller-facing result. Use explicit Brian Network/Clock, fixed disjoint channels and held-current delivery; scheduled synaptic delays persist between steps. External noise must be indexed by simulation time and neuron independently of spikes/actions. Do not build ARX, MPC, RLS, game environments, hardware waveform adapters or full experiment sweeps in M1.

Tests: analytical no-input membrane decay; threshold/reset/refractory; positive E/negative I synapse; pulse causes a causal *post-onset* response with paired same-state zero-current comparator; [start,stop) event count fixture; invalid command leaves state/time unchanged; same-seed replay; two-chunk equals continuous including a synaptic event pending across boundary; separate trial/process cannot mutate another's state/clock or RNG. Test current limits/total/slew and explicit pA-vs-µA boundary. All assertions must fail for a deliberately shifted input/event boundary fixture. Use numerical tolerance for analytical decay, exact arrays for same-environment replay and count/clock semantics.

Deliver one small runnable single-trial command producing metadata, receipts and numerical observations in an exclusive new run directory, plus test output and measured initialization/step time for200 and1000 cells. No scientific efficacy claim. M1 PASS is software contract qualification; M2 supplies network feasibility. Stop and report before proceeding if timing/state ownership or pulse causality fails.

## Architecture review acceptance matrix

| Question | Review finding | Evidence or remaining gate |
|---|---|---|
| Rebuilding existing functionality? | No own neural integrator, SDK clone or monitor framework | Brian functions reused; optional SDK data-source contract verified |
| Every abstraction demonstrated? | Three trial operations, data records and observation firewall needed for V0 | No universal waveform/snapshot/backend plugin API |
| Causal stimulation? | Brian bounded probe demonstrates activity change; BL-1 current path exists; SDK random/replay do not respond | Full E/I indirect-response gate M2 still unexecuted |
| Private state protected? | Separate controller observations from evaluator truth by contract | Enforce imports/object references and test at M1/M4 |
| Target controllable? | Not established; positive-only input, fixed budget and indirect neurons can fail | M2 authority probe and all-network reporting |
| Intervention identifiable? | Randomized calibration and held-out sham probes distinguish prediction from intervention effect | M3 rank/response/no-input/shuffle checks |
| Benchmark favors adaptation? | Gain-loss condition favors its premise; stationary, PI, increased gain and cost guardrails counter selection | Still limited to this simulator family; no broad superiority claim |
| Instances independent? | One process/trial, reproducible prefix, action-independent innovations specified | Delay/stream/checkpoint tests required; API probe alone incomplete |
| Plasticity supported? | V0 none; gain drift explicitly external parameter | Q3 requires actual STDP and retention/ablation controls |
| Useful if adaptive fails? | Yes: PI sufficiency, model mismatch, authority and observability limits | Retain negatives and distinguish instrument failure |
| Strongest simpler explanation? | More input, direct drive, integral compensation, target choice or tuning advantage | Disjoint cells, cost, PI, fixed model, frozen splits and nulls |
| Neuroscientist challenge? | Uncalibrated current mapping, random topology, no culture/MEA artifacts, time scales and neuron-selection simplifications | Explicit simulation-only scope, later authentic-data validation |

## Completion, verification and open risks

Mission001 produces an implementation-ready *conditional* design, not a validated research result. Core recommendation supported by pinned source and a local causal/timing probe. Highest risks: (1) feasible indirect positive-input control under drift; (2) identification versus autocorrelation; (3) matched-noise/state continuation; (4) PI eliminating the proposed novelty; (5) neural/MEA physiological mismatch; (6) license and SDK scheduling constraints. Full ranked review is in ADR001.

Executed: repository/environment/context inspections, eight candidate source/package/license audits with explicit depth differences, primary-source research, source-version inventory, temporary Brian install and small causal/replay/chunk probes. Source tests were read; **upstream suites were not run**. No BL-1 physiological calibration, CPU scaling sweep, NEST install, full V0 simulation, controller benchmark, biological-data experiment, hardware/cloud access or ethics clearance claimed.

Documentation acceptance requires resolving internal specification contradictions and verifying local links/evidence references; scientific acceptance requires future instrument gates. Mission report must retain that distinction. Starting/final HEAD remains `011c3ce1a71960544032717e91076730416c19fd`; final intended changes are only the six design files plus audit evidence, uncommitted. Exact final working-tree inventory is recorded in evidence/repository_state.txt after verification. No M1 runtime package or controller was created.
