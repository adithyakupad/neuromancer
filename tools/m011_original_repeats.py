"""Ten fixed original V1 failure-test invocations; failures are never replaced."""
import json
import os
from pathlib import Path
import subprocess
import sys

from neuromancer.supervisor import Deadline, atomic_json, supervise

root = Path(sys.argv[1]).resolve()
root.mkdir(parents=True, exist_ok=False)
deadline = Deadline.after(240)
if "NEUROMANCER_DEADLINE_NS" in os.environ:
    parent = Deadline.from_environment()
    deadline = Deadline(min(deadline.end_ns, parent.end_ns), parent.clock_id)
rows = []
for index in range(10):
    deadline.check()
    folder = root / f"repeat_{index:02}"
    folder.mkdir()
    command = [sys.executable, "-m", "pytest", "-q",
               "tests/test_supervisor.py::test_real_worker_lifecycle[write_failure]",
               f"--basetemp={folder / 'tmp'}", f"--junitxml={folder / 'tests.xml'}"]
    result = supervise([command], folder / "supervision", deadline, workers=1)
    rows.append(dict(index=index, command=command, status=result["status"]))
    atomic_json(root / "outcomes.json", rows)
    if not result["cleanup_verified"]:
        raise RuntimeError("Unsafe outer cleanup; stop and retain remaining identities")
atomic_json(root / "complete.json", dict(trials=len(rows),
    all_passed=all(row["status"] == "COMPLETED" for row in rows), remaining_s=deadline.remaining()))
if not all(row["status"] == "COMPLETED" for row in rows):
    raise RuntimeError("Original isolated V1 test failed: V1 HOLD, no replacement/retry")
