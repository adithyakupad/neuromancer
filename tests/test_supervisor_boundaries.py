"""Deterministic classification tests, separate from real OS lifecycle evidence."""
import json
from pathlib import Path
import signal
import pytest
from neuromancer.clocks import ClockError
import neuromancer.supervisor as s


class Clock:
    def __init__(self):self.value=1_000_000_000;self.fail=False
    def read(self):
        if self.fail and self.value>=1_050_000_000:raise ClockError('injected discontinuity')
        return self.value
    def sleep(self,seconds):self.value+=max(1,int(seconds*1e9))


def harness(monkeypatch,exit_ns,delay_observation=False,descendant=False):
    c=Clock();processes=[];signals=[];child=[descendant]
    class Process:
        pid=101_001
        def __init__(self,*args,**kwargs):self.returncode=None;processes.append(self)
        def poll(self):
            if self.returncode is None and c.value>=exit_ns:
                # The controlled model knows exact exit_ns. Delivery to supervisor may lag.
                if delay_observation:c.value=2_010_000_000
                self.returncode=0
            return self.returncode
    def send(pid,sig):
        signals.append(sig)
        if sig==signal.SIGKILL:
            child[0]=False
            if processes[0].returncode is None:processes[0].returncode=-int(sig)
    monkeypatch.setattr(s,'now_ns',c.read);monkeypatch.setattr(s,'clock_domain',lambda:'m008.synthetic')
    monkeypatch.setattr(s.time,'sleep',c.sleep);monkeypatch.setattr(s.time,'monotonic_ns',lambda:c.value)
    monkeypatch.setattr(s.subprocess,'Popen',Process);monkeypatch.setattr(s,'group_exists',lambda pid:processes[0].returncode is None or child[0])
    monkeypatch.setattr(s,'_signal',send)
    return c,signals


@pytest.mark.parametrize('trace',[False,True])
@pytest.mark.parametrize('exit_ns,lag,expected',[
    (1_100_000_000,False,'COMPLETED'),
    (2_000_000_000,False,'DEADLINE_EXCEEDED'),
    (2_000_000_001,False,'DEADLINE_EXCEEDED'),
    (1_900_000_000,True,'DEADLINE_EXCEEDED'),
    (2_100_000_000,False,'DEADLINE_EXCEEDED'),
    (10**20,False,'DEADLINE_EXCEEDED')])
def test_cutoff_classification_exact_boundaries(tmp_path,monkeypatch,trace,exit_ns,lag,expected):
    c,signals=harness(monkeypatch,exit_ns,lag);d=s.Deadline(2_800_000_000,'m008.synthetic')
    r=s.supervise([['controlled-worker']],tmp_path/'owned',d,trace=trace)
    assert r['status']==expected and r['cleanup_verified'] and r['finished_ns']<=d.end_ns
    assert r['workers'][0]['state']=='REAPED'
    if exit_ns==10**20:assert signal.SIGTERM in signals and signal.SIGKILL in signals
    if trace:
        t=json.loads((tmp_path/'owned/lifecycle.json').read_text());assert t['events']
        assert all(e['clock_id']==d.clock_id for e in t['events'])
        observed=r['workers'][0]['first_observed_exit_ns']
        if expected=='COMPLETED':assert observed<r['work_cutoff_ns']
        else:assert observed>=r['work_cutoff_ns']


def test_trace_publication_failure_never_success(tmp_path,monkeypatch):
    harness(monkeypatch,1_100_000_000);original=s.atomic_json
    def fail(path,value):
        if path.name=='lifecycle.json':raise OSError('injected trace persistence failure')
        original(path,value)
    monkeypatch.setattr(s,'atomic_json',fail)
    r=s.supervise([['controlled']],tmp_path/'owned',s.Deadline(2_800_000_000,'m008.synthetic'),trace=True)
    assert r['status']=='SUPERVISOR_FAILURE' and r['cleanup_verified']
    assert json.loads((tmp_path/'owned/terminal.json').read_text())['status']=='SUPERVISOR_FAILURE'


def test_trace_clock_discontinuity_fail_closed(tmp_path,monkeypatch):
    c,signals=harness(monkeypatch,10**20);c.fail=True
    r=s.supervise([['controlled']],tmp_path/'owned',s.Deadline(2_800_000_000,'m008.synthetic'),trace=True)
    assert r['status']=='CLOCK_FAILURE' and r['cleanup_verified'] and r['finished_ns'] is None
    assert signal.SIGKILL in signals


def test_timely_exit_then_global_publication_expiry(tmp_path,monkeypatch):
    c,_=harness(monkeypatch,1_100_000_000);original=s.atomic_json
    def slow_publish(path,value):
        original(path,value)
        if path.name=='terminal.json':c.value=2_800_000_001
    monkeypatch.setattr(s,'atomic_json',slow_publish)
    r=s.supervise([['controlled']],tmp_path/'owned',s.Deadline(2_800_000_000,'m008.synthetic'),trace=True)
    assert r['workers'][0]['first_observed_exit_ns']<r['work_cutoff_ns']
    assert r['status']=='DEADLINE_EXCEEDED' and r['cause']=='terminal publication exceeded deadline'


def test_reaped_parent_cannot_conceal_live_descendant(tmp_path,monkeypatch):
    c,signals=harness(monkeypatch,1_100_000_000,descendant=True)
    r=s.supervise([['controlled']],tmp_path/'owned',s.Deadline(2_800_000_000,'m008.synthetic'),trace=True)
    assert r['status']=='WORKER_FAILURE' and r['cleanup_verified']
    assert r['workers'][0]['parent_reaped'] and signal.SIGKILL in signals


def test_assertion_failure_still_retains_fixture_artifacts(tmp_path):
    import os,shutil,subprocess,sys
    case=tmp_path/'isolated';case.mkdir()
    shutil.copy2(Path(__file__).with_name('conftest.py'),case/'conftest.py')
    (case/'test_supervisor.py').write_text("def test_injected_failure(tmp_path):\n (tmp_path/'returned.json').write_text('{\"status\":\"fixture-failure\"}')\n assert False, 'deliberate evidence retention test'\n")
    env=dict(os.environ,NEUROMANCER_TEST_ARTIFACTS=str(tmp_path/'retained'))
    result=subprocess.run([sys.executable,'-m','pytest','-q',str(case),'--basetemp='+str(tmp_path/'nested-temp')],capture_output=True,text=True,env=env,timeout=6)
    assert result.returncode==1,result.stdout+result.stderr
    folders=list((tmp_path/'retained').iterdir());assert len(folders)==1
    evidence=json.loads((folders[0]/'pytest_evidence.json').read_text())
    assert evidence['reports']['call']=='failed'
    assert json.loads((folders[0]/'returned.json').read_text())['status']=='fixture-failure'
