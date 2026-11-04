# M003.1 evidence and reproduction

Simulation only; frozen protocol `docs/research/006_M003_1_MODEL_NECESSITY_PROTOCOL.md`. Preserve M001–M003: all849 starting tracked files hashed in `preservation.json`. The M003 artifact audit is separately recorded in `historical_audit.json` (all637 M003 inventory hashes verified).

## Model and acquisition boundaries

`neuromancer.necessity` adds static/FIR fits and adapts the unchanged public M003 ARX predictor. All models fit the same1550 targets (rows800..2349,16–47s), with fit-only scaling/intercept. `forecast_inputs(record,u_history,plan)` accepts no observed rates. The common wrapper dispatches to that pure function for STATIC/FIR and never reads its rate argument; mutation tests verify this. AR/ARX alone use completed observations. No input-only initial baseline is obtained from future sham: fixed training intercept/output mean only, past delivered input history for FIR. The absolute-rate information sets differ deliberately; common-origin linear contrasts cancel initial rate history exactly.

`neuromancer.necessity_experiment` reuses the unchanged M003 six-branch acquisition function. Its worker supplies only the registered schedule/name constants in each independent spawned process. Historical code and shared state are unchanged; this adapter is not a general plugin interface. Each new worker handles only M003.1 jobs. All neural/model/OU parameters, memberships, queues, refractory state, filter and clocks are original. Existing and new tests cover constraints/rank and exact mathematical replay; live acquisition asserts exact checkpoint restoration/noise agreement and receipts for every bin/branch.

## Commands

Actual interpreter `/tmp/neuromancer-audit/venv/bin/python`, existing pinned Python3.12 environment. Prefix scientific commands with `MPLCONFIGDIR=/tmp/neuromancer-m003-1-mpl OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`. Run from repository root; use exclusive absent run directories, never overwrite evidence.

```sh
python -m pytest -q tests/test_necessity.py
python -m pytest -q --junitxml=reports/evidence/m003_1/final_tests.xml
python -m neuromancer.necessity_experiment --output runs/m003-1-01
python reports/evidence/m003_1/fit_models.py runs/m003-1-01 runs/m003-1-models-02
python reports/evidence/m003_1/analyze.py runs/m003-1-01 runs/m003-1-models-02 runs/m003-1-analysis-01
python reports/evidence/m003_1/verify.py runs/m003-1-01 runs/m003-1-models-02 runs/m003-1-analysis-01
python reports/evidence/m003_1/figures.py runs/m003-1-analysis-01
python -m pip check
```

Exact commands/source revisions, execution logs, manifests and runtime measurements accompany the report. The fitter opens only `prefix.npz` and `plans.npz`, never `confirmation.npz` or evaluator-only `trial.json`. All candidate/selected models and common-origin forecasts are saved and hashed before scoring. Hyperparameters are globally selected on new chronological hypervalidation only (no old validation network reuse). Nulls use these choices without tuning. The selected strongest stimulation-only family is fixed by validation absolute1s output loss, never by reserved effects or a per-network oracle.

The primary metric cannot establish initial-state necessity for a linear additive model: subtract common-origin recursions and the shared observation history cancels. The independently computed zero-state IIR kernel and mean-history replacement ablation test that identity numerically. The ARX input-response kernel can still differ from a finite FIR; any superiority must be interpreted as a predictive parameterization result, not state-information proof. This distinction was frozen before acquisition.

## Data and clocks

The committed `results/raw/` contains every trial `n{network}_r{noise}` with separate public prefix/plans, evaluator-only confirmation, receipt ledger and full seed/source/checkpoint/noise provenance. `results/models/` contains all grid candidates, selected coefficients/scales/means, conditioning, validation scores, calibration intervals, mean-history ablation and pre-evaluation forecasts. `results/data.npz` is a lossless combined numeric archive (`allow_pickle=False`), first axis trials aligned to `identities`.

| Field | Remaining axes | Units/meaning |
| --- | --- | --- |
| prefix_counts/rates |3350×20 /3350×4| integer spikes / original filtered E rates Hz |
| prefix_delivered/prefix_desired |3350×4| actual pA / desired steady pA |
| desired/planned/delivered |6×100×4| desired steady action / known slew plan / actual delivered hold, pA |
| counts/rates |6×100×20 /6×100×4| public spike observations / filtered Hz |
| neurons |6×1000| evaluator-only total spikes per neuron, never features |
| recording/stimulation |20×5 /4×50| exact disjoint neuron IDs |
| forecast/ordinary |7×6×100×4| saved open-loop / teacher-forced next-step forecasts, Hz |
| width |7×4×4| absolute-output interval halfwidth, model×horizon×sector, Hz |
| ARX_mean_history |6×100×4| forecast after origin rate-history replacement, Hz |

Models: STATIC,FIR,ARX,AR,STATIC_SHUFFLED,FIR_SHUFFLED,ARX_SHUFFLED. Branches: S,SHORT,LONG,NEAR,FAR,R. Horizons:1,10,50,100bins (20ms,200ms,1s,2s means). Prefix bin k starts20000*k us and ends/is available at20000*(k+1); reserved starts67000000+20000*k. All20 validity-mask entries are true with20000us coverage, asserted live; no missing channel was silently ignored. Integration100us is distinct from20ms observation/command ticks. Plan and actual delivery agree exactly after acquisition; only the known plan enters a prospective forecast.

Calibration origins55..62s and the preregistered2s horizon imply final calibration target ends64s in the zero washout phase; this follows the frozen origin/horizon arithmetic. No fitting/selection data extend beyond their stated target intervals and all calibration precedes67s confirmation. The saved snapshot states64s explicitly. Overlapping calibration origins are correlated: intervals are empirical diagnostics, not certified coverage or paired-effect intervals.

`all_predictions.csv` retains every model/condition/sector/noise; `trial_metrics.json` retains all scalar/horizon statistics, nulls and failures; `network_metrics.csv` is the primary network means. `comparison.json` contains equal-network hierarchical bootstrap intervals and frozen primary decision. `conditioning.json`, all candidate coefficient files and selected model manifests retain full singular spectra, rank, conditions, parameter counts and effective history. `delivered_exposure.csv` records actual bounds/slew/charge: structured four conditions each24pA*s summed commands, multiplied by50cells/channel gives1200pC total injected model charge; this is not biological charge-density safety evidence.

Bootstrap seed20261101; root20261018; unchanged network roles0–3, independent neural noise22–24/25 role4 absolute-time blocks, action role5 blocks0/1/2/4. No validation IDs10–14 or test100–119 acquired. `verification.json` is an independent analytical implementation in this session, not an external investigator or second simulator. Prior source remains available and hash-verifiable.

The latest complete regression run is `qualification_tests.txt/xml`:74 passed (65 historical+9 new). Earlier71/72-test outputs are retained. `FAILED_FIT_001.md` and `caller_repair_replay.json` explain the preserved pre-confirmation caller-alignment failure; all33 already-produced model/selection files matched exactly on repaired deterministic rerun, without repeating neurons. `results/failed_fit_001/` preserves that entire attempted fit. Successful model directory is `runs/m003-1-models-02`.

`bundle_audit.py DIRECTORY` independently checks all whole-network bootstrap fields/relative intervals and exact original memberships, checks every new R sequence, and exports declared per-condition descriptive metrics. It changes no frozen scientific endpoint. `cost.py RAW MODELS ANALYSIS` runs the fixed five-refit/50-forecast probe on n0/noise22; it never reads confirmation outcomes. `reproduce.py RAW MODELS ORIGINAL NEW` verifies every scientific field/archive/figure again, excluding only measured analysis time. For offline verification on a fresh checkout use `verify.py reports/evidence/m003_1/results/raw reports/evidence/m003_1/results/models reports/evidence/m003_1/results`; no original ignored runs path is required.

Resource disclosure: NumPy uses Apple Accelerate. OPENBLAS_NUM_THREADS/OMP_NUM_THREADS were requested as1, but actual BLAS thread count was not measured/verified. See `RESOURCE_DEVIATION_001.md`; these are local-machine performance measurements, not verified single-thread results. No package was changed to rescue outcomes.

Charge semantics: `model_charge_pC` in the inherited receipt/exposure schema is nominal command-equivalent charge across50 targets/channel, before the effective-coupling multiplier. It is1200pC for structured primary g=1 actions. Null g=0 retains the same delivered command/exposure ledger but has zero effective injected current/charge. Do not interpret the nominal null field as actual effective injection or hardware charge.
