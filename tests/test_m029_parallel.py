import json

import pytest

from tools import m029_parallel as parallel
from tools import m028_io


@pytest.fixture
def artifacts(tmp_path, monkeypatch):
    branch = [0, 47, 'STATIC_RLS-MPC']
    rows = [dict(network=0, replicate=47, branch=branch[2], step=i) for i in range(0, 3200, 50)]
    rows.append(dict(network=0, replicate=47, branch=branch[2], completed=True))
    denominators = dict(count=3200, minimum_lower=.999)
    monkeypatch.setattr(m028_io, 'EXTRA_PROGRESS', denominators)
    m028_io.atomic_json(tmp_path/'progress.json', dict(checkpoints=rows, completed_branches=1))
    (tmp_path/'backend.json').write_text(json.dumps(dict(denominators=denominators)))
    certificate = dict(stage_pass=True, failure=None, completed_branches=1, prescribed_branches=1,
                       checkpoints=rows, maximum_coefficient_radius=.001, maximum_covariance_radius=.001,
                       digest_differences=0, timings={key: dict(calls=3200) for key in
                       ('information_update', 'native_update', 'state_residual', 'digest')})
    certificate['timings']['planner_certificate'] = dict(calls=64)
    (tmp_path/'certificate.json').write_text(json.dumps(certificate))
    worker = dict(branch=branch, source='source', pid=1, pgid=1, deadline_ns=100, clock_id='clock',
                  kernel_sha256='kernel', returncode=0, started_ns=15, finished_ns=20,
                  sha256={name: parallel.sha(tmp_path/name) for name in parallel.FILES})
    (tmp_path/'worker.json').write_text(json.dumps(worker))
    record = dict(pid=1, pgid=1, terminal='COMPLETED', parent_reaped=True,
                  events=[dict(state='RUNNING', monotonic_ns=12)])
    result = dict(started_ns=10, work_cutoff_ns=90, deadline_ns=100, deadline_clock_id='clock')
    return tmp_path, branch, record, result


def verify(artifacts):
    output, branch, record, result = artifacts
    return parallel.verify_worker(output, branch, 'source', record, result, 'kernel')


def test_canonical_manifest():
    assert len(parallel.manifest()) == 40
    assert parallel.manifest()[0] == [0, 47, 'STATIC_RLS-MPC']


def test_complete_branch(artifacts):
    assert verify(artifacts)['plans'] == 64


@pytest.mark.parametrize('problem', ['tail', 'hash', 'unreaped', 'wrong-branch', 'partial'])
def test_reject_corrupted_or_incomplete_worker(artifacts, problem):
    output, branch, record, _ = artifacts
    if problem in ('tail', 'hash'):
        ledger = output/'checkpoints.jsonl'
        with ledger.open('a') as stream:
            stream.write('{}\n')
        if problem == 'tail':
            worker = parallel.read(output/'worker.json')
            worker['sha256'][ledger.name] = parallel.sha(ledger)
            (output/'worker.json').write_text(json.dumps(worker))
    elif problem == 'unreaped':
        record['parent_reaped'] = False
    elif problem == 'wrong-branch':
        branch[-1] = 'LOSS_RLS-MPC'
    else:
        (output/'certificate.json').unlink()
    with pytest.raises((OSError, ValueError)):
        verify(artifacts)
