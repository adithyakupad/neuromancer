"""One original-budget subprocess diagnostic, called under an outer watchdog."""
import json
import os
from pathlib import Path
import resource
import sys
import threading
import time

from neuromancer.supervisor import Deadline, supervise, atomic_json

resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
root = Path(sys.argv[1])
mode = sys.argv[2]
deadline = Deadline.after(1.8)
if "NEUROMANCER_DEADLINE_NS" in os.environ:
    assert deadline.end_ns <= Deadline.from_environment().end_ns
cutoff = deadline.end_ns - 800_000_000
thread = None
errors = []
if mode == "original":
    command = [sys.executable, "tests/supervisor_worker.py", "write_failure",
               str(root / "worker"), str(cutoff)]
elif mode in ("fixed_failure", "late_failure"):
    command = [sys.executable, "tests/supervisor_failure_worker.py", str(root / "worker"),
               "timely" if mode == "fixed_failure" else "late"]

    def release():
        try:
            while deadline.remaining() > .8:
                ready = root / "worker" / "ready.json"
                if ready.exists():
                    value = json.loads(ready.read_text())
                    assert value["clock_id"] == deadline.clock_id
                    from neuromancer.clocks import now_ns
                    atomic_json(root / "worker" / "release.json",
                                dict(clock_id=deadline.clock_id, released_ns=now_ns()))
                    return
                time.sleep(.001)
            errors.append("Release missed original work cutoff")
        except Exception as error:
            errors.append(repr(error))

    thread = threading.Thread(target=release, daemon=True)
    thread.start()
else:
    command = [sys.executable, "tools/m010_worker.py", mode, str(root / "worker")]
result = supervise([command], root / "supervision", deadline, trace=True)
(root / "returned.json").write_text(json.dumps(result, indent=2) + "\n")
if thread is not None:
    thread.join(timeout=.1)
    atomic_json(root / "release_driver.json", dict(errors=errors, alive=thread.is_alive()))
    assert not errors and not thread.is_alive()
rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
rss_bytes = rss if sys.platform == "darwin" else rss * 1024
(root / "memory.json").write_text(json.dumps(dict(child_peak_rss_bytes=rss_bytes)))
assert rss_bytes <= 1024**3
assert result["cleanup_verified"] and result["finished_ns"] <= result["deadline_ns"]
