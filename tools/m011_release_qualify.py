"""Independently qualify the unchanged V1 commit, not optional engineering source."""
import json
import os
from pathlib import Path
import subprocess
import sys

from neuromancer.supervisor import Deadline, atomic_json, supervise

BASE = "86ad99f6956c76a5bb6d169e21544684f57c9270"
SOURCE = os.environ.get("M011_EXPECTED_SOURCE", BASE)
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=False)
tools = Path(__file__).resolve().parent
reference = tools.parent / "reports/engineering/evidence/m011/isolated_v1/release/reference"
assert subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == SOURCE
assert not subprocess.check_output(["git", "diff", "--name-only", SOURCE])
for name in Path("src/neuromancer").glob("*.py"):
    assert name.read_bytes() == subprocess.check_output(["git", "show", f"{BASE}:{name}"]), str(name)
deadline = Deadline.after(1200)
python = sys.executable
os.environ.update(VECLIB_MAXIMUM_THREADS="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1",
                  M008_WORKER_TRACE="1", MPLCONFIGDIR="/tmp/neuromancer-m011-v1-mpl",
                  NEUROMANCER_TEST_ARTIFACTS=str(output / "test_artifacts"))
commands = [
    [python, "-m", "pip", "check"],
    [python, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", ".", "--wheel-dir", str(output / "wheel")],
    ["/usr/bin/env", "-u", "PYTHONPATH", python, "-m", "pip", "install", "--no-deps", "--force-reinstall", str(output / "wheel/neuromancer-1.0.0-py3-none-any.whl")],
    ["/usr/bin/env", "-u", "PYTHONPATH", python, str(tools / "m011_installed_check.py"), str(output)],
    ["/usr/bin/env", "-u", "PYTHONPATH", str(Path(python).parent / "neuromancer-diagnostic"),
     "--mode", "smoke", "--output", str(output / "installed_smoke")],
    [python, str(tools / "m011_v1_probe.py"), str(output / "probe"), "--neural", "--reference", str(reference)],
    [python, "scripts/reproduce_v1_evidence.py", "--output", str(output / "reproduction")],
    [python, "-m", "pytest", "-q", f"--basetemp={output / 'pytest_tmp'}", f"--junitxml={output / 'tests.xml'}"],
    [python, str(tools / "m011_original_repeats.py"), str(output / "original_repeats")],
]
atomic_json(output / "manifest.json", dict(source=SOURCE, commands=commands,
    harness_sha256={str(path):__import__('hashlib').sha256(path.read_bytes()).hexdigest()
                   for path in tools.glob("m011*.py")}))
results = []
for index, command in enumerate(commands):
    deadline.check()
    result = supervise([command], output / f"stage_{index:02}", deadline, workers=1)
    results.append(dict(index=index, status=result["status"], command=command))
    atomic_json(output / "stage_results.json", results)
    if not result["cleanup_verified"]:
        raise RuntimeError("Unsafe cleanup; stop qualification")
all_passed = all(row["status"] == "COMPLETED" for row in results)
atomic_json(output / "status.json", dict(status="PASS" if all_passed else "HOLD",
    source=SOURCE, remaining_s=deadline.remaining(), stages=results))
print("PASS" if all_passed else "HOLD")
