> Final hosted engineering gate FAIL/HOLD: one unchanged supervisor real-worker timing fixture failed on macOS. Local199PASS and prior CI199PASS are retained, not substituted. See the comparison report final addendum.

# V1.1 performance review candidate

This branch is `1.1.0rc1`, not a published release. V1.0.0 preparation remains isolated
on release/v1-license-version (PR #1). Do not include these source changes in v1.0.0.
No new biological or adaptive-control superiority claim. The V1 scientific record is fixed.

## Install and reproduce

Use Python3.12 and the unchanged requirements-v1.txt stack. In an isolated environment:

```sh
python -m pip install -r requirements-v1.txt
python -m pip wheel --no-deps --no-build-isolation . -w dist
python -m pip install --no-deps dist/neuromancer-1.1.0rc1-py3-none-any.whl
python -m pip check
python -m pytest -q
PYTHONPATH=src python benchmarks/v1_1.py --output runs/performance-FRESH
PYTHONPATH=src python benchmarks/qualify.py runs/paired-FRESH python benchmarks/paired_latency.py --output runs/paired-FRESH.json
python scripts/reproduce_v1_evidence.py --output runs/evidence-FRESH
```

The main benchmark output must not exist; its shared900s deadline includes process cleanup.
The paired latency script accepts --output FRESH.json and requires the same inherited deadline as the supervisor. Other supplementary scripts currently write to curated reports/performance/evidence paths and
therefore are audit tools, not overwrite-safe public run entry points. Do not rerun wheel or final-qualification scripts over curated evidence. For a new complete audit, use
an isolated checkout/copy and change output destinations prospectively. The main benchmark,
CLI and scientific reproduction helper support fresh user-selected outputs.

## Scope

Accepted: streamed SHA256 payloads; stop clipping after fixed candidate holds are reached.
Rejected: explicit coarse-OU out= arithmetic (no extra measured benefit).
All mathematical operations,625candidate forecasts/costs/ties,PI/RLS behavior,stimulation
bounds,100us integration,20ms observations and random-stream identities preserved.
Exact equivalence applies to executed fixtures/replayed records, not a mathematical proof
for all future environments. Supported backend remains Brian2 NumpyCodeObject.

Measured gains are modest in runtime and substantial in peak allocation/RSS. The2x workflow,
2x neural and30% p95 targets were NOT MET. OS tail latency varied and sometimes regressed.
This is a review candidate; performance-target qualification remains PARTIAL/HOLD.
No publication or automatic scientific acquisition is authorized.

See reports/performance/V1_BASELINE.md, V1_OPTIMIZATION.md and V1_BENCHMARK_COMPARISON.md.
Scientific proposals live on research/v1-1-proposals, not this implementation branch.
