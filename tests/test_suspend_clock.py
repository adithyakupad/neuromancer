"""Clock semantics and resume policy; physical machine sleep is never automated."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

import pytest
from neuromancer import clocks
from neuromancer.supervisor import Deadline, supervise


def test_native_clock_bracketing_and_integer_ticks():
    c=clocks.get_clock();samples=[c.sample() for _ in range(100)]
    assert all(a['continuous_ns']<=b['continuous_ns'] for a,b in zip(samples,samples[1:]))
    assert all(s['continuous_ns']>=s['active_ns'] for s in samples)
    assert all(s['clock_id']==c.domain for s in samples)
    clocks.check_reading(2**63,2**63+100,2**63+40,2**62,None)


def test_expected_suspend_is_not_clock_failure():
    old=(1000,1005,800)
    clocks.check_reading(11000,11005,11002,810,old)
    # Forward/backward wall adjustments never appear in the consistency input.
    for wall in (-10**30,10**30):
        assert isinstance(wall,int)
        clocks.check_reading(11000,11005,11002,810,old)


@pytest.mark.parametrize('reading',[(900,905,902,810),(1100,1105,2000,810),
    (1100,1105,1102,799),(1100,1105,1102,2000),(-1,5,0,0)])
def test_unreliable_clocks_fail_closed(reading):
    with pytest.raises(clocks.ClockError):clocks.check_reading(*reading,(1000,1005,800))


def test_clock_domain_and_boot_mixing_rejects(monkeypatch):
    with pytest.raises(TypeError):Deadline(123)
    with pytest.raises(clocks.ClockError):Deadline(123,'legacy-uptime')
    d=Deadline.after(1)
    monkeypatch.setenv('NEUROMANCER_DEADLINE_NS',str(d.end_ns))
    monkeypatch.setenv('NEUROMANCER_DEADLINE_CLOCK',d.clock_id)
    assert Deadline.from_environment()==d
    monkeypatch.setenv('NEUROMANCER_DEADLINE_CLOCK',d.clock_id+'foreign-boot')
    with pytest.raises(clocks.ClockError):Deadline.from_environment()


def test_wall_steps_do_not_move_deadline(monkeypatch):
    d=Deadline.after(1);end=d.end_ns
    monkeypatch.setattr(time,'time_ns',lambda:10**30)
    d.check();assert d.end_ns==end
    monkeypatch.setattr(time,'time_ns',lambda:-10**30)
    d.check();assert d.end_ns==end


def test_frozen_active_clock_but_advancing_continuous(monkeypatch):
    import neuromancer.supervisor as s
    tick=1000
    monkeypatch.setattr(s,'now_ns',lambda:tick)
    d=Deadline.after(1)
    tick+=500000000;d.check()
    tick=d.end_ns
    with pytest.raises(TimeoutError):d.check()
    assert d.remaining()==0


@pytest.mark.parametrize('mode',['short_suspend','expired_suspend','expired_suspend_descendant','clock_failure'])
def test_real_workers_after_injected_resume(tmp_path,mode):
    worker=Path(__file__).with_name('supervisor_worker.py')
    code='''
import json,sys,time
from pathlib import Path
import neuromancer.supervisor as s
from neuromancer.clocks import ClockError
p=Path(sys.argv[1]);mode=sys.argv[2];native=s.now_ns;active=time.monotonic_ns
started=active();triggered=False;resume_at=None
def injected():
 global triggered,resume_at
 if active()-started>350000000:
  triggered=True
  if mode=='clock_failure':raise ClockError('injected API inconsistency')
  value=native()+(10000000000 if mode.startswith('expired_suspend') else 200000000)
  if resume_at is None:resume_at=value
  return value
 return native()
s.now_ns=injected
d=s.Deadline.after(1.8)
command=[sys.executable,sys.argv[3],'descendant' if mode.endswith('descendant') else 'ignore_term',str(p/'worker')]
r=s.supervise([command],p/'supervision',d)
r['injection_triggered']=triggered
r['injected_resume_ns']=resume_at
r['real_active_elapsed_s']=(active()-started)/1e9
(p/'returned.json').write_text(json.dumps(r))
'''
    p=subprocess.Popen([sys.executable,'-c',code,str(tmp_path),mode,str(worker)],
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=p.communicate(timeout=6)
    except subprocess.TimeoutExpired:
        for f in tmp_path.rglob('pid.json'):
            try:os.killpg(json.loads(f.read_text())['pgid'],signal.SIGKILL)
            except ProcessLookupError:pass
        os.killpg(p.pid,signal.SIGKILL);p.communicate(timeout=1)
        pytest.fail('Outer watchdog intervened')
    assert p.returncode==0,err.decode()
    r=json.loads((tmp_path/'returned.json').read_text())
    assert r['injection_triggered'] and r['cleanup_verified'],r
    assert r['status']==('CLOCK_FAILURE' if mode=='clock_failure' else 'DEADLINE_EXCEEDED')
    assert (tmp_path/'worker/partial.txt').read_text()=='completed checkpoint\n'
    states=[e['state'] for e in r['workers'][0]['events']]
    assert 'TERMINATING' in states and states[-1]=='REAPED'
    if not mode.endswith('descendant'):assert 'KILLING' in states
    if mode.startswith('expired_suspend'):
        assert r['post_deadline_cleanup']
        assert r['real_active_elapsed_s']<1.5
        assert r['finished_ns']>r['deadline_ns'] # elapsed deadline remains expired.
        first_stop=next(e['monotonic_ns'] for e in r['workers'][0]['events'] if e['state']=='STOP_REQUESTED')
        assert 0<=first_stop-r['injected_resume_ns']<100000000
    if mode=='short_suspend':assert not r['post_deadline_cleanup']
    pid=r['workers'][0]['pid']
    # Repeating cleanup is harmless after the owned group is gone.
    from neuromancer.supervisor import _signal,group_exists
    assert _signal(pid,signal.SIGTERM) is None
    assert _signal(pid,signal.SIGKILL) is None
    assert not group_exists(pid)
    with pytest.raises(ProcessLookupError):os.kill(pid,0)
    for f in (tmp_path/'worker').rglob('pid.json'):
        with pytest.raises(ProcessLookupError):os.kill(json.loads(f.read_text())['pid'],0)


def test_unavailable_api_does_not_fall_back(monkeypatch):
    monkeypatch.setattr(clocks,'_clock',None)
    def missing():raise OSError('missing platform API')
    monkeypatch.setattr(clocks,'SuspendClock',missing)
    with pytest.raises(clocks.ClockError):clocks.get_clock()
    assert clocks._clock is None


def test_clock_inconsistency_is_latched():
    c=clocks.SuspendClock();original=c._reference
    c._reference=lambda:0
    with pytest.raises(clocks.ClockError):c.sample()
    c._reference=original
    with pytest.raises(clocks.ClockError):c.sample()


def test_nested_acquisition_does_not_reset_deadline(tmp_path,monkeypatch):
    import neuromancer.control_experiment as c
    d=Deadline.after(2)
    monkeypatch.setenv('NEUROMANCER_DEADLINE_NS',str(d.end_ns))
    monkeypatch.setenv('NEUROMANCER_DEADLINE_CLOCK',d.clock_id)
    monkeypatch.setattr(c,'provenance',lambda:{'fixture':True})
    def fake(commands,output,deadline):
        assert deadline==d and all(command[-1]==str(d.end_ns) for command in commands)
        return dict(status='DEADLINE_EXCEEDED')
    monkeypatch.setattr(c,'supervise',fake)
    monkeypatch.setattr(sys,'argv',['fixture','--stage','TUNE','--output',str(tmp_path/'output')])
    with pytest.raises(SystemExit):c.main()


@pytest.mark.parametrize('fault',['clock_failure','late_publication'])
def test_clock_failure_at_final_publication(tmp_path,monkeypatch,fault):
    import neuromancer.supervisor as s
    d=Deadline.after(1);original=s.atomic_json;real=s.now_ns;published=False
    def write(path,value):
        nonlocal published
        original(path,value)
        if path.name=='terminal.json':published=True
    def clock():
        if published:
            if fault=='clock_failure':raise clocks.ClockError('injected final reading failure')
            return d.end_ns+1
        return real()
    monkeypatch.setattr(s,'atomic_json',write);monkeypatch.setattr(s,'now_ns',clock)
    result=s.supervise([],tmp_path/'owned',d)
    expected='CLOCK_FAILURE' if fault=='clock_failure' else 'DEADLINE_EXCEEDED'
    assert result['status']==expected
    assert json.loads((tmp_path/'owned/terminal.json').read_text())['status']==expected
