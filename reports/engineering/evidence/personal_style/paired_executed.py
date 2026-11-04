"""Fixed three-cycle ABBA readability benchmark, one worker and600s total."""
import json
import os
import sys
from pathlib import Path

from neuromancer.supervisor import Deadline, atomic_json, supervise

root = Path("/tmp/neuromancer-style-paired")
root.mkdir(exist_ok=False)
deadline = Deadline.after(600)
commands = []
manifest = []
for cycle in range(3):
    for position, version in enumerate(("original", "candidate", "candidate", "original")):
        output = root / f"cycle{cycle}_{position}_{version}"
        command = ["/usr/bin/env", f"PYTHONPATH=/tmp/neuromancer-style-{version}/src",
                   sys.executable, "/tmp/neuromancer_style_probe.py", str(output),
                   "--neural", "--reference", "/tmp/neuromancer-style-reference-probe"]
        commands.append(command)
        manifest.append(dict(cycle=cycle, position=position, version=version,
                             output=str(output), command=command))
atomic_json(root / "manifest.json", manifest)
result = supervise(commands, root / "supervision", deadline, workers=1)
atomic_json(root / "status.json", dict(status=result["status"], remaining_s=deadline.remaining()))
if result["status"] != "COMPLETED":
    raise RuntimeError("Incomplete benchmark; preserve every partial output")
print(result["status"])
