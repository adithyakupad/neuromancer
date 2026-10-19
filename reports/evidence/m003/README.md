# M003 evidence and reproduction

Simulation-only identification study. Frozen protocol: `docs/research/005_M003_IDENTIFICATION_PROTOCOL.md` plus pre-acquisition `PREREGISTRATION_CLARIFICATION_001.md`. Read both. No historical protocol or neural parameter changed. All commands run from repository root using the pinned existing Python 3.12 environment; install the package with its existing `dev,diagnostic` extras on another machine.

## Executed workflow

The actual acquisition directories are exclusive and ignored under `runs/`; they remain locally available. Curated complete numerical arrays, coefficients, provenance and outputs are committed under `results/{D,V,G}`. The complete raw acquisition archives are also committed in each stage’s `raw/` directory, including separate prefix/plans/confirmation files and per-branch receipts. The lossless combined `identification_data.npz` supports analysis without stitching trials; no spike counts are omitted. Continuous raw voltage/time-resolved private currents were never requested or collected. `neurons` contains whole-neuron branch spike totals for evaluator checks, never model features.

Set `MPLCONFIGDIR=/tmp/neuromancer-m003-mpl OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`; Python used was `/tmp/neuromancer-audit/venv/bin/python`. Actual shell invocations and outputs are preserved in `commands.md` and `logs/`.

```sh
python -m neuromancer.identification_experiment --stage D --output runs/m003-dev-01
python reports/evidence/m003/fit_models.py runs/m003-dev-01 runs/m003-dev-models-01
python reports/evidence/m003/analyze.py runs/m003-dev-01 runs/m003-dev-models-01 runs/m003-dev-analysis-01
python reports/evidence/m003/verify.py runs/m003-dev-01 runs/m003-dev-models-01 runs/m003-dev-analysis-01
```

Only after both development scientific and software verification PASS:

```sh
python -m neuromancer.identification_experiment --stage V --qualification runs/m003-dev-analysis-01/comparison.json --output runs/m003-validation-01
python reports/evidence/m003/fit_models.py runs/m003-validation-01 runs/m003-validation-models-01 --selection runs/m003-dev-models-01/selection.json
python reports/evidence/m003/analyze.py runs/m003-validation-01 runs/m003-validation-models-01 runs/m003-validation-analysis-01
python reports/evidence/m003/verify.py runs/m003-validation-01 runs/m003-validation-models-01 runs/m003-validation-analysis-01
python -m neuromancer.identification_experiment --stage G --qualification runs/m003-dev-analysis-01/comparison.json --stationary runs/m003-dev-01 --output runs/m003-stress-01
python reports/evidence/m003/fit_models.py runs/m003-stress-01 runs/m003-stress-models-01 --reuse runs/m003-dev-models-01
python reports/evidence/m003/analyze.py runs/m003-stress-01 runs/m003-stress-models-01 runs/m003-stress-analysis-01 --stationary runs/m003-dev-analysis-01
python reports/evidence/m003/verify.py runs/m003-stress-01 runs/m003-stress-models-01 runs/m003-stress-analysis-01
```

V and G acquisition ran sequentially to bound memory; either result cannot change D selection. For each analysis directory run `figures.py DIRECTORY` (G additionally `--stationary runs/m003-dev-analysis-01`) and `summarize.py DIRECTORY`. The latter exports already-frozen endpoints, sector effects and delivered exposure, with independent primary-MSE assertions; it does not choose models or new gates. Figure styles and metadata are deterministic. No scientific neural acquisition was repeated to improve results.

```sh
python -m pytest -q --junitxml=reports/evidence/m003/final_tests.xml
python -m pip check
```

The final verification includes an independent numerical implementation, not a second investigator or external replication. New software fixtures use a known linear system; those are never described as neural scientific results. The initial too-tight coefficient-recovery fixture and its correction are retained in `predictor_initial_failure.txt` and Git history. The final test includes recovery at the original noisy setting with analytic coefficient standard errors.

## Committed data contracts

Each stage has `comparison.json` (network-level gates/intervals), `network_metrics.csv`, `trial_metrics.json` (every network/noise including nulls), `all_predictions.csv` (every model/condition and four sector effects), `conditioning.json`, `selection.json`, `trial_provenance.json`, `raw_summary.json`, `raw_provenance.json`, `analysis_lineage.json`, `verification.json`, deterministic PNG/SVG and `figure_manifest.json`. `models/` preserves all selected coefficients/scales/means/diagnostics, D's entire 24-candidate/trial grid, pre-evaluation recursive forecasts, separate interval calibration and hashes. G uses byte-identical D model/forecast artifacts, never a refit.

`identification_data.npz` uses `allow_pickle=False`, numeric arrays, first axis trials aligned with `identities[:, (network, noise)]`. Remaining axes:

| Field | Remaining axes | Meaning/units |
| --- | --- | --- |
| prefix_counts | 3350,20 | integer spikes per original recording channel |
| prefix_rates | 3350,4 | original causal filtered E sector rate, Hz; pre-initialization NaNs retained |
| prefix_delivered / prefix_desired | 3350,4 | delivered/planned steady request, pA |
| desired / planned / delivered | 6,100,4 | steady request / slew-validated known plan / actual hold, pA |
| counts / rates | 6,100,20 or 4 | reserved observations, spikes or Hz |
| neurons | 6,1000 | evaluator-only branch spike totals |
| recording / stimulation | 20,5 or 4,50 | exact neuron membership |
| forecast | 4,6,100,4 | pre-evaluation common-origin model forecasts, Hz |
| ordinary | 4,6,100,4 | teacher-forced causal next-step forecasts, Hz |
| interval_halfwidth | 4,3,4 | output halfwidth, model × horizon(1,10,50 bins) × sector, Hz |
| residual_threshold | 4 | per-model calibration lower05 observed-minus-predicted 1s mean rate, Hz |

Model order CONSTANT,AR,ARX,SHUFFLED; branch order S,P01,P12,P23,P03,R; sector/channel indexing is zero-based. Prefix bin k starts `20000*k` us, ends/is available at `20000*(k+1)` us. Reserved bin k starts `67000000+20000*k` us. All observations have 20 valid channels and 20000us coverage, asserted during acquisition and independently checked. No synthesized missing-mask values; no invalid observation was ignored. Request/delivery bin starts coincide; commands held until stop. Physical integration remains100us. Fit rows753..2349; no future normalization. `trained_start_us=15000000` in model diagnostics denotes the physical fitting phase; the exact valid row interval begins15060000us as preregistered.

Seed/source identities are complete in `raw_provenance.json` and `trial_provenance.json`: root20261018, fixed network roles0–3 replicate0, exogenous OU role4 indexed by absolute simulated1s blocks, randomized action role5 blocks0/1/2/3. Bootstrap seed20261030 is separate analytical randomness. Noise18–20 repeated within each network; null21; stress18 matched to D. IDs100–119 are absent from every acquisition manifest. `preservation.json` hashes all210 initially tracked files. Source commits and protocol hashes establish timing before acquisition/outcome inspection.

`delivered_exposure.csv` reports integral of sum of channel commands, pA*s=pC per command. Each command acts on50 cells: multiply by50 for total injected model charge across stimulated cells. This is simulated current exposure, not biological charge density or a hardware safety claim. All four P schedules have120pA*s exposure, including slew tails. R's realized exposure is measured per trial. `random_condition_metrics.csv` isolates the reserved R sequence, and `sector_responses.csv` preserves all four output effects without hidden-state selection.

## Offline evidence audit on a fresh checkout

To run the frozen verifier without reacquiring neural data, copy `results/D/raw` to the absent `runs/m003-dev-01` and `results/D` to absent `runs/m003-dev-analysis-01` first (these restore the exact original relative references in V/G manifests). Then run `verify.py results/D/raw results/D/models results/D` and the same for V/G, using the full `reports/evidence/m003/` prefix. Preserve any existing `runs/` directories; never overwrite them. The verifier checks historical source bytes as well as artifacts, so use this study revision. Reproduction of neural trajectories is a separate, more expensive check using the acquisition commands above.

Stage G's generic `comparison.json.scientific_gate` and primary-comparison plot reuse the D comparison formula as descriptive summaries. They are not a new confirmatory stress gate. Only D and V were preregistered for scientific qualification; stress interpretation is bias/coverage/residual generalization with paired uncertainty. The report states this explicitly.
