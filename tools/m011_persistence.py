"""Fixed20-case durability diagnostic; all outcomes retained, no latency rescue."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from neuromancer.supervisor import Deadline, atomic_json

sys.path.insert(0, str(Path("tests").resolve()))
from supervisor_test_support import communicate

root = Path(sys.argv[1])
root.mkdir(parents=True, exist_ok=False)
deadline = Deadline.after(240)
if "NEUROMANCER_DEADLINE_NS" in os.environ:
    parent = Deadline.from_environment()
    deadline = Deadline(min(parent.end_ns, deadline.end_ns), parent.clock_id)
conditions = ["ordinary"] * 10 + [name for stage in
    ("serialization", "write", "flush", "fsync", "replace") for name in (stage + "_delay",) * 2]
sources = ("tools/m011_persistence.py", "tools/m011_persistence_case.py",
           "src/neuromancer/supervisor.py", "src/neuromancer/clocks.py",
           "tests/supervisor_failure_worker.py")
atomic_json(root / "manifest.json", dict(conditions=conditions, clock_id=deadline.clock_id,
    deadline_ns=deadline.end_ns, source_revision=subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip(),
    sources={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in sources},
    load_average=os.getloadavg(), python=sys.version, platform=sys.platform))
rows = []
for index, condition in enumerate(conditions):
    deadline.check()
    if deadline.remaining() < 6.5:
        raise TimeoutError("Insufficient original watchdog/fixture budget")
    folder = root / f"{index:02}_{condition}"
    folder.mkdir()
    process = subprocess.Popen([sys.executable, "tools/m011_persistence_case.py", str(folder), condition],
        start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = communicate(process, folder)
    if process.returncode:
        raise RuntimeError(f"Diagnostic incomplete:{folder}; preserve all partial events")
    result = json.loads((folder / "returned.json").read_text())
    rows.append(dict(index=index, condition=condition, status=result["status"],
        operation_opportunity=(folder / "worker/failure.json").exists(),
        cleanup_verified=result["cleanup_verified"]))
    atomic_json(root / "outcomes.json", rows)
atomic_json(root / "complete.json", dict(status="DIAGNOSTICS_COMPLETE", cases=len(rows),
    all_cases_retained=True, remaining_s=deadline.remaining()))
print(json.dumps(rows))
