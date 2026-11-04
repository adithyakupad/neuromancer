"""Preregistered25-case diagnostic bank; every repeat and outcome retained."""
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
conditions = (["original"] * 5 + ["filesystem_error"] * 5
              + ["python_exception"] * 3 + ["caught_exit"] * 3
              + ["traceback_delay"] * 2 + ["normal_exit"] * 3
              + ["operation_delay"] * 2 + ["shutdown_delay"] * 2)
sources = ["tools/m010_worker.py", "tools/m010_case.py", "tools/m010_diagnose.py",
           "src/neuromancer/supervisor.py", "src/neuromancer/clocks.py",
           "tests/supervisor_worker.py", "tests/supervisor_timing.py"]
atomic_json(root / "manifest.json", dict(conditions=conditions,
    deadline_ns=deadline.end_ns, clock_id=deadline.clock_id,
    source_revision=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    sources={p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
    thread_requests={p: os.environ.get(p) for p in
                     ("VECLIB_MAXIMUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")}))
rows = []
os.environ["M008_WORKER_TRACE"] = "1"
for index, condition in enumerate(conditions):
    deadline.check()
    folder = root / f"{index:02}_{condition}"
    folder.mkdir()
    process = subprocess.Popen([sys.executable, "tools/m010_case.py", str(folder), condition],
                               start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = communicate(process, folder)
    if process.returncode:
        raise RuntimeError(f"Diagnostic/cleanup failure in{folder}; retain outputs")
    result = json.loads((folder / "returned.json").read_text())
    rows.append(dict(index=index, condition=condition, status=result["status"],
                     cleanup_verified=result["cleanup_verified"]))
    atomic_json(root / "outcomes.json", rows)
    if condition == "normal_exit":
        assert result["status"] == "COMPLETED"
    elif condition in ("traceback_delay", "operation_delay", "shutdown_delay"):
        assert result["status"] == "DEADLINE_EXCEEDED"
    elif condition == "caught_exit":
        assert result["status"] == "WORKER_FAILURE"
    else:
        assert result["status"] in ("WORKER_FAILURE", "DEADLINE_EXCEEDED")
atomic_json(root / "complete.json", dict(trials=len(rows), remaining_s=deadline.remaining()))
print(json.dumps(rows))
