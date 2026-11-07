# Reproducing M002.1

This is a simulation-only diagnostic, preregistered in PREREGISTRATION.md.
The original neural model, public observation interface and V0 protocol are unchanged.
Use the M002 Python3.12 environment and requirements-m002.txt; no new dependency.

```sh
python -m neuromancer.authority_diagnosis --output runs/m002_1-new
python reports/evidence/m002_1/analyze.py runs/m002_1-new runs/m002_1-new-analysis
python reports/evidence/m002_1/verify.py runs/m002_1-new runs/m002_1-new-analysis
python reports/evidence/m002_1/export_tables.py runs/m002_1-new-analysis
python reports/evidence/m002_1/figures.py runs/m002_1-new-analysis
python -m pytest -q
```

The simulation command fixes ten training networks, five noise replicates,
eight actions and two gains, using three worker processes. It takes substantially
longer than the M002 smoke test. Output directories must be new; failed trials
retain append-only partial condition records. No controller or neural fitting runs.

Raw per-trial NPZ contains per-neuron counts, observed20 ms counts, private current
means/traces and all actual delivered current schedules. Curated authority_data.npz
retains every trial's counts, current-group means, observed/raw/filter rates,
actual schedules and membership maps; the 50-trial mean current time course is
labeled as an aggregate. It does not retain every individual-neuron current sample.
All numeric archives load with allow_pickle=False. The accompanying JSON preserves
all800 condition outcomes,800 action audits and50 provenance/seed/checkpoint records.

Population definitions matter: fixed_unstim_E is the same600 never-targeted E
cells for every allocation. action_unstim_E also includes inactive stimulation
channels (700 E for concentrated actions). A directly active population is absent
for sham; its response is undefined, not zero firing. The primary observed80 E
population always stays fixed. The analysis subtracts sham activity on identical
cell memberships before averaging noise replicates.

Primary network CIs have five independent noise units. The global allocation is
selected on replicates0–1 and evaluated on2–4; it has only three evaluation noise
units and wider CIs. Whole-window bins and neurons are not replication units.
Pointwise intervals are descriptive and are not multiplicity-adjusted claims.

Committed curated results live in results/. raw_summary.json hashes the separate
local raw run, not files relative to this curated folder. manifest.json hashes the
curated evidence. verification.json records the independent checks and byte-identical
figure regeneration. all_trials.csv has800 conditions; network_intervention_summary.csv
has160 network/gain/action rows with noise SD/CI; sector_trials.csv has3200 rows for
the four fixed sector populations. Parameter maps and actual schedules are in the
curated numeric archive; raw numerical arrays remain locally in the ignored run
folder. No raw run was deleted.
