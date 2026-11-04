"""Independent source-isolation and persistence-artifact checks, never acquisition."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

V1 = "86ad99f6956c76a5bb6d169e21544684f57c9270"
LICENSED = "c7012fc4d002a9904abbb68a21a554e11e78d570"


def tree(revision):
    entries = {}
    for row in subprocess.check_output(["git", "ls-tree", "-rz", revision]).split(b"\0"):
        if row:
            metadata, name = row.split(b"\t", 1)
            entries[name.decode()] = metadata.split()[2].decode()
    return entries


def isolation(worktree):
    old = tree(LICENSED)
    release = tree(V1)
    permitted = {"src/neuromancer/supervisor.py", "tests/supervisor_worker.py",
                 "tests/test_supervisor.py", "tests/test_calibration.py",
                 ".github/workflows/ci.yml", ".github/workflows/v1-qualification.yml"}
    changed = {name for name in old if old[name] != release.get(name)}
    assert changed == permitted
    assert "tests/supervisor_failure_worker.py" not in release
    assert "docs/development/CODING_STYLE.md" not in release
    for name in ("src/neuromancer/supervisor.py", "tests/test_supervisor.py",
                 "tests/supervisor_worker.py", "tests/supervisor_handshake_worker.py"):
        assert release[name] == tree("08a956ce")[name]
    for optional in ("ce147866", "72824e6c", "4a8e91ee"):
        assert subprocess.run(["git", "merge-base", "--is-ancestor", optional, V1]).returncode == 1
    assert subprocess.check_output(["git", "-C", str(worktree), "rev-parse", "HEAD"], text=True).strip() == V1
    assert not subprocess.check_output(["git", "-C", str(worktree), "status", "--porcelain"])
    checked = 0
    for name, expected in release.items():
        path = worktree / name
        data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        assert actual == expected, name
        checked += 1
    return dict(status="PASS", candidate=V1, physical_files_checked=checked,
                licensed_base=LICENSED, changed_existing_paths=sorted(changed),
                scientific_implementation_and_evidence="unchanged from licensed V1",
                M010_fixture_and_optional_style_and_performance="excluded")


def persistence(root, live_groups):
    manifest = json.loads((root / "manifest.json").read_text())
    outcomes = json.loads((root / "outcomes.json").read_text())
    assert len(manifest["conditions"]) == len(outcomes) == 20
    for name, digest in manifest["sources"].items():
        data = subprocess.check_output(["git", "show", f"{manifest['source_revision']}:{name}"])
        assert hashlib.sha256(data).hexdigest() == digest
    rows = []
    for index, condition in enumerate(manifest["conditions"]):
        folder = root / f"{index:02}_{condition}"
        result = json.loads((folder / "returned.json").read_text())
        observer = json.loads((folder / "observer.json").read_text())
        events = json.loads((folder / "component_events.json").read_text())
        outer = json.loads((folder / "outer_watchdog.json").read_text())
        assert observer["dropped_stage_events"] == 0 and not observer["thread_alive"]
        assert not outer["watchdog_intervened"] and result["cleanup_verified"]
        assert all(row["clock_id"] == result["deadline_clock_id"] for row in events)
        assert result["deadline_ns"] - result["work_cutoff_ns"] == 800_000_000
        payload = (folder / "initial_payload.json").read_text()
        assert hashlib.sha256(payload.encode()).hexdigest() == observer["initial_payload_sha256"]
        writes = [row for row in events if row["kind"] == "write_begin"]
        assert sum(row["characters"] for row in writes) == len(payload)
        assert len(writes) == sum(row["kind"] == "write_end" for row in events)
        streamed = [json.loads(line) for line in (folder / "outer_stdout.log").read_text().splitlines()]
        assert all(row in events for row in streamed)
        durations = {}
        for phase in ("file_create", "serialization_with_writes", "flush", "fsync", "close", "replace"):
            begin = [row for row in events if row["kind"] == phase + "_begin"]
            end = [row for row in events if row["kind"] == phase + "_end"]
            assert len(begin) == len(end) == 1
            a, b = begin[0], end[0]
            assert a["ns"] <= b["ns"]
            durations[phase] = dict(wall_ms=(b["ns"]-a["ns"])/1e6,
                cpu_ms=(b["cpu_ns"]-a["cpu_ns"])/1e6,
                voluntary_switches=b["voluntary"]-a["voluntary"],
                involuntary_switches=b["involuntary"]-a["involuntary"])
        if condition != "ordinary":
            assert result["status"] == "DEADLINE_EXCEEDED"
        else:
            assert result["status"] in ("WORKER_FAILURE", "DEADLINE_EXCEEDED")
        if live_groups:
            groups = [outer["supervisor_pid"]] + [row["pgid"] for row in result["workers"] if "pgid" in row]
            for group in groups:
                try:
                    os.killpg(group, 0)
                except ProcessLookupError:
                    pass
                else:
                    raise AssertionError(f"Owned group still exists:{group}")
        rows.append(dict(index=index, condition=condition, status=result["status"],
            operation_executed=(folder / "worker/failure.json").exists(), components=durations,
            resource_deadline_exceeded=result["finished_ns"] > result["deadline_ns"],
            cleanup_verified=result["cleanup_verified"]))
    return dict(status="PASS", cases=20, rows=rows, live_group_check=live_groups,
                meaning="diagnostic integrity, not a universal timely-success qualification")


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("kind", choices=("isolation", "persistence"))
parser.add_argument("source", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--live-groups", action="store_true")
args = parser.parse_args()
result = isolation(args.source) if args.kind == "isolation" else persistence(args.source, args.live_groups)
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({key:value for key, value in result.items() if key != "rows"}))
