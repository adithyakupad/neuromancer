# M003.1 actual command record

Repository `/Users/adithyaupad/Developer/neuromancer`. Actual Python `/tmp/neuromancer-audit/venv/bin/python` (abbreviated `PY` below); scientific commands set `MPLCONFIGDIR=/tmp/neuromancer-m003-1-mpl OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`. Output logs, test XML and stage manifests accompany this record.

Executed before outcome scoring:

```sh
git status --short --branch
git rev-parse HEAD
git switch -c research/m003-1-model-necessity
PY -m pytest -q tests/test_necessity.py
PY -m pytest -q --junitxml=reports/evidence/m003_1/tests.xml
PY -m neuromancer.necessity_experiment --output runs/m003-1-01
PY -m pytest -q tests/test_necessity.py
PY -m pytest -q --junitxml=reports/evidence/m003_1/final_tests.xml
PY -m pip check
PY -m compileall -q reports/evidence/m003_1
```

Historical audit used SHA256 over all849 starting tracked files, and independently checked all637 entries of `reports/evidence/m003/verification_manifest.json`; no historical output file was rewritten. Pure numerical fixture checks and old regression simulations are software verification, not new scientific-cohort observations. New trials use only the preregistered33 network/noise identities. Failed commands/runs, if any, remain in logs and are explained in the report. Git branch/commit mutations used authorized sandbox escalation; no download, external messaging or remote merge.

Executed fitting/scoring/audit commands, in order (same interpreter/environment):

```sh
PY reports/evidence/m003_1/fit_models.py runs/m003-1-01 runs/m003-1-models-01
# Above failed before confirmation; source caller repair and test committed in ae1d7d0.
PY -m pytest -q tests/test_necessity.py
PY reports/evidence/m003_1/fit_models.py runs/m003-1-01 runs/m003-1-models-02
PY reports/evidence/m003_1/analyze.py runs/m003-1-01 runs/m003-1-models-02 runs/m003-1-analysis-01
PY reports/evidence/m003_1/verify.py runs/m003-1-01 runs/m003-1-models-02 runs/m003-1-analysis-01
PY -m pytest -q --junitxml=reports/evidence/m003_1/qualification_tests.xml
PY reports/evidence/m003_1/figures.py runs/m003-1-analysis-01
PY reports/evidence/m003_1/cost.py runs/m003-1-01 runs/m003-1-models-02 runs/m003-1-analysis-01
PY reports/evidence/m003_1/reproduce.py runs/m003-1-01 runs/m003-1-models-02 runs/m003-1-analysis-01 runs/m003-1-reanalysis-01
PY reports/evidence/m003_1/bundle_audit.py runs/m003-1-analysis-01
PY reports/evidence/m003_1/verify.py reports/evidence/m003_1/results/raw reports/evidence/m003_1/results/models reports/evidence/m003_1/results
PY reports/evidence/m003_1/bundle_audit.py reports/evidence/m003_1/results
```

All failed fitting files/logs were preserved; a byte comparison verified33 files identical in the rerun. A metadata-span writer initially requested unavailable `st_birthtime_ns`; documented fallback uses float-second `st_birthtime` and records an elapsed filesystem span, not an isolated failed-fit runtime. Copies used standard-library shutil.copytree/copy2. Additional read-only NumPy configuration inspection identified Apple Accelerate; actual thread count was not measured (`RESOURCE_DEVIATION_001.md`). Whole-neural acquisition was never rerun.
