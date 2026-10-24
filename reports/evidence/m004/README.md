# M004 evidence, schema and reproduction

Simulation only. Protocol008 plus PREREGISTRATION_CLARIFICATION_001.md are authoritative. Starting1fe8f6bd0a1e057b8bbe10cd7d10d49e33c1a2d2; all2481 historical files preserved. Neural source and constraints unchanged. Selected adaptation/detector are in selection.json, committed before validation acquisition. No locked100–119, controller or biological experiment.

## Reproduction

Existing environment /tmp/neuromancer-m004-venv/bin/python, Python3.12. Recreate from unchanged requirements-m002.txt plus editable package if absent; the pre-existing .venv is Python3.14 and was not overwritten. Export VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/neuromancer-m004-mpl; actual BLAS threads unverified. Use new exclusive output directories. Source/config/environment/command vectors and measured stages accompany results.

    python -m neuromancer.online_experiment --stage D --output runs/m004-dev-01
    python reports/evidence/m004/replay.py --raw runs/m004-dev-01 --output runs/m004-dev-replay-01
    python reports/evidence/m004/select_models.py --raw runs/m004-dev-01 --replay runs/m004-dev-replay-01 --output selection-new.json

Inspect/commit the sealed selection before validation. Do not overwrite the preserved selection. Validation always runs under this preregistered schedule, even if development scientific gates fail:

    python -m neuromancer.online_experiment --stage V --selection selection-new.json --output runs/m004-validation-01
    python reports/evidence/m004/replay.py --raw runs/m004-validation-01 --output runs/m004-validation-replay-01

For analysis pass --dev, --dev-replay, --validation, --validation-replay, --selection, --output. verify_analysis.py takes the same inputs plus --analysis. verify.py audits each raw/replay pair using --raw --replay --output. figures.py takes --analysis. dev_stages.py/final_stages.py retain exact executed command vectors and900s stage caps; source uses these literal scratch paths. Curated results/{dev_raw,dev_replay,validation_raw,validation_replay,analysis} are exact copies; substitute them to audit committed evidence without reacquiring neurons. All new tests are discovered by the existing pytest/CI configuration.

## Acquisition and timing

Development network0–9/noise32 tuning,33 reserved, STATIC/LOSS; exploratoryUP0–9/noise32; NULL0–2/noise36; WEAK0–2/noise35. Validation10–14/noise32,33 STATIC/LOSS. Root20261018 and original role definitions. Every trial starts a new engine and advances continuously0–79s. Save54/64/74s checkpoints without restoring. Only after full79s completion replay matched1s active/sham probes. Static/loss/up share exogenous streams/commands until and after59s; no future gain or counterfactual enters public observations or algorithms. No observation stream is assembled from resets.

Every raw trial contains public.npz (all3950 completed20ms observations), plans.npz (desired/ramped prescribed commands), evaluator.npz (gain schedule/membership, evaluator-only), six probe observation archives and three probe plan archives; trial.json has config/seeds/parameter hashes/noise blocks/checkpoint hashes/constraints/timing/RSS. Arrays reuse the historical public observation schema: counts, raw E sector rate, filtered4sector rate, requested/delivered pA, integer start/stop/available us, valid/coverage, flat public spike event times/channels with offsets. Per-channel rates=count/(5*.02)Hz; filter initialization at15s. Successful receipt status/duration/schema/channel ordering/trial identity and canonical command ID c<start_us> are constant and asserted in arrays(); all variable numeric receipt fields/times are preserved. Trial ID m004-nN-rR-CONDITION, branch context disambiguates counterfactual receipt reuse.

Nominal charge=50*sum_jk u*.02pC; effective charge includes evaluatorgain. Gain is actuator coupling, not plasticity. Sham is a legal rampdown from prior delivered current, not instantaneous zero. Paired effect therefore means continuation versus rampdown from the same history. Exact active replay and null equality asserted during acquisition and independently audited.

## Online replay and model state

replay.py opens only public.npz and plans.npz. It processes forecasts before receiving the next bin, then updates on completed observations. Causal replay of an uninterrupted trajectory is information-equivalent here because inputs are fixed externally; this is not live hardware or a measured real-time closed-loop system. Future-observation mutation fixture succeeds with all evaluator/probe files absent. Source is not a security sandbox; actual functional information flow is tested.

initial.json contains final/provisional FIR, shuffled FIR and ARX coefficients/scales/diagnostics. online.npz:

- rolling[7,40,50,4]: models FROZEN,SW250,SW500,RLS995,RLS999,SHUFFLED,ARX; origins39..78s;50future20ms bins;4outputs. Known futureplans equally supplied, no future activity.
- one_step[7,2000,4]: predictions made before the corresponding observation, bins39–79s. Ordinary20ms errors are separate from rolling1s mean errors.
- theta[6,41,41,4]: six FIR-family parameters at clocks39..79s;41coefficients includingintercept peroutput. p[2,2,41,41]: RLS995/999 initial/final inverse information.
- contrast[7,3,2,50,4]: prospective active/sham forecasts at54,64,74s, generated without paired outcomes.
- detector[8,40,3]: nu(.25,.5) outer ×threshold(3,5,8,12) inner; completedblock ends40..79s; statistic-before-reset/armed/alarm.
- calibration_residual[8,4], width[4]; coefficient_norm/kernel_gain_proxy/baseline[6,41,...], update_counts[6,41], update_ns[6,2000], forecast_ns[7,40]. Undefined gain proxy uses NaN in NPZ, blank CSV, never zero imputation.

Parameter snapshots are at each forecast origin plus end, not every20ms; complete public bins and fixed algorithm reconstruct all intermediate updates. Numerical verification checks weighted-batch RLS at every origin plus interior one-step samples, all sliding refits, every rolling forecast and frozen/sliding/ARX next-bin forecast. No claim that every covariance matrix was serialized. update counts/latencies cover all observations. Failure records explicitly freeze the affected method's last valid state and prevent complete qualification; no base-case failure is silently replaced.

## Evaluator and statistics

Only analyze.py opens evaluatorgain or paired outcomes, after replay seal.json hashes all models/predictions. ORACLE uses initial FIR with lag-specific physical u*g and original fitted zero-input intercept; it has privileged gain, not future neural activity, and is an approximate reference rather than an exact prediction ceiling. It is never deployable or used for tuning.

CSV rolling: everytrial/model/origin1s mean-rate MSE,bias,MAE,coverage,amplitude. one_step: ordinary20ms pre/post metrics. windows: pre/post0–5/5–10/10–20s coverage/errors. effects: all3same-origin probes, all8models, paired contrast metrics. coefficients: kernel-scale proxy/baseline/parameternorm/updates, with truegain evaluator-only. failures: everymodel counters/status. detections and detector_blocks retain everyalarm/statistic/amplitude/arming state. event_present distinguishes real gain changes from STATIC/NULL pseudo-event window indicators. Alarms at59s are pre-change; timelywindow(59,69]s. Extraalarms after first matched event remain unmatched for eventprecision. WEAK has no causal gain information and is unarmed, never counted successful detection.

networks averages only reserved developmentnoise33 and confirmation32/33 within eachnetwork. TUNE32 metrics are separate selection evidence. Bootstrap10000 whole-network draws seed20261104; no bin/pulse/noise pseudo-replication. H1/H2 gates independent, both development and confirmation required. Individual candidate failures/stationarytradeoffs and secondary effects retained, not substituted for primary. Intercept adaptation can improve absolute prediction without improving intervention contrasts; report distinction prominently.

Independent audits use older preserved count/filter equations and new augmented least squares/discounted normal equations/recursions/CUSUM/aggregation, not the study estimator functions. This is independent analytical implementation in the same session, not an external investigator or alternate simulator/biological replication. SHA inventory excludes its own self-reference and final report closure; Git commits preserve those.
