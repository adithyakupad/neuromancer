"""Qualification of the exact M026 authorization and synthetic PID publication."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest

from neuromancer.clocks import clock_domain, now_ns


def test_unauthorized_change_to_authorized_fixture_is_rejected(monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts/m017_reproduce.py"
    verify_history = runpy.run_path(str(script))["verify_history"]
    read_bytes = Path.read_bytes

    def edited_fixture(path):
        original = read_bytes(path)
        if path == Path("tests/supervisor_worker.py"):
            return original + b"\n# Unauthorized follow-up edit.\n"
        return original

    monkeypatch.setattr(Path, "read_bytes", edited_fixture)
    with pytest.raises(AssertionError, match=r"Protected baseline path differs: tests/supervisor_worker\.py"):
        verify_history()


WORKER_DRIVER = """
import json
import os
from pathlib import Path
import runpy
import sys

worker, folder, mode = sys.argv[1:]
sys.path.insert(0, str(Path(worker).parent))
sys.argv = [worker, 'complete', folder]
write_text = Path.write_text
replace = Path.replace

def checked_write(path, data, *args, **kwargs):
    if path.name == 'pid.json.tmp' and mode == 'interrupt':
        write_text(path, data[:5], *args, **kwargs)
        os._exit(73)
    return write_text(path, data, *args, **kwargs)

def checked_replace(path, destination):
    if path.name == 'pid.json.tmp':
        assert not Path(destination).exists()
        assert json.loads(path.read_text())['pid'] == os.getpid()
    return replace(path, destination)

Path.write_text = checked_write
Path.replace = checked_replace
runpy.run_path(worker, run_name='__main__')
"""


@pytest.mark.parametrize("mode", ("complete", "interrupt"))
def test_pid_marker_is_visible_only_after_complete_write(tmp_path, mode):
    worker = Path(__file__).with_name("supervisor_worker.py").resolve()
    deadline_ns = now_ns() + 30_000_000_000
    env = dict(os.environ, NEUROMANCER_DEADLINE_NS=str(deadline_ns),
               NEUROMANCER_DEADLINE_CLOCK=clock_domain())
    result = subprocess.run(
        [sys.executable, "-c", WORKER_DRIVER, str(worker), str(tmp_path), mode],
        env=env, capture_output=True, timeout=15,
    )
    marker = tmp_path / "pid.json"
    staging = tmp_path / "pid.json.tmp"
    if mode == "interrupt":
        assert result.returncode == 73, result.stderr.decode()
        assert staging.read_text() == '{"pid'
        assert not marker.exists()
    else:
        assert result.returncode == 0, result.stderr.decode()
        record = json.loads(marker.read_text())
        assert record["pid"] > 0 and record["pgid"] > 0
        assert 0 < record["started_ns"] < record["deadline_ns"] == deadline_ns
        assert not staging.exists()
