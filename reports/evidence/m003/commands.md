# M003 executed commands

Repository `/Users/adithyaupad/Developer/neuromancer`; environment `/tmp/neuromancer-audit/venv/bin/python` (below `PY`). Scientific/analysis commands used `MPLCONFIGDIR=/tmp/neuromancer-m003-mpl OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`. Output logs are preserved under `logs/`. Source/environment/seed/CLI identity for each neural stage is also recorded in its `raw/provenance.json`. These are commands actually executed; run-directory names are original, not new recommended experiments.

```sh
git status --short --branch
git rev-parse HEAD
git switch -c research/m003-system-identification
PY -m pytest -q --junitxml=reports/evidence/m003/baseline_tests.xml
PY -m pytest -q tests/test_identify.py
PY -m pytest -q --junitxml=reports/evidence/m003/tests.xml
PY -m neuromancer.identification_experiment --stage D --output runs/m003-dev-01
PY reports/evidence/m003/fit_models.py runs/m003-dev-01 runs/m003-dev-models-01
PY reports/evidence/m003/analyze.py runs/m003-dev-01 runs/m003-dev-models-01 runs/m003-dev-analysis-01
PY reports/evidence/m003/verify.py runs/m003-dev-01 runs/m003-dev-models-01 runs/m003-dev-analysis-01
PY reports/evidence/m003/figures.py runs/m003-dev-analysis-01
PY reports/evidence/m003/summarize.py runs/m003-dev-analysis-01
PY -m neuromancer.identification_experiment --stage V --qualification runs/m003-dev-analysis-01/comparison.json --output runs/m003-validation-01
PY -m pytest -q --junitxml=reports/evidence/m003/final_tests.xml
PY -m pip check
PY -m neuromancer.identification_experiment --stage G --qualification runs/m003-dev-analysis-01/comparison.json --stationary runs/m003-dev-01 --output runs/m003-stress-01
PY reports/evidence/m003/fit_models.py runs/m003-validation-01 runs/m003-validation-models-01 --selection runs/m003-dev-models-01/selection.json
PY reports/evidence/m003/analyze.py runs/m003-validation-01 runs/m003-validation-models-01 runs/m003-validation-analysis-01
PY reports/evidence/m003/verify.py runs/m003-validation-01 runs/m003-validation-models-01 runs/m003-validation-analysis-01
PY reports/evidence/m003/figures.py runs/m003-validation-analysis-01
PY reports/evidence/m003/summarize.py runs/m003-validation-analysis-01
```

The first new synthetic coefficient-recovery fixture failed an unrealistically tight deterministic tolerance at noise SD.01. Its output is retained; the low-noise recovery fixture and a separate original-noise analytical-standard-error fixture now both pass. No neural seeds or results were changed. `analysis_tests.txt` and `extended_tests.txt` retain intermediate successful checks; `final_tests.txt/xml` is the complete final65-test run. Repeated supporting exports/figure renders do not reacquire neural data.

A read-only process-list probe (`ps -axo pid,etime,pcpu,rss,command`) was denied by the sandbox. No CPU/process measurement is inferred from that probe. Resource measurements use elapsed timers and the Python worker's actual recorded `ru_maxrss`; aggregate process peak memory was not directly measured. Git branch/commit writes were authorized sandbox escalations. No network download, package installation or external message was needed.

Final frozen-model and reproducibility commands (same environment):

```sh
PY reports/evidence/m003/fit_models.py runs/m003-stress-01 runs/m003-stress-models-01 --reuse runs/m003-dev-models-01
PY reports/evidence/m003/analyze.py runs/m003-stress-01 runs/m003-stress-models-01 runs/m003-stress-analysis-01 --stationary runs/m003-dev-analysis-01
PY reports/evidence/m003/verify.py runs/m003-stress-01 runs/m003-stress-models-01 runs/m003-stress-analysis-01
PY reports/evidence/m003/figures.py runs/m003-stress-analysis-01 --stationary runs/m003-dev-analysis-01
PY reports/evidence/m003/summarize.py runs/m003-stress-analysis-01
PY reports/evidence/m003/reproduce.py runs/m003-dev-01 runs/m003-dev-models-01 runs/m003-dev-analysis-01 runs/m003-dev-reanalysis-01
PY reports/evidence/m003/reproduce.py runs/m003-validation-01 runs/m003-validation-models-01 runs/m003-validation-analysis-01 runs/m003-validation-reanalysis-01
PY reports/evidence/m003/reproduce.py runs/m003-stress-01 runs/m003-stress-models-01 runs/m003-stress-analysis-01 runs/m003-stress-reanalysis-01 --stationary runs/m003-dev-analysis-01
PY reports/evidence/m003/verify.py reports/evidence/m003/results/D/raw reports/evidence/m003/results/D/models reports/evidence/m003/results/D
PY reports/evidence/m003/verify.py reports/evidence/m003/results/V/raw reports/evidence/m003/results/V/models reports/evidence/m003/results/V
PY reports/evidence/m003/verify.py reports/evidence/m003/results/G/raw reports/evidence/m003/results/G/models reports/evidence/m003/results/G
```

Complete raw/model/analysis directory copies were made with standard-library `shutil.copytree/copy2`, then verified in the committed layout. Supporting source/doc whitespace checks exclude immutable generated CSV/SVG/XML. Final source/history/split/artifact inventory checks are in `verification_manifest.json`.
