"""Independent M010 source and process-artifact verification; no acquisition."""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess

BASE = "72824e6cb48e714e11a398f2787146099daec397"


def preservation():
    allowed = {"tests/test_supervisor.py", ".github/workflows/ci.yml",
               ".github/workflows/v1-qualification.yml"}
    changes = {}
    count = 0
    for row in subprocess.check_output(["git", "ls-tree", "-rz", BASE]).split(b"\0"):
        if not row:
            continue
        metadata, name = row.split(b"\t", 1)
        path = Path(name.decode())
        assert path.exists() or path.is_symlink(), str(path)
        data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        count += 1
        if hashlib.sha1(blob).hexdigest() != metadata.split()[2].decode():
            assert str(path) in allowed, str(path)
            changes[str(path)] = hashlib.sha256(data).hexdigest()
    assert set(changes) == allowed
    return dict(status="PASS", base=BASE, checked_files=count, unchanged_files=count-len(changes),
                changes=changes, production_and_historical_evidence="byte-identical")


def trials(root, kind, live_groups):
    rows = []
    manifest = json.loads((root / "manifest.json").read_text())
    for name, expected in manifest.get("sources", {}).items():
        recorded_source = subprocess.check_output(
            ["git", "show", f"{manifest['source_revision']}:{name}"])
        assert hashlib.sha256(recorded_source).hexdigest() == expected, name
    expected_count = 25
    assert len(manifest["conditions"]) == expected_count
    outcomes = json.loads((root / "outcomes.json").read_text())
    assert len(outcomes) == expected_count
    for index, condition in enumerate(manifest["conditions"]):
        path = root / f"{index:02}_{condition}"
        result = json.loads((path / "returned.json").read_text())
        terminal = json.loads((path / "supervision/terminal.json").read_text())
        outer = json.loads((path / "outer_watchdog.json").read_text())
        assert result == terminal
        assert outer["watchdog_intervened"] is False and outer["returncode"] == 0
        assert result["cleanup_verified"] and result["finished_ns"] <= result["deadline_ns"]
        assert result["deadline_ns"] - result["work_cutoff_ns"] == 800_000_000
        worker = result["workers"][0]
        assert worker["state"] == "REAPED" and worker["parent_reaped"]
        assert (path / "worker/partial.txt").read_text() == "completed checkpoint\n"
        events = [json.loads(line) for line in (path / "worker/events.jsonl").read_text().splitlines()]
        assert all(event["clock_id"] == result["deadline_clock_id"] for event in events)
        times = {event["kind"]: event["monotonic_ns"] for event in events}
        assert result["started_ns"] <= min(times.values()) <= max(times.values())
        if kind == "repeats":
            report = json.loads((path / "worker/failure.json").read_text())
            release = json.loads((path / "worker/release.json").read_text())
            assert report["errno"] == errno.ENOTDIR and report["exception_type"] == "NotADirectoryError"
            assert report["scientific_success"] is False
            assert report["clock_id"] == release["clock_id"] == result["deadline_clock_id"]
            assert times["ready"] <= release["released_ns"] <= times["release_seen"]
            assert times["release_seen"] <= report["operation_ns"] <= report["caught_ns"]
            assert report["caught_ns"] <= times["failure_record_written"] < result["work_cutoff_ns"]
            assert not (path / "worker/completion.json").exists()
            if condition == "fixed_failure":
                assert result["status"] == "WORKER_FAILURE" and worker["returncode"] == 23
                assert times["failure_record_written"] <= times["failure_exit_intent"]
                assert times["failure_exit_intent"] <= worker["first_observed_exit_ns"] < result["work_cutoff_ns"]
                assert worker["events"][-1]["monotonic_ns"] < result["work_cutoff_ns"]
            else:
                assert condition == "late_failure" and result["status"] == "DEADLINE_EXCEEDED"
                assert worker["returncode"] == -15
                assert worker["first_observed_exit_ns"] >= result["work_cutoff_ns"]
        else:
            if condition == "normal_exit":
                assert result["status"] == "COMPLETED"
            elif condition.endswith("delay"):
                assert result["status"] == "DEADLINE_EXCEEDED"
            elif condition == "caught_exit":
                assert result["status"] == "WORKER_FAILURE"
            else:
                assert result["status"] in ("WORKER_FAILURE", "DEADLINE_EXCEEDED")
        if live_groups:
            for pgid in (worker["pgid"], outer["supervisor_pid"]):
                try:
                    os.killpg(pgid, 0)
                except ProcessLookupError:
                    pass
                else:
                    raise AssertionError(f"Owned group still exists:{pgid}")
        rows.append(dict(index=index, condition=condition, status=result["status"],
            worker_returncode=worker["returncode"],
            exit_margin_ms=(result["work_cutoff_ns"]-worker["first_observed_exit_ns"])/1e6,
            elapsed_ms=(result["finished_ns"]-result["started_ns"])/1e6,
            events_ms={name: (stamp-result["started_ns"])/1e6 for name, stamp in times.items()}))
    return dict(status="PASS", trials=len(rows), live_group_check=live_groups, rows=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("preservation", "diagnostics", "repeats"))
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--live-groups", action="store_true")
    args = parser.parse_args()
    result = preservation() if args.kind == "preservation" else trials(args.root, args.kind, args.live_groups)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}))


if __name__ == "__main__":
    main()
