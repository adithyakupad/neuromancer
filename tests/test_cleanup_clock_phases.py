"""Controlled lifecycle evidence. Real process qualification remains separate."""
import json
from pathlib import Path
import signal

import pytest

import neuromancer.supervisor as supervisor
from neuromancer.clocks import ClockError


PHASES = (
    'before_readiness',
    'after_readiness',
    'during_cancellation',
    'before_descendant_reaping',
    'after_cleanup_verification',
)


def controlled_supervision(monkeypatch, tmp_path, phase, fault, kill_delay_ns=1_000_000):
    """Run the actual supervisor with separately controlled elapsed and active time."""
    state = dict(active_ns=1_000_000_000, offset_ns=0, triggered=False,
                 unreliable=False, ready=False, terminated=False, reaped=False,
                 kill_at=None, signals=[], observations=[])
    original_publish = supervisor.atomic_json
    original_touch = Path.touch

    def trigger(boundary):
        if boundary != phase or state['triggered']:
            return
        state['triggered'] = True
        state['observations'].append(dict(boundary=boundary, active_ns=state['active_ns']))
        if fault == 'forward_suspend':
            state['offset_ns'] = 10_000_000_000
        elif fault == 'clock_error':
            state['unreliable'] = True

    def read_clock():
        if state['unreliable']:
            raise ClockError('injected qualified-clock inconsistency')
        return state['active_ns'] + state['offset_ns']

    def advance(seconds):
        state['active_ns'] += max(1, int(seconds * 1e9))

    class Process:
        pid = 101_001

        def __init__(self, *args, **kwargs):
            self.returncode = None
            state['ready'] = True
            trigger('after_readiness')

        def poll(self):
            if phase == 'after_cleanup_verification' and state['active_ns'] >= 1_100_000_000:
                self.returncode = 0
                state['terminated'] = True
            if state['kill_at'] is not None and state['active_ns'] >= state['kill_at'] + kill_delay_ns:
                self.returncode = -int(signal.SIGKILL)
            if self.returncode is not None:
                state['reaped'] = True
            return self.returncode

    def send_group(pid, sig):
        state['signals'].append(int(sig))
        if sig == signal.SIGTERM:
            trigger('before_descendant_reaping')
        if sig == signal.SIGKILL:
            state['terminated'] = True
            state['kill_at'] = state['active_ns']

    def publish(path, value):
        original_publish(path, value)
        if path.name == 'progress.json' and not state['ready']:
            trigger('before_readiness')
        if path.name == 'terminal.json':
            trigger('after_cleanup_verification')

    def touch(path, *args, **kwargs):
        result = original_touch(path, *args, **kwargs)
        if path.name == 'stop-0':
            trigger('during_cancellation')
        return result

    monkeypatch.setattr(supervisor, 'now_ns', read_clock)
    monkeypatch.setattr(supervisor, 'clock_domain', lambda: 'resolution.controlled')
    monkeypatch.setattr(supervisor.time, 'monotonic_ns', lambda: state['active_ns'])
    monkeypatch.setattr(supervisor.time, 'sleep', advance)
    monkeypatch.setattr(supervisor.subprocess, 'Popen', Process)
    monkeypatch.setattr(supervisor, 'group_exists', lambda pid: not state['reaped'])
    monkeypatch.setattr(supervisor, '_signal', send_group)
    monkeypatch.setattr(supervisor, 'atomic_json', publish)
    monkeypatch.setattr(Path, 'touch', touch)
    deadline = supervisor.Deadline(2_800_000_000, 'resolution.controlled')
    result = supervisor.supervise([['controlled-parent-and-descendant']], tmp_path/'owned', deadline)
    (tmp_path/'scenario-result.json').write_text(json.dumps(dict(state=state, result=result), indent=2))
    assert result['deadline_ns'] == 2_800_000_000
    return result, state


@pytest.mark.parametrize('phase', PHASES)
@pytest.mark.parametrize('fault', ('forward_suspend', 'clock_error'))
def test_clock_transition_at_lifecycle_phase(monkeypatch, tmp_path, phase, fault):
    result, state = controlled_supervision(monkeypatch, tmp_path, phase, fault)
    assert state['triggered']
    if fault == 'clock_error':
        assert result['status'] == 'CLOCK_FAILURE'
        assert result['cleanup_verified']
        assert result['finished_ns'] is None
    elif phase in ('during_cancellation', 'before_descendant_reaping'):
        assert result['status'] == 'CLEANUP_FAILURE'
        assert result['cause'] == 'DEADLINE_EXCEEDED'
        assert not result['cleanup_verified']
        assert state['terminated'] and not state['reaped']
        assert result['cleanup_deadline_ns'] == result['deadline_ns']
        assert not result['post_deadline_cleanup']
    else:
        assert result['status'] == 'DEADLINE_EXCEEDED'
        assert result['cleanup_verified']
        if phase == 'after_readiness':
            assert result['post_deadline_cleanup']
            assert result['cleanup_deadline_ns'] <= 11_000_000_000 + 800_000_000
        if phase == 'before_readiness':
            assert result['workers'][0]['terminal'] == 'NOT_STARTED'
    assert result['status'] != 'COMPLETED'


def test_ordinary_cleanup_expiry_does_not_reset_budget(monkeypatch, tmp_path):
    result, state = controlled_supervision(monkeypatch, tmp_path, 'no_injection', 'none',
                                          kill_delay_ns=500_000_000)
    assert not state['triggered'] and state['terminated'] and not state['reaped']
    assert result['status'] == 'CLEANUP_FAILURE'
    assert result['cleanup_deadline_ns'] == result['deadline_ns']
    assert result['finished_ns'] <= result['deadline_ns']


def test_normal_cleanup_reaps_parent_and_descendant(monkeypatch, tmp_path):
    result, state = controlled_supervision(monkeypatch, tmp_path, 'no_injection', 'none')
    assert not state['triggered']
    assert result['status'] == 'DEADLINE_EXCEEDED' and result['cleanup_verified']
    assert state['reaped'] and state['terminated']
    assert result['workers'][0]['parent_reaped']
