# M002.2 reproduction and evidence

Simulation-only finite-bank measurement; no controller/model fitting. Original model,
observations, stimulation bounds and108 previously tracked files remain unchanged.
See PREREGISTRATION.md and the explicitly committed pre-execution arithmetic correction
PREREGISTRATION_AMENDMENT_001.md. Noise IDs5–7 are new, networks0–9 only.

Use Python3.12 and the unchanged requirements-m002.txt environment. No new dependency.
Commands assume repository root; output directories must not already exist.

```sh
python -m neuromancer.reachability --output runs/m002_2-new
python reports/evidence/m002_2/analyze.py runs/m002_2-new runs/m002_2-new-analysis
python reports/evidence/m002_2/verify.py runs/m002_2-new runs/m002_2-new-analysis
python reports/evidence/m002_2/figures.py runs/m002_2-new-analysis
python -m pytest -q
```

The fixed run uses three process workers,30 prefixes and720 six-second branches
(4770 simulated seconds). No frequency/phase/amplitude search, noise replacement or
subset inference. Failures preserve partial condition logs. A missing or partial
summary is not a complete experiment, and analysis requires all30 trials.

Curated data live in results/. reachability_data.npz retains every trial's
per-neuron total counts,24 evaluator-group20 ms counts,20 permitted observation
channel counts, unchanged filter traces, delivered and desired action schedules,
baseline counts, time grids and memberships. Temporary full-neuron spike events
are counted during execution but not kept in the final arrays. No hidden activity
selects an action or target. All NPZ loads use allow_pickle=False.

all_trials.csv has720 network/noise/gain/action rows; network_summary.csv has240
network/gain/action mean/SD/t-CI rows; sector_trials.csv has2880 sector rows. JSON
contains all prespecified bootstrap summaries, finite-bank range, held-out-noise
readout, target gate and timing descriptors, plus30 complete seed/config/checkpoint
records and720 delivered-action audits. One trajectory or correlated time bin is
never treated as an independent network.

raw_summary.json hashes the local raw run files, separate from curated files.
manifest.json hashes curated files. raw_provenance.json identifies the executed
source/dirty state, seed roles, versions and both preregistration hashes. Analysis
lineage is recorded separately rather than pretending later documentation existed
at simulation execution. Raw files remain locally under the ignored run folder.

The fast objective uses the original100 ms causal filtered rate. The slow candidate
uses raw counts over1 s epochs as a rate summary; it does not change observations.
The standalone noise screen is not a feedback efficacy measurement, and a failed
conservative headroom CI may reflect insufficient precision. All gates and their
components must be reported regardless of the final proposal recommendation.
