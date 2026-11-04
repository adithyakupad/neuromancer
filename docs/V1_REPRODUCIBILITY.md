# Reproducing the V1 simulation research instrument

Use this guide from the repository root. It distinguishes a small smoke example, **source-artifact reproduction** and a fresh scientific acquisition. None establishes biological or hard-real-time hardware validation.

## Supported installation

The audited local host is macOS arm64 with CPython 3.12; package metadata requires Python >=3.12,<3.13. The clock/supervisor also implements Linux CLOCK_BOOTTIME/POSIX support, but consult actual [M007 CI results](../reports/M007_FINAL_RELEASE_AUDIT.md) before claiming hosted qualification. Windows is not qualified. Full M005B acquisition currently requires macOS because the launcher invokes `/usr/bin/caffeinate`.

In a fresh environment, install exact pins and build/install the wheel:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-v1.txt
.venv/bin/python -m pip wheel --no-build-isolation --no-deps . --wheel-dir dist
.venv/bin/python -m pip install --no-deps dist/neuromancer-1.0.0-py3-none-any.whl
.venv/bin/python -m pip check
.venv/bin/python -c 'import numpy,brian2,scipy,pytest; print(numpy.__version__,brian2.__version__,scipy.__version__,pytest.__version__)'
```

Expected versions: NumPy2.5.4, Brian2 2.10.1, SciPy1.18.0, pytest9.1.1. `requirements-v1.txt` includes all original `requirements-m002.txt` pins and the verification-only SciPy pin. No original version upgrade is part of reproduction. Core runtime is Brian2/NumPy; the diagnostic CLI (including smoke) requires the declared Matplotlib diagnostic extra. Use the full research stack for all modules, plots and tests. The package remains1.0.0; no1.0tag has been published.

## Smoke example and software tests

```sh
.venv/bin/neuromancer-diagnostic --mode smoke --output runs/my-smoke
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python -m pytest -q
```

Smoke uses development network0, default noise0,200ms and ten20ms steps. Expected outputs: `steps.jsonl`, `smoke.json`, `provenance.json`, `summary.json` with `status=complete`. Choose an unused output path. This is not reserved controller evaluation. M007 reports actual test/warning counts and installation details.

## Reproduce the committed scientific evidence (recommended)

```sh
.venv/bin/python scripts/reproduce_v1_evidence.py --output runs/my-evidence-reproduction
```

This bounded, evidence-only helper creates a **fresh1200s current-boot deadline**, or inherits an enclosing deadline when one is explicitly set. It reads only the committed M005B primary evidence and never calls a neural acquisition runner. Do not import historical expired deadline timestamps from a previous run or boot.

Expected output tree:

- `analysis/`: repeat-level metrics,1s time courses, network qualification and frozen scientific summary.
- `model_verification.json`: reconstructed observed events/counts, delivered actions, FIR/RLS state digests and candidate scores.
- `statistics_verification.json`: separate raw-count/target/bootstrap gate calculations.
- `figures/`: tracking/cumulative and network/cost PNG/SVG figures, sector and computation summaries.
- `commands.json`, `supervision/`, `reproduction.json`: actual commands, worker outcomes and byte comparisons.

The four canonical tables/summary files must be byte-identical to `reports/evidence/v1_finish/m005b/analysis_primary`. Figure identity is separately reported: byte equality is expected on the pinned qualified host; font/backend/OS differences can change pixels, so retain both outputs and verify identical underlying numeric tables. The original research evidence is never overwritten. For general numerical comparisons, the independently audited primary statistics agree within1e-12; FIR/weighted-batch reconstruction uses the verifier's declared2e-8 relative/absolute tolerance, while state digests and event/count/action equality are exact on the qualified stack.

Expected primary post-loss IAE: PI11.46875, RLS13.12921875, fixed MPC18.9778125Hz·s. Primary adaptive superiority is **FAIL**, despite a positive adaptive-versus-fixed comparison. Validation remains closed; locked100–119 are not read.

## Frozen model, configuration and provenance

[Protocol011](research/011_M005B_CONTROL_PROTOCOL.md) fixes the neural substrate, calibration, controller definitions,625candidates, targets, cohorts, endpoints and statistics. The acquisition source is `457491390e8d3f25ad79b5cbe44bed03975805f6`; completed V1 evidence/report revision is `6420f8529289ec31f0237eb69a705c64d8467ed7`. Operation V1's output-path repair is separately preserved; it changed no scientific arithmetic or neural data.

Primary: networks0–9/noise47,48; faults: networks0–2/noise49. Root seed20261018 and SeedSequence roles remain frozen. Parameter roles0–3 use replicate0; OU uses `(network,4,replicate,absolute1sblock)` and PCG64. Same-origin arms restore neural queues/clocks/filter/cursors and share absolute-time exogenous noise. Different feedback arms diverge afterward. Repeats average within network before10,000paired network-bootstrap draws with PCG64seed20261105; bins are not independent networks.

Every trial has51s calibration and13×64s primary branches. LOSS changes hidden efficacy from1 to.6 at16s of control. Target=original calibration baseline+1Hz. Raw1s observed E80 rate is the primary statistic;20ms counts remain archived. Primary scoring is the full16–64s window. Integration100µs, actuation/observation20ms, planning1s. No future observations, evaluator gain or sham data enter controllers.

See [evidence schema](V1_EVIDENCE_SCHEMA.md), source/config/seed hashes and `release_manifest.json` under `reports/evidence/v1_finish`. M007 verifies historical snapshots before intentionally updating README/this guide; authorized documentation changes are recorded separately, never treated as numerical amendments.

## Fresh acquisition is a different operation

The current audit does **not** authorize rerunning the complete study. A future authorized reproduction must first qualify environment, source, current-boot clock, resource forecast and unique output roots. Do not run acquisition merely to regenerate figures or tables.

For an independently authorized fresh run on the supported host, the existing CLI is `python -m neuromancer.m005b_study acquire --phase primary --output NEW_ROOT/primary`, followed by `python reports/evidence/v1_finish/finish_development.py --root NEW_ROOT`. These commands are intentionally not part of the evidence-only quickstart. They preserve the frozen10,800s development cap including faults and conditional5,400s validation cap; analysis uses2,400s. Validation requires development gates to pass. Locked100–119 require independent authorization and remain absent from this runner.

The source records16s partial segments and complete markers only after full branches/trials. Failed attempts, unfavorable outcomes and partial files must remain; no replacement seeds, target clipping or retrospective budget extension. Budget expiry or boot/clock mismatch is failure, not completion. The original successful workload measured5639.339s primary and509.778s faults on the reported M5 host, not a portable runtime guarantee. Limits:3scientific workers,<2GiB/worker,750MiB new evidence,1.2GiB combined. Nominal1s monitoring had measured overhead; inspect actual cadence. Suspend consumes the deadline, but user-space cannot enforce cleanup while asleep. No physical sleep test or hard-real-time guarantee is asserted.

Thread environment variables request BLAS limits; they do not establish actual thread count. Bitwise reproducibility is qualified only within the reported stack/platform. No biological, plasticity, hardware-safe or broad controller-generalization claim follows from successful reproduction.
