"""Analyze all existing M010 samples. This script does NOT run a benchmark."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

output = Path(sys.argv[1])
output.mkdir(parents=True, exist_ok=False)
root = Path("reports/engineering/evidence/m010")
rng = np.random.default_rng(20261111)
result = {}
source_hashes = {}
for bank in ("performance", "performance_serialized"):
    folder = root / bank
    manifest = json.loads((folder / "manifest.json").read_text())
    source_hashes[str(folder / "manifest.json")] = hashlib.sha256((folder / "manifest.json").read_bytes()).hexdigest()
    cases = []
    for case in manifest["cases"]:
        # Resolve preserved metadata by basename, not old absolute acquisition paths.
        path = folder / Path(case["output"]).name / "measurements.json"
        record = json.loads(path.read_text())
        source_hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        assert record["exact_equivalence"]
        cases.append(dict(**case, measurement=record))
    workloads = {}
    for name in cases[0]["measurement"]["timings"]:
        arrays = {}
        summaries = {}
        for version in ("reference", "current"):
            selected = [case for case in cases if case["version"] == version]
            wall = np.array([case["measurement"]["timings"][name]["wall_ns"] for case in selected]) / 1e6
            cpu = np.array([case["measurement"]["timings"][name]["cpu_ns"] for case in selected]) / 1e6
            assert wall.shape == cpu.shape == (6, 9)
            arrays[version] = wall
            summaries[version] = dict(processes=6, samples=54,
                wall_median_ms=float(np.median(wall)), wall_p95_ms=float(np.quantile(wall, .95)),
                wall_max_ms=float(wall.max()), cpu_median_ms=float(np.median(cpu)),
                cpu_p95_ms=float(np.quantile(cpu, .95)), wall_minus_cpu_max_ms=float((wall-cpu).max()),
                first_measured_median_ms=float(np.median(wall[:, 0])),
                later_measured_median_ms=float(np.median(wall[:, 1:])))
        # Whole-cycle bootstrap preserves within-process repeated samples and ABBA
        # ordering. Only THREE cycles exist: interval resolution is very limited.
        cycle_samples = {}
        for version in arrays:
            cycle_samples[version] = np.array([
                [case["measurement"]["timings"][name]["wall_ns"] for case in cases
                 if case["cycle"] == cycle and case["version"] == version]
                for cycle in range(3)]) / 1e6
        draws = rng.integers(0, 3, (10000, 3))
        ratios = []
        for draw in draws:
            reference = cycle_samples["reference"][draw].ravel()
            current = cycle_samples["current"][draw].ravel()
            ratios.append(np.quantile(current, .95) / np.quantile(reference, .95))
        point = summaries["current"]["wall_p95_ms"] / summaries["reference"]["wall_p95_ms"]
        workloads[name] = dict(**summaries, p95_ratio=point,
            descriptive_cycle_bootstrap95=np.quantile(ratios, [.025, .975]).tolist(),
            cycle_ratios=[float(np.quantile(cycle_samples['current'][cycle], .95) /
                                np.quantile(cycle_samples['reference'][cycle], .95)) for cycle in range(3)],
            existing_frozen_gate_unchanged=json.loads((folder / "comparison.json").read_text())["workloads"][name]["passed"])
    result[bank] = dict(workloads=workloads, all_samples_included=True, new_benchmark=False,
        processes=12, cycles=3, samples_per_source_per_workload=54)
(output / "analysis.json").write_text(json.dumps(dict(banks=result, source_sha256=source_hashes,
    bootstrap_seed=20261111, draws=10000, interpretation="descriptive only; no replacement gate"), indent=2) + "\n")
print("PASS: existing samples analyzed without exclusions or new benchmark acquisition")
