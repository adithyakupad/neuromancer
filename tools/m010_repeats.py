"""Frozen20timely/5late failure-fixture repeats, independently watchdog bounded."""
import json
from pathlib import Path
import subprocess
import sys

from neuromancer.supervisor import Deadline, atomic_json

sys.path.insert(0, str(Path("tests").resolve()))
from supervisor_test_support import communicate

root = Path(sys.argv[1])
root.mkdir(parents=True, exist_ok=False)
deadline = Deadline.after(240)
conditions = ["fixed_failure"] * 20 + ["late_failure"] * 5
atomic_json(root / "manifest.json", dict(conditions=conditions, deadline_ns=deadline.end_ns,
    clock_id=deadline.clock_id, source_revision=subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip()))
rows = []
for index, condition in enumerate(conditions):
    deadline.check()
    folder = root / f"{index:02}_{condition}"
    folder.mkdir()
    process = subprocess.Popen([sys.executable, "tools/m010_case.py", str(folder), condition],
                               start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = communicate(process, folder)
    if process.returncode:
        raise RuntimeError(f"Repeat failed in{folder}; retain all evidence")
    result = json.loads((folder / "returned.json").read_text())
    expected = "WORKER_FAILURE" if condition == "fixed_failure" else "DEADLINE_EXCEEDED"
    rows.append(dict(index=index, condition=condition, status=result["status"]))
    atomic_json(root / "outcomes.json", rows)
    assert result["status"] == expected
atomic_json(root / "complete.json", dict(trials=len(rows), remaining_s=deadline.remaining()))
print(json.dumps(rows))
