# Actual execution ledger

Working directory /Users/adithyaupad/Developer/neuromancer. Python /tmp/neuromancer-audit/venv/bin/python. Shell zsh. See stages.json for exact executed post-acquisition argument vectors, UTC starts, return codes and measured stage durations. Acquisition CLI/environment/head/source hashes in results/raw/provenance.json. All scientific subprocesses set VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1; post-acquisition also MPLCONFIGDIR=/tmp/neuromancer-m003-2-mpl. No install/download.

1. Verified git status, branch, exactfd003766d2dc1774e4ba2fce086f092e2736d41d and historical source/protocol/report/evidence. Hashed1253 startingfiles. Created requested research/m003-2-state-dependence; committed preregistration7c82912 before neural acquisition.
2. Python -m pytest -q --junitxml=reports/evidence/m003_2/initial_tests.xml -> initial_tests.txt:81PASS (74historical+7new),28.04s.
3. Committed acquisition/predictors/tests1ce720e. Python -m neuromancer.state_experiment --output runs/m003-2-01 -> acquisition.log, three workers, fixed53trials/45mincap. No rerun/seed replacement.
4. Added two leakage/separation tests. Python -m pytest -q tests/test_state_dependence.py -> new_tests.txt:9PASS,17.37s.
5. Python environment inspection -> environment.json, np.show_config identifies Apple Accelerate; actual threading not measured. Python -m pip check -> pip_check.txt: no broken requirements. compileall on new sources/evidence scripts:success.
6. Python -m pytest -q --junitxml=reports/evidence/m003_2/tests.xml -> tests.txt:83PASS,25deprecationwarnings,49.50s (concurrent acquisition).
7. Independent preselection audit on completed FIT/validation26–28 only -> preselection_audit.json:255 archivesPASS; no reserved29/30 or null31 outcomes opened.
8. Bounded run_stages.py waits for complete acquisition summary, then sequentially runs fit_models, analyze, figures, verify; each900s cap, exclusive directories and logs. fit_models freezes/hash-seals predictions before analyze opens reserved branch outcomes. All actual command vectors/statuses are retained in stages.json. Subsequent reanalysis and curated-copy audit are recorded in final verification manifest.

No preceding scientific protocol, source, result or test fixture modified. No locked/validation network acquisition, controller, neural tuning, extra noise replicate or opportunistic extension. Local tests/probes are instrument checks, not extra scientific observations used for fitting/selection.
