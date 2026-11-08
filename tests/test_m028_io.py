import json
import numpy as np
import pytest

from tools import m028_io


def test_durable_append_and_exact_reconstruction(tmp_path):
    path=tmp_path/'progress.json'
    rows=[dict(step=0,radius=1e-8)]
    m028_io.atomic_json(path,dict(checkpoints=rows,completed_branches=0))
    rows.append(dict(step=50,radius=1e-7))
    m028_io.atomic_json(path,dict(checkpoints=rows,completed_branches=0))
    result=m028_io.load_progress(path)
    assert result['checkpoints']==rows and result['checkpoint_count']==2
    assert len(path.read_bytes())<600


def test_failed_pointer_preserves_committed_prefix_and_tail(tmp_path,monkeypatch):
    path=tmp_path/'progress.json'
    rows=[dict(step=0)]
    m028_io.atomic_json(path,dict(checkpoints=rows))
    original=path.read_bytes()
    def failure(*args):raise OSError('injected pointer publication failure')
    monkeypatch.setattr(m028_io,'durable_json',failure)
    rows.append(dict(step=50))
    with pytest.raises(OSError):m028_io.atomic_json(path,dict(checkpoints=rows))
    assert path.read_bytes()==original
    assert m028_io.load_progress(path)['checkpoints']==rows[:1]
    assert b'50' in path.with_name('checkpoints.jsonl').read_bytes()
    with pytest.raises(ValueError,match='tail preserved'):
        m028_io.atomic_json(path,dict(checkpoints=rows))


def test_corrupt_ledger_cannot_be_accepted(tmp_path):
    path=tmp_path/'progress.json'
    m028_io.atomic_json(path,dict(checkpoints=[dict(step=0)]))
    ledger=path.with_name('checkpoints.jsonl')
    ledger.write_bytes(ledger.read_bytes().replace(b'0',b'1'))
    with pytest.raises(ValueError,match='integrity'):
        m028_io.load_progress(path)
