"""One original-budget subprocess diagnostic, called under an outer watchdog."""
import json
from pathlib import Path
import resource
import sys

from neuromancer.supervisor import Deadline, supervise

resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
root = Path(sys.argv[1])
mode = sys.argv[2]
deadline = Deadline.after(1.8)
cutoff = deadline.end_ns - 800_000_000
if mode == "original":
    command = [sys.executable, "tests/supervisor_worker.py", "write_failure",
               str(root / "worker"), str(cutoff)]
else:
    command = [sys.executable, "tools/m010_worker.py", mode, str(root / "worker")]
result = supervise([command], root / "supervision", deadline, trace=True)
(root / "returned.json").write_text(json.dumps(result, indent=2) + "\n")
rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
rss_bytes = rss if sys.platform == "darwin" else rss * 1024
(root / "memory.json").write_text(json.dumps(dict(child_peak_rss_bytes=rss_bytes)))
assert rss_bytes <= 1024**3
assert result["cleanup_verified"] and result["finished_ns"] <= result["deadline_ns"]
