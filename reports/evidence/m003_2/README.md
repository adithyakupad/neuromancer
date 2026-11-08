# M003.2 evidence and reproduction

Frozen protocol: docs/research/007_M003_2_STATE_DEPENDENCE_PROTOCOL.md, preregistration commit7c82912. Starting1253 historical paths preserved by preservation.json. Acquisition source1ce720e; no historical files changed.

Existing pinned Python environment: /tmp/neuromancer-audit/venv/bin/python (recreate from requirements-m002.txt and editable package if absent). Set VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 before Python. CPU costs are local workload measurements, not verified single-thread/hardware guarantees.

Acquisition command (exclusive new directory):

    python -m neuromancer.state_experiment --output runs/m003-2-01

Then sequentially, new exclusive stage directories:

    python reports/evidence/m003_2/fit_models.py --raw runs/m003-2-01 --output runs/m003-2-models-01
    python reports/evidence/m003_2/analyze.py --raw runs/m003-2-01 --models runs/m003-2-models-01 --output runs/m003-2-analysis-01
    python reports/evidence/m003_2/figures.py --analysis runs/m003-2-analysis-01 --raw runs/m003-2-01 --models runs/m003-2-models-01
    python reports/evidence/m003_2/verify.py --raw runs/m003-2-01 --models runs/m003-2-models-01 --analysis runs/m003-2-analysis-01 --output runs/m003-2-analysis-01/verification.json
    python -m pytest -q

Curated results/raw, results/models, results/analysis mirror these three stage directories. Substitute them for scratch paths to verify committed evidence without reacquisition. Both entrypoints and scripts use existing package helpers, no new dependency/plugin framework/export change. Existing CI discovers new tests automatically.

## Raw schema

53 trials nN_rR: network0–9; noise26,27 fitting;28 selection+empirical intervals;29,30 reserved; null0–2/noise31. All use root20261018. Config/seed roles, parameter hashes, OU block hashes, source/git/environment and command provenance in raw/provenance.json and trial.json. plans.npz preserves7×100×4 requested desired and ramped planned pA values. Names S,C0,C1,C2,C3,P,R. No gain/hidden variable in model inputs.

backbone.npz contains1750 completed20ms observations from0–35s. Each LOW/HIGH/origin.npz contains only available last50 observations, zero input histories, scalar, completed-calibration thresholds and absolute origin time; no future branch outcome. LOW/HIGH/origin.json records evaluator checkpoint hashes/common-noise map/branch budgets and runtime. Seven separate branch NPZs preserve counts(100,20), original raw sector/filtered rates(100,4), requested/delivered currents(100,4), integer start/stop/available times, valid/coverage arrays, spike-event offsets/times/channel IDs and evaluator-only1000-cell total spikes. Branch comparisons assert exact restoration and common exogenous blocks at execution. Monitor counts verify recording assignments; raw neuron totals never enter features.

Successful receipts all have schema1, status delivered, trial_id state-nN-rR, command_id c<start_us>, all ordered channels(0,1,2,3), duration20000us, requested_start=delivered_start=observation start, delivered_stop=observation stop; this is asserted for every bin. Numeric receipt values and times are in archives, canonical constant fields here and in source. Missing/invalid commands are not used. Per-channel rates_hz are exactly counts/(5*.02) Hz and are losslessly reconstructible. Original filter_initialized is false before15s and true thereafter, inferred exactly from absolute times; NaNs before initialization preserved. Offset ragged arrays retain every public recorded spike event.

Exposure is sum_jk u*.02 pA*s. Nominal model charge is50times exposure pC (50 stimulated cells/channel); multiply by hidden efficacy for effective injection, zero in null. This is model charge, not measured energy or a biological safety claim. Stimulation/recording membership and baseline/elapsed-time diagnostics preserved per trial.

## Models and scoring schema

FIR and STATE are direct paired-effect regressions trained using simulator counterfactuals, not a demonstrated biological calibration procedure. Validation outcomes28 are allowed; reserved29/30 and null31 outcomes are not opened until after forecast_seal.json. fit_models.py accesses reserved origin/plans only; a corruption test enforces that loader path. Candidate/selected/half-data JSON preserves all coefficients, scaling, rank/singular values, conditions/penalties; ARX is a secondary absolute-rate model. intervals.npz axes network,model,horizon. No intercept for direct effects; exact zero-input contrast.

Forecast NPZ axes model[FIR,STATE,STATE_SHUFFLED,FIR_SHUFFLED,ARX], stratum[LOW,HIGH], branch[S,C0,C1,C2,C3,P,R], futurebin100,sector4. delta and absolute arrays preserve all predictions; _half uses only fitnoise26 with frozen global penalty. Fitnoise26/27 labels are completed active-minus-sham training data, equal for all primary models. Forecast seal hashes all coefficients and predictions before reserved evaluator starts.

Analysis data.npz: actual axes network10,noise2,stratum2,branch7,horizon4,sector4; predicted/errors add model5 after noise. Horizons1,10,50,100bins =20,200,1000,2000ms. network axes10,model5,horizon4 average active6actions/strata/noises/sectors equally. Primary first50-bin *mean* response MSE, not mean per-bin MSE. Episodes/sectors/networks CSVs give all granularity; no time-bin pseudo-replication. Origins table includes everyphase/null. Residual_lag1 is withinbranch, origin_ablation replaces scalar with fittedmean, null records actualzero and false predictedresponses. comparison.json gives frozen gates and whole-network bootstrap.

Empirical interval validation reused selectionnoise28; dependence/limited calibration prevents certified coverage. State label control swaps two strata within each fitreplicate; its information-inversion limitation was preregistered. Report all results rather than interpreting a useful absolute forecast as causal-state identification.

Independent verify.py implements separate lags, normal equations, recursion, event/count filters, origin selector, selection and scoring/bootstrap; it is not external investigator replication. Deterministic figures fix SVG hash salt/metadata. Reanalysis comparison excludes only measured runtime. Final hash manifest inventories every artifact; historical protocols/results are unchanged.

Deterministic reanalysis into another exclusive directory:

    python reports/evidence/m003_2/reproduce.py --raw reports/evidence/m003_2/results/raw --models reports/evidence/m003_2/results/models --original reports/evidence/m003_2/results/analysis --output runs/m003-2-reanalysis-01

It checks every regenerated numerical/CSV/PNG/SVG byte and every scientific JSON field; only measured analysis runtime differs. No simulation is rerun and no hyperparameter is reselected.
