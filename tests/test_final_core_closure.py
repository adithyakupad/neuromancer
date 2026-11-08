"""Deterministic regression for the real suspend fixture's startup preconditions."""
import ast
from pathlib import Path

import pytest

from neuromancer.clocks import ClockError


def fixture_injection(tmp_path, mode, elapsed=400_000_000):
    """Compile the actual clock-injection function with controlled time and files."""
    source = ast.parse(Path(__file__).with_name("test_suspend_clock.py").read_text())
    test = next(node for node in source.body
                if isinstance(node, ast.FunctionDef)
                and node.name == "test_real_workers_after_injected_resume")
    code = next(ast.literal_eval(node.value) for node in test.body
                if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "code"
                        for target in node.targets))
    function = next(node for node in ast.parse(code).body
                    if isinstance(node, ast.FunctionDef) and node.name == "injected")
    state = dict(mode=mode, p=tmp_path, active=lambda: elapsed,
                 started=0, native=lambda: 1_000_000_000,
                 triggered=False, resume_at=None, ClockError=ClockError, work_cutoff_ns=2_000_000_000)
    exec(compile(ast.Module(body=[function], type_ignores=[]), "<actual suspend fixture>", "exec"), state)
    return state


@pytest.mark.parametrize("mode", ("short_suspend", "expired_suspend", "expired_suspend_descendant"))
def test_resume_waits_for_real_checkpoint_and_delayed_start(tmp_path, mode):
    state = fixture_injection(tmp_path, mode)
    assert state["injected"]() == 1_000_000_000
    assert not state["triggered"]
    # A cancelled or failed startup may leave staging files, never a checkpoint.
    worker = tmp_path / "worker"
    worker.mkdir()
    (worker / "partial.tmp").write_text("incomplete")
    assert state["injected"]() == 1_000_000_000
    assert not state["triggered"]
    (worker / "partial.txt").write_text("completed checkpoint\n")
    if mode.endswith("descendant"):
        assert state["injected"]() == 1_000_000_000
        assert not state["triggered"]
        child = worker / "child"
        child.mkdir()
        (child / "partial.txt").write_text("completed checkpoint\n")
    expected = 11_000_000_000 if mode.startswith("expired") else 1_200_000_000
    assert state["injected"]() == expected
    assert state["triggered"] and state["resume_at"] == expected


def test_ready_worker_before_elapsed_boundary_is_not_resumed_early(tmp_path):
    worker = tmp_path / "worker"
    worker.mkdir()
    (worker / "partial.txt").write_text("completed checkpoint\n")
    state = fixture_injection(tmp_path, "expired_suspend", elapsed=350_000_000)
    assert state["injected"]() == 1_000_000_000
    assert not state["triggered"]


@pytest.mark.parametrize("mode", ("clock_failure_pre_ready", "clock_failure"))
def test_startup_clock_errors_remain_fail_closed(tmp_path, mode):
    state = fixture_injection(tmp_path, mode)
    (tmp_path / "supervision").mkdir()
    (tmp_path / "supervision/progress.json").write_text("{}")
    if mode == "clock_failure":
        worker = tmp_path / "worker"
        worker.mkdir()
        (worker / "ready.json").write_text("{}")
        assert state["injected"]() == 1_000_000_000
        (worker / "partial.txt").write_text("completed checkpoint\n")
    with pytest.raises(ClockError):
        state["injected"]()
    assert state["triggered"]


def test_missed_running_phase_is_setup_failure(tmp_path):
    worker = tmp_path / "worker"
    worker.mkdir()
    (worker / "partial.txt").write_text("completed checkpoint\n")
    state = fixture_injection(tmp_path, "expired_suspend")
    state["work_cutoff_ns"] = 1_000_000_000
    with pytest.raises(RuntimeError, match="missed work cutoff"):
        state["injected"]()
