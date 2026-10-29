# Reproducing the NEUROMANCER V1 research instrument

This is a simulated recurrent spiking-network research platform. It is not a biological experiment, a model of living-neuron learning, or hard real-time hardware software. Scientific release scope and actual qualification decisions are in `reports/NEUROMANCER_V1_RESEARCH_REPORT.md`; historical reports retain their original decisions.

## Environment

Use CPython3.12 on a machine with sufficient memory; all original package pins are in `requirements-m002.txt`. `requirements-v1.txt` adds the explicitly qualified SciPy verification dependency. No automatic version upgrade is part of reproduction.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-v1.txt
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m pip check
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q
```

Thread environment variables request a limit; they do not prove the operating BLAS thread count. Retain measured thread-pool metadata where available. The numerical stream contract is deterministic for the qualified platform/software stack; cross-platform bitwise reproducibility requires a fresh comparison and is not assumed.

## Scientific contract

`docs/research/011_M005B_CONTROL_PROTOCOL.md` is the authoritative frozen experiment. Read it before acquisition. It fixes the neural model, original51s calibration,64s regulation, hidden efficacy loss at relative16s, FIR structure, RLS policy,625-candidate planner, PI10/5, trial identities, budgets and network-level inference. The scheduling/encoding qualification in documents012/013 does not change scientific settings. Never use calibration or held-out outcomes to retune the frozen study.

Development uses networks0–9/noise47–48. Validation10–14/noise49–50 is conditional on all development primary gates passing. Locked100–119 are excluded and require a separate authorized protocol. Development secondary faults use0–2/noise49 only after the primary decision is frozen; they cannot rescue a failed gate.

## Execution

Run from a clean committed checkout. Use unique empty output directories: incomplete attempts are evidence and must not be overwritten. Acquire only after all engineering readiness checks and resource forecasts pass.

```sh
export VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
.venv/bin/python -m neuromancer.m005b_study acquire --phase primary --output reports/evidence/v1_finish/m005b/primary
```

The CLI launches three owned workers, uses a shared boot-scoped suspend-inclusive deadline, preserves16s segments, checks memory/storage and marks complete branches/trials explicitly. It inhibits idle sleep but cannot enforce user-space deadlines while the host is suspended. Physical sleep/resume was not deliberately exercised during this study. Expiry/resume/clock faults stop rather than reset budgets.

Analysis must run under a single2,400s boot-scoped `Deadline` shared by its nested commands; see the saved analysis launch and exact command manifest. Set `NEUROMANCER_DEADLINE_NS` and `NEUROMANCER_DEADLINE_CLOCK` from that launch, never from a different boot. Main analysis:

```sh
.venv/bin/python -m neuromancer.m005b_analysis reports/evidence/v1_finish/m005b/primary reports/evidence/v1_finish/m005b/analysis_primary
```

Independent verification scripts in `reports/evidence/v1_finish/` reconstruct counts/receipts/model states/planner scores (`verify_study.py`), raw targets/statistics/gates (`verify_metrics.py`), and weak-excitation shadow predictions (`shadow_controls.py`). They are analysis-only and receive no authority to choose new actions. Pass explicit fresh output paths. They fail on incomplete cohorts. Failed scientific gates leave validation closed; no result-dependent replacement is allowed.

## Evidence and interpretation

The initial51s prefix is shared computationally across branches, but its physical-current exposure is counted for every arm. Each branch restores the exact same neural checkpoint and common absolute-time OU stream. Diverged closed-loop branches do not have identical later neural states. Noise repeats are averaged within network before inference; bins are not independent network replicates.

The causal codec retains delivered input, observed output, validity/counters, per20ms model-state hashes and dense1s snapshots. Replaying this information reconstructs all intermediate coefficients/information. Each plan retains all625 scores, origin coefficients/history and chosen forecast; omitted alternate forecasts can be reconstructed. This avoids redundant storage without changing numerical updates.

Retain every incomplete attempt, failure cause and historical negative result. A process exit is not a scientific PASS. Full adaptive scientific success requires improvement against both PI and fixed predictive control plus cost, stationary, final-bias and safety guards. Biological validity, generalization to unseen preparations and hardware timing are unvalidated.
