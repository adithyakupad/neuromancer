"""Readability candidate qualification, one1200s budget; no study acquisition."""
import os
import sys
from pathlib import Path

from neuromancer.supervisor import Deadline, atomic_json, supervise


def main():
    root = Path("reports/engineering/evidence/personal_style/final")
    root.mkdir(parents=True, exist_ok=False)
    deadline = Deadline.after(1200)
    python = sys.executable
    os.environ.update(VECLIB_MAXIMUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                      OMP_NUM_THREADS="1", MPLCONFIGDIR="/tmp/neuromancer-style-mpl",
                      NEUROMANCER_TEST_ARTIFACTS=str(root / "test_artifacts"))
    commands = [
        [python, "-m", "pip", "check"],
        [python, "-m", "pytest", "-q", f"--basetemp={root / 'test_tmp'}",
         f"--junitxml={root / 'tests.xml'}"],
        [python, "tools/personal_style_probe.py", str(root / "probe"), "--neural",
         "--reference", "reports/engineering/evidence/personal_style/reference"],
        [python, "scripts/reproduce_v1_evidence.py", "--output", str(root / "scientific_reproduction")],
        [python, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", ".",
         "--wheel-dir", str(root / "wheel")],
    ]
    atomic_json(root / "commands.json", commands)
    result = supervise(commands, root / "supervision", deadline, workers=1)
    atomic_json(root / "status.json", dict(status=result["status"], remaining_s=deadline.remaining()))
    if result["status"] != "COMPLETED":
        raise RuntimeError("Qualification incomplete; preserve every failure and partial artifact")
    print(result["status"])


if __name__ == "__main__":
    main()
