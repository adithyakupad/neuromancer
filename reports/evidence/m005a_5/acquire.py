"""Only the prospectively enumerated missing trials; unchanged scientific worker."""
import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
from neuromancer.clocks import now_ns,clock_domain,ClockError
from neuromancer.supervisor import Deadline,supervise,atomic_json
from neuromancer.diagnostic import provenance
ROOT=Path(__file__).resolve().parent

def inner():
    d=Deadline.from_environment();plan=json.loads((ROOT/'plan.json').read_text());raw=ROOT/'continuation'
    raw.mkdir(exist_ok=False);pairs=plan['missing'];names=plan['names']
    assert len(pairs)==17 and len(set(map(tuple,pairs)))==17
    meta=provenance();meta.update(stage='CONFIRM',names=names,replicates=[41,42],networks=list(range(10)),trial_pairs=pairs,
        started_monotonic_ns=int(os.environ['M005A_CAPTURE_BEGIN_NS']),started_epoch_s=float(os.environ['M005A_CAPTURE_EPOCH']),
        deadline_monotonic_ns=d.end_ns,deadline_clock_id=d.clock_id,wall_limit_s=4800,simulated_seconds=5219,
        protocol_sha256=hashlib.sha256(Path('docs/research/009_M005A_CONTROL_PROTOCOL.md').read_bytes()).hexdigest(),
        selection_sha256=plan['selection_sha256'],selection_revision=plan['selection_revision'],amendment='docs/research/011_M005A_5_CONFIRMATION_CONTINUATION.md')
    atomic_json(raw/'provenance.json',meta)
    commands=[[sys.executable,'-m','neuromancer.control_experiment','--worker',str(n),str(r),str(raw),json.dumps(names),str(d.end_ns)] for n,r in pairs]
    result=supervise(commands,raw/'supervision',d,workers=3)
    if result['status']!='COMPLETED':raise SystemExit('Nonqualifying acquisition: '+result['status'])
    trials=[json.loads((raw/f'n{n}_r{r}'/'trial.json').read_text()) for n,r in pairs]
    assert all(t['status']=='complete' and len(t['branches'])==8 and t['peak_rss_bytes']<2*1024**3 for t in trials)
    d.check();atomic_json(raw/'summary.json',dict(status='complete',trial_pairs=pairs,trials=trials,wall_ns=now_ns()-meta['started_monotonic_ns']))
    d.check()

def capture():
    began=now_ns();epoch=time.time();d=Deadline(began+4800*10**9,clock_domain())
    plan=json.loads((ROOT/'plan.json').read_text())
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert not subprocess.check_output(['git','status','--porcelain'],text=True).strip()
    assert hashlib.sha256(Path('reports/evidence/m005a_3/tuning_analysis/selection.json').read_bytes()).hexdigest()==plan['selection_sha256']
    env=dict(os.environ,NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id,M005A_CAPTURE_BEGIN_NS=str(began),M005A_CAPTURE_EPOCH=str(epoch))
    command=[sys.executable,str(Path(__file__).resolve()),'--inner'];reason=None;proc=None;awake=None
    with (ROOT/'acquisition.log').open('wb') as log:
        proc=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        awake=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(proc.pid)])
        atomic_json(ROOT/'acquisition_launch.json',dict(head=head,pid=proc.pid,command=command,selection_sha256=plan['selection_sha256'],selection_revision=plan['selection_revision'],started_ns=began,epoch_s=epoch,deadline_ns=d.end_ns,clock_id=d.clock_id))
        stop_sent=False
        try:
            while proc.poll() is None:
                current=now_ns()
                raw=ROOT/'continuation';progress=raw/'supervision/progress.json'
                if progress.exists():
                    workers=json.loads(progress.read_text())['workers'];pids=[w['pid'] for w in workers if w.get('pid') and not w.get('terminal')];rss={}
                    if pids:
                        out=subprocess.run(['ps','-o','pid=,rss=','-p',','.join(map(str,pids))],capture_output=True,text=True,timeout=2)
                        rss={int(line.split()[0]):int(line.split()[1])*1024 for line in out.stdout.splitlines()}
                    trials=[json.loads(f.read_text()) for f in raw.glob('n*_r*/trial.json')]
                    roots=list(Path('reports/evidence').glob('m005a*'))+list(Path('runs').glob('m005a-*'))
                    allocation=sum(f.stat().st_blocks*512 for root in roots for f in root.rglob('*') if f.is_file() and not f.is_symlink())
                    sample=dict(ns=current,clock_id=d.clock_id,elapsed_s=(current-began)/1e9,epoch_s=time.time(),completed=len(trials),rss_bytes=rss,allocated_bytes=allocation,peak_rss_bytes=max([t['peak_rss_bytes'] for t in trials],default=0),faults=[str(f) for f in raw.glob('n*_r*/failure.json')])
                    with (ROOT/'resource_samples.jsonl').open('a') as stream:stream.write(json.dumps(sample)+'\n');stream.flush()
                    if allocation>500*1024**2 or max(rss.values(),default=0)>=2*1024**3 or sample['peak_rss_bytes']>=2*1024**3 or sample['faults']:
                        reason='Resource/worker fault';raise RuntimeError(reason)
                if (current-began)/1e9>4805:raise TimeoutError('Outer cleanup-only watchdog')
                time.sleep(.5 if current>=d.end_ns else 5)
        except BaseException as exc:
            reason=repr(exc);os.killpg(proc.pid,signal.SIGINT);stop_sent=True
            try:proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                progress=ROOT/'continuation/supervision/progress.json'
                if progress.exists():
                    for w in json.loads(progress.read_text())['workers']:
                        if w.get('pgid'):
                            try:os.killpg(w['pgid'],signal.SIGKILL)
                            except ProcessLookupError:pass
                os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=1)
        finally:
            awake.terminate()
            try:awake.wait(timeout=1)
            except subprocess.TimeoutExpired:awake.kill();awake.wait(timeout=1)
    try:finish=now_ns()
    except ClockError as exc:finish=None;reason=repr(exc)
    end=time.time()
    result=dict(status='COMPLETE' if proc.returncode==0 and reason is None and finish is not None and finish<=d.end_ns else 'PARTIAL',returncode=proc.returncode,reason=reason,started_ns=began,finished_ns=finish,elapsed_s=(finish-began)/1e9 if finish is not None else None,calendar_s=end-epoch,deadline_ns=d.end_ns,clock_id=d.clock_id,head=head)
    atomic_json(ROOT/'acquisition_closure.json',result);print(json.dumps(result),flush=True)
    if result['status']!='COMPLETE':raise SystemExit(1)

if __name__=='__main__':
    if sys.argv[1:]==['--inner']:inner()
    else:capture()
