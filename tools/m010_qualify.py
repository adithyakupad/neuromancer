"""Focused or full M010 qualification; fixed shared deadlines, no study acquisition."""
import argparse
import os
from pathlib import Path
import sys

from neuromancer.supervisor import Deadline, atomic_json, supervise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("focused", "full"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = args.output
    root.mkdir(parents=True, exist_ok=False)
    deadline = Deadline.after(120 if args.phase == "focused" else 1200)
    python = sys.executable
    os.environ.update(M008_WORKER_TRACE="1", MPLCONFIGDIR="/tmp/neuromancer-m010-mpl",
                      VECLIB_MAXIMUM_THREADS="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1",
                      NEUROMANCER_TEST_ARTIFACTS=str(root / "test_artifacts"))
    pytest = [python, "-m", "pytest", "-q", f"--basetemp={root / 'test_tmp'}",
              f"--junitxml={root / 'tests.xml'}"]
    if args.phase == "focused":
        commands = [pytest + ["tests/test_supervisor.py", "tests/test_supervisor_boundaries.py",
                              "tests/test_suspend_clock.py"],
                    [python, "tools/m010_repeats.py", str(root / "repeats")]]
    else:
        commands = [[python, "-m", "pip", "check"], pytest,
                    [python, "tools/personal_style_probe.py", str(root / "probe"), "--neural",
                     "--reference", "reports/engineering/evidence/personal_style/reference"],
                    [python, "scripts/reproduce_v1_evidence.py", "--output", str(root / "reproduction")],
                    [python, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", ".",
                     "--wheel-dir", str(root / "wheel")]]
    atomic_json(root / "commands.json", commands)
    result = supervise(commands, root / "supervision", deadline, workers=1)
    atomic_json(root / "status.json", dict(status=result["status"], remaining_s=deadline.remaining()))
    if result["status"] != "COMPLETED":
        raise RuntimeError("M010 qualification incomplete; retain partials and failure")
    print(result["status"])


if __name__ == "__main__":
    main()
