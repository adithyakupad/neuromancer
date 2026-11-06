"""Reproduce M013/M014 summaries from copies and check the V2 historical archive."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

MANIFEST = Path("reports/engineering/evidence/m017/base_preservation.json")
STYLE_PATHS = {
    "src/neuromancer/control.py", "src/neuromancer/identify.py",
    "src/neuromancer/online_identify.py", "src/neuromancer/predictive.py",
    "src/neuromancer/predictive_planner.py", "src/neuromancer/plasticity.py",
    "src/neuromancer/functional_learning.py", "src/neuromancer/reservoir.py",
    "src/neuromancer/causal_memory.py", "src/neuromancer/neural_io.py",
    "src/neuromancer/cl_adapter.py", "src/neuromancer/cl_response_source.py",
    "scripts/m013_pilot.py", "scripts/m014_pilot.py", "scripts/m015_memory.py",
    "scripts/m016_run.py", "scripts/m013_analyze.py", "scripts/m014_analyze.py",
}


def verify_history():
    protected = json.loads(MANIFEST.read_text())["protected_sha256"]
    for name, expected in protected.items():
        path = Path(name)
        data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            if name not in STYLE_PATHS and name != "scripts/m016_verify.py":
                raise AssertionError(f"Protected baseline path differs: {name}")
    return len(protected)


def main(output):
    result = {"audited_paths": verify_history(), "archives": {}}
    for stage, folder, script in (
        ("m013", "pilot_typed", "m013_analyze.py"),
        ("m014", "pilot", "m014_analyze.py"),
    ):
        source = Path("reports/research/evidence") / stage / folder
        scratch = output / stage
        shutil.copytree(source, scratch)
        subprocess.run([sys.executable, f"scripts/{script}", str(scratch)], check=True)
        original = json.loads((source / "independent_analysis.json").read_text())
        reproduced = json.loads((scratch / "independent_analysis.json").read_text())
        assert original == reproduced, stage
        result["archives"][stage] = reproduced
    (output / "reproduction.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
