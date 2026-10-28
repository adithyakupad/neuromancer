"""Real subprocess supervisor tests, independently watchdog-bounded."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest
from neuromancer.supervisor import Deadline, atomic_json

WORKER = Path(__file__).with_name('supervisor_worker.py')


def test_deadline_shared_and_calendar_independent(monkeypatch):
    now = 100
    monkeypatch.setattr(time, 'monotonic_ns', lambda: now)
    d = Deadline.after(1)
    assert d.end_ns == 1000000100
    monkeypatch.setattr(time, 'time', lambda: -1e20)
    now = d.end_ns-1; d.check()
    now += 1
    with pytest.raises(TimeoutError): d.check()
    assert d.remaining() == 0
    with pytest.raises(ValueError): Deadline.after(float('nan'))


def test_atomic_artifact_survives_failed_replace(tmp_path, monkeypatch):
    p = tmp_path/'checkpoint.json'; atomic_json(p, {'version':1})
    def fail(*args): raise OSError('injected replacement failure')
    monkeypatch.setattr(os, 'replace', fail)
    with pytest.raises(OSError): atomic_json(p, {'version':2})
    assert json.loads(p.read_text()) == {'version':1}


@pytest.mark.parametrize('mode', ['complete','timeout','cooperative','ignore_stop',
    'ignore_term','shutdown_block','exception','unexpected','descendant','orphan',
    'write_failure','before','race'])
def test_real_worker_lifecycle(tmp_path, mode):
    # The test process is an independent outer watchdog. Its fallback addresses
    # each recorded owned group, not just the supervisor session.
    code = '''
import json, sys
from pathlib import Path
from neuromancer.supervisor import Deadline, supervise
root=Path(sys.argv[1]); mode=sys.argv[2]; worker=sys.argv[3]
d=Deadline.after(1.8)
cutoff=d.end_ns-800000000
command=[sys.executable,worker,mode,str(root/'worker'),str(cutoff)]
r=supervise([command],root/'supervision',d)
(root/'returned.json').write_text(json.dumps(r))
'''
    p = subprocess.Popen([sys.executable,'-c',code,str(tmp_path),mode,str(WORKER)],
                         start_new_session=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    began=time.monotonic()
    try:
        stdout,stderr=p.communicate(timeout=6)
    except subprocess.TimeoutExpired:
        for f in tmp_path.rglob('pid.json'):
            pgid=json.loads(f.read_text())['pgid']
            try: os.killpg(pgid,signal.SIGKILL)
            except ProcessLookupError: pass
        os.killpg(p.pid,signal.SIGKILL);p.communicate(timeout=1)
        pytest.fail('Independent outer watchdog intervened')
    assert p.returncode == 0,stderr.decode()
    r=json.loads((tmp_path/'returned.json').read_text())
    assert time.monotonic()-began < 4
    assert (tmp_path/'worker'/'partial.txt').read_text() == 'completed checkpoint\n'
    if mode in ('complete','before'):
        assert r['status']=='COMPLETED'
    elif mode in ('exception','unexpected','write_failure','orphan'):
        assert r['status'] in ('WORKER_FAILURE','CLEANUP_FAILURE')
    else:
        assert r['status']=='DEADLINE_EXCEEDED',r
    if mode != 'orphan':
        assert r['cleanup_verified'],r
        assert r['workers'][0]['state']=='REAPED'
    assert r['finished_ns'] <= r['deadline_ns'],r
    if mode in ('ignore_term','shutdown_block'):
        assert 'KILLING' in [e['state'] for e in r['workers'][0]['events']]
    # Independent process-table check includes descendants, separately from leader.
    table=subprocess.check_output(['ps','-axo','pid=,stat='],text=True)
    states={int(line.split()[0]):line.split()[1] for line in table.splitlines()}
    for f in tmp_path.rglob('pid.json'):
        pid=json.loads(f.read_text())['pid']
        assert pid not in states or states[pid].startswith('Z'),(pid,states.get(pid))
    if mode=='orphan' and r['status']=='CLEANUP_FAILURE':
        assert not r['cleanup_verified']  # Never pretend an unreaped group is gone.


def test_supervisor_failure_cleanup_and_restart(tmp_path):
    code = """
import sys,json
from pathlib import Path
import neuromancer.supervisor as s
p=Path(sys.argv[1]); original=s.atomic_json; count=0
def injected(path,value):
 global count
 count+=1
 if count==2: raise OSError('injected progress write failure')
 return original(path,value)
s.atomic_json=injected
r=s.supervise([[sys.executable,sys.argv[2],'ignore_term',str(p/'worker')]],p/'owned',s.Deadline.after(2))
(p/'returned.json').write_text(json.dumps(r))
try: s.supervise([],p/'owned',s.Deadline.after(1))
except FileExistsError: (p/'restart_rejected').touch()
"""
    proc=subprocess.Popen([sys.executable,'-c',code,str(tmp_path),str(WORKER)],
                          start_new_session=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try: out,err=proc.communicate(timeout=6)
    except subprocess.TimeoutExpired:
        for f in tmp_path.rglob('pid.json'):
            try: os.killpg(json.loads(f.read_text())['pgid'],signal.SIGKILL)
            except ProcessLookupError: pass
        os.killpg(proc.pid,signal.SIGKILL);proc.communicate(timeout=1)
        pytest.fail('Outer watchdog intervened')
    assert proc.returncode==0,err.decode()
    result=json.loads((tmp_path/'returned.json').read_text())
    assert result['status']=='SUPERVISOR_FAILURE' and result['cleanup_verified']
    assert result['persistence_errors'] and (tmp_path/'restart_rejected').exists()


def test_final_artifact_failure_never_success(tmp_path,monkeypatch,capsys):
    import neuromancer.supervisor as s
    original=s.atomic_json
    def fail_terminal(path,value):
        if path.name=='terminal.json': raise OSError('injected terminal write failure')
        return original(path,value)
    monkeypatch.setattr(s,'atomic_json',fail_terminal)
    result=s.supervise([],tmp_path/'owned',Deadline.after(1))
    assert result['status']=='SUPERVISOR_FAILURE'
    assert 'SUPERVISOR_FAILURE' in capsys.readouterr().err
    assert (tmp_path/'owned'/'progress.json').exists()


def test_nested_stages_use_remaining_deadline(tmp_path):
    from neuromancer.supervisor import supervise
    d=Deadline.after(1)
    first=supervise([],tmp_path/'first',d)
    time.sleep(.21)
    second=supervise([],tmp_path/'second',d)
    assert first['deadline_ns']==second['deadline_ns']==d.end_ns
    assert second['status']=='DEADLINE_EXCEEDED'


def test_multiworker_shared_budget_with_queue(tmp_path):
    code='''
import json,sys
from pathlib import Path
from neuromancer.supervisor import Deadline,supervise
p=Path(sys.argv[1]);w=sys.argv[2];d=Deadline.after(1.8)
commands=[[sys.executable,w,'ignore_term',str(p/f'worker{i}')] for i in range(5)]
r=supervise(commands,p/'supervision',d,workers=2)
(p/'returned.json').write_text(json.dumps(r))
'''
    p=subprocess.Popen([sys.executable,'-c',code,str(tmp_path),str(WORKER)],
                       start_new_session=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try: stdout,stderr=p.communicate(timeout=6)
    except subprocess.TimeoutExpired:
        for f in tmp_path.rglob('pid.json'):
            try: os.killpg(json.loads(f.read_text())['pgid'],signal.SIGKILL)
            except ProcessLookupError: pass
        os.killpg(p.pid,signal.SIGKILL);p.communicate(timeout=1)
        pytest.fail('Outer watchdog intervened')
    assert p.returncode==0,stderr.decode()
    r=json.loads((tmp_path/'returned.json').read_text())
    assert r['status']=='DEADLINE_EXCEEDED' and r['cleanup_verified']
    assert [w['terminal'] for w in r['workers']].count('NOT_STARTED')==3
    assert [w['terminal'] for w in r['workers']].count('FORCED_TERMINATION')==2
    for f in tmp_path.rglob('pid.json'):
        info=json.loads(f.read_text());assert info['deadline_ns']==r['deadline_ns']
        with pytest.raises(ProcessLookupError): os.kill(info['pid'],0)
    assert r['finished_ns']<=r['deadline_ns']


def test_acquisition_uses_supervisor_fail_closed(tmp_path,monkeypatch):
    import neuromancer.control_experiment as c
    def fake(commands,output,deadline):
        assert len(commands)==10
        assert all(int(command[-1])==deadline.end_ns for command in commands)
        assert [int(command[4]) for command in commands]==list(range(10))
        assert all(command[5]=='40' for command in commands)
        assert 3598 < deadline.remaining() <= 3600
        return dict(status='DEADLINE_EXCEEDED')
    monkeypatch.setattr(c,'supervise',fake)
    monkeypatch.setattr(c,'provenance',lambda:{'fixture':True})
    output=tmp_path/'acquisition'
    monkeypatch.setattr(sys,'argv',['fixture','--stage','TUNE','--output',str(output)])
    with pytest.raises(SystemExit): c.main()
    assert json.loads((output/'resource_stop.json').read_text())['status']=='DEADLINE_EXCEEDED'
    assert not (output/'summary.json').exists()


def test_atomic_neural_archive_preservation(tmp_path,monkeypatch):
    import numpy as np
    from neuromancer.control_experiment import _save_npz
    path=tmp_path/'fixture.npz';data=np.arange(20)
    _save_npz(path,counts=data)
    def fail(*args): raise OSError('injected archive publication failure')
    monkeypatch.setattr(os,'replace',fail)
    with pytest.raises(OSError): _save_npz(path,counts=data+1)
    np.testing.assert_array_equal(np.load(path)['counts'],data)
    assert (tmp_path/'fixture.npz.tmp').exists()


def test_cleanup_failure_is_explicit(tmp_path):
    code='''
import json,sys
from pathlib import Path
import neuromancer.supervisor as s
p=Path(sys.argv[1]);s.group_exists=lambda pgid: True
r=s.supervise([[sys.executable,sys.argv[2],'ignore_term',str(p/'worker')]],p/'supervision',s.Deadline.after(1.8))
(p/'returned.json').write_text(json.dumps(r))
'''
    proc=subprocess.Popen([sys.executable,'-c',code,str(tmp_path),str(WORKER)],
                          start_new_session=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try: out,err=proc.communicate(timeout=6)
    except subprocess.TimeoutExpired:
        for f in tmp_path.rglob('pid.json'):
            try: os.killpg(json.loads(f.read_text())['pgid'],signal.SIGKILL)
            except ProcessLookupError: pass
        os.killpg(proc.pid,signal.SIGKILL);proc.communicate(timeout=1)
        pytest.fail('Outer watchdog intervened')
    assert proc.returncode==0,err.decode()
    r=json.loads((tmp_path/'returned.json').read_text())
    assert r['status']=='CLEANUP_FAILURE' and r['cause']=='DEADLINE_EXCEEDED'
    assert not r['cleanup_verified'] and r['workers'][0]['terminal']=='CLEANUP_FAILURE'
    assert r['workers'][0]['parent_reaped']
    with pytest.raises(ProcessLookupError): os.kill(r['workers'][0]['pid'],0)
