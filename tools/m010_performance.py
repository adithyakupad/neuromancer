"""Fixed three-cycle ABBA preservation benchmark; no optimization or study data."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

import numpy as np
from neuromancer.supervisor import Deadline, atomic_json, supervise

BASE = "72824e6cb48e714e11a398f2787146099daec397"
root = Path(sys.argv[1]).resolve()
root.mkdir(parents=True, exist_ok=False)
deadline = Deadline.after(600)
reference = root / "reference_source"
reference.mkdir()
archive = subprocess.check_output(["git", "archive", BASE, "src/neuromancer"])
with tarfile.open(fileobj=io.BytesIO(archive)) as source:
    source.extractall(reference, filter="data")
hashes = {}
for original in (reference / "src/neuromancer").glob("*.py"):
    current = Path("src/neuromancer") / original.name
    assert original.read_bytes() == current.read_bytes(), str(current)
    hashes[str(current)] = hashlib.sha256(current.read_bytes()).hexdigest()
commands = []
manifest = []
for cycle in range(3):
    for position, version in enumerate(("reference", "current", "current", "reference")):
        output = root / f"cycle{cycle}_{position}_{version}"
        source = reference / "src" if version == "reference" else Path("src").resolve()
        command = ["/usr/bin/env", f"PYTHONPATH={source}", sys.executable,
                   "tools/personal_style_probe.py", str(output), "--neural", "--reference",
                   "reports/engineering/evidence/personal_style/reference"]
        commands.append(command)
        manifest.append(dict(cycle=cycle, position=position, version=version,
                             output=str(output), command=command))
atomic_json(root / "manifest.json", dict(base=BASE, cases=manifest, source_hashes=hashes))
result = supervise(commands, root / "supervision", deadline, workers=1)
atomic_json(root / "status.json", dict(status=result["status"], remaining_s=deadline.remaining()))
if result["status"] != "COMPLETED":
    raise RuntimeError("Benchmark incomplete; retain failures and partials")
for item in manifest:
    item["measurements"] = json.loads((Path(item["output"]) / "measurements.json").read_text())
    assert item["measurements"]["exact_equivalence"]
comparisons = {}
for name in manifest[0]["measurements"]["timings"]:
    groups = {kind: np.concatenate([item["measurements"]["timings"][name]["wall_ns"]
               for item in manifest if item["version"] == kind]) / 1e6
               for kind in ("reference", "current")}
    summary = {kind: dict(p50_ms=float(np.median(values)), p95_ms=float(np.quantile(values, .95)),
                         max_ms=float(values.max()), samples=len(values))
               for kind, values in groups.items()}
    median = summary["current"]["p50_ms"] / summary["reference"]["p50_ms"]
    p95 = summary["current"]["p95_ms"] / summary["reference"]["p95_ms"]
    comparisons[name] = dict(**summary, median_ratio=median, p95_ratio=p95,
                             passed=median <= 1.1 and p95 <= 1.2)
rss = {kind: [item["measurements"]["max_rss_native_units"] for item in manifest
              if item["version"] == kind] for kind in ("reference", "current")}
rss_ratio = max(rss["current"]) / max(rss["reference"])
rss_bytes = max(rss["current"]) if sys.platform == "darwin" else max(rss["current"]) * 1024
passed = all(value["passed"] for value in comparisons.values()) and rss_ratio <= 1.1 and rss_bytes <= 2 * 1024**3
atomic_json(root / "comparison.json", dict(workloads=comparisons, rss_native_units=rss,
    rss_max_ratio=rss_ratio, current_max_rss_bytes=rss_bytes, all_exact=True, passed=passed))
assert passed, "Prespecified performance bound failed; retain all samples"
print("PASS: exact outputs and prespecified performance bounds")
