"""One bounded diagnostic trial; no neural/scientific imports beyond package clock."""
import argparse,json,os,platform,resource,sys,time
from pathlib import Path
import neuromancer.supervisor as s
from neuromancer.clocks import now_ns,clock_domain


def main():
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('condition');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CPU,(20,20));resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024*1024,16*1024*1024))
    d=s.Deadline.after(1.8);cutoff=d.end_ns-800000000
    s.atomic_json(a.output/'context.json',dict(deadline_created_ns=d.end_ns-1800000000,deadline_ns=d.end_ns,work_cutoff_ns=cutoff,clock_id=d.clock_id,condition=a.condition,python=sys.version,platform=platform.platform()))
    os.environ['M008_WORKER_TRACE']='1'
    if a.condition=='wake_delay':os.environ['M008_WAKE_DELAY_S']='.30'
    if a.condition=='import_delay':os.environ['M008_PREIMPORT_DELAY_S']='1.05'
    real_popen=s.subprocess.Popen;real_atomic=s.atomic_json;stall_done=False
    if a.condition=='parent_delay':
        def popen(*args,**kwargs):
            child=real_popen(*args,**kwargs);poll=child.poll
            def delayed_poll():
                nonlocal stall_done
                if (a.output/'worker/completion.json').exists() and not stall_done:
                    stall_done=True;before=now_ns();time.sleep(.30);s.atomic_json(a.output/'parent_stall.json',dict(before_ns=before,after_ns=now_ns(),clock_id=d.clock_id))
                return poll()
            child.poll=delayed_poll;return child
        s.subprocess.Popen=popen
    if a.condition=='persist_delay':
        def slow_atomic(path,value):
            nonlocal stall_done
            if path.name=='progress.json' and value['workers'][0]['state']=='RUNNING' and not stall_done:
                stall_done=True;before=now_ns();time.sleep(1.05);real_atomic(a.output/'parent_stall.json',dict(before_ns=before,after_ns=now_ns(),clock_id=d.clock_id))
            return real_atomic(path,value)
        s.atomic_json=slow_atomic
    mode='complete' if a.condition=='immediate' else 'before'
    command=[sys.executable,'tests/supervisor_worker.py',mode,str(a.output/'worker'),str(cutoff)]
    r=s.supervise([command],a.output/'supervision',d,trace=True)
    s.atomic_json(a.output/'returned.json',r)
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert rss<=1024**3
    assert r['cleanup_verified'] and r['finished_ns']<=r['deadline_ns'],r
    for f in (a.output/'worker').rglob('pid.json'):
        pid=json.loads(f.read_text())['pid']
        try:os.kill(pid,0)
        except ProcessLookupError:pass
        else:raise AssertionError(f'Owned PID still present: {pid}')
    s.atomic_json(a.output/'checked.json',dict(cleanup_verified=True,rss_bytes=rss,perturbation_applied=stall_done))
if __name__=='__main__':main()
