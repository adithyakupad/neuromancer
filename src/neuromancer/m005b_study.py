"""Frozen M005B acquisition CLI; original scientific settings, auditable records."""
import argparse,gc,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
import numpy as np
from .supervisor import Deadline,supervise,atomic_json
from .clocks import now_ns,clock_domain,get_clock
from .substrate import Config
from .control import Policy
from .predictive import initialize,PredictiveController,PIReference
from .research_codec import model_digest,compact_plan
from .calibration import prefix_schedule
from .diagnostic import schedule,provenance,peak_rss_bytes
from .state_experiment import arrays
from .control_experiment import _save_npz
from .reachability import state_hashes

KINDS=('PI10_5','FIXED-MPC','RLS-MPC','BIAS-MPC','FIXED','ZERO')
BANK=tuple((reg,k) for reg in ('STATIC','LOSS') for k in KINDS)+(('LOSS','MAX'),)


def make_controller(initial,kind):
    if kind.endswith('-MPC'):return PredictiveController(initial,kind.split('-')[0])
    c=PIReference(initial.calibration,initial.trial_id,initial.history[-1]);c.policy=Policy(initial.calibration,kind)
    original_command,original_accept=c.command,c.accept;c.command_ns=[];c.update_ns=[]
    def command(t):
        start=now_ns();result=original_command(t);c.command_ns.append(now_ns()-start);return result
    def accept(o,r,t):
        start=now_ns();result=original_accept(o,r,t);c.update_ns.append(now_ns()-start);return result
    c.command,c.accept=command,accept
    return c


def state_frame(c):
    if hasattr(c,'model'):return np.array([c.time_us,c.q,c.safe,c.recover,c.model.received,c.model.updates,c.model.skips,c.failure is not None],float)
    p=c.policy;return np.r_[p.record()]


def worker(n,rep,phase,root):
    if (n,rep) not in jobs(phase):raise ValueError('Unregistered network/noise identity')
    from ._brian import BrianEngine
    from .tick_execution import TickExecution
    d=Deadline.from_environment();out=Path(root)/f'n{n}_r{rep}';out.mkdir(exist_ok=False);e=None;began=now_ns()
    try:
        d.check();e=BrianEngine(Config(network_id=n,replicate_id=rep,trial_id=f'm005b-{phase}-n{n}-r{rep}'));prefix=[];commands=prefix_schedule()
        for start in range(0,2550,800):
            d.check();part=e.run_commands(schedule(e,commands[start:start+800]));prefix.extend(part)
            if len(part)==800:_save_npz(out/f'prefix_segment_{start//800}.npz',**arrays(part))
        initial=initialize([r.observation for r in prefix],[r.receipt for r in prefix]);_save_npz(out/'prefix.npz',**arrays(prefix));_save_npz(out/'initial.npz',p=initial.information_inverse,history=initial.history)
        from dataclasses import asdict
        atomic_json(out/'initial.json',dict(record=initial.record,calibration=asdict(initial.calibration),trial_id=initial.trial_id))
        driver=TickExecution(e);e.save('control');checkpoint=state_hashes(e);branch_bank=BANK if phase!='faults' else tuple((reg,kind,fault) for kind in ('PI10_5','RLS-MPC') for reg in ('STATIC','LOSS') for fault in ('DELAY','DROP'))
        summaries=[];horizon=2 if phase=='engineering' else 64
        for item in branch_bank:
            d.check();reg,kind=item[:2];fault=item[2] if len(item)==3 else None;name='_'.join(item);e.restore('control');assert state_hashes(e)==checkpoint
            c=make_controller(initial,kind);records=[];predictions=[];frames=[];hashes=[];presented=[];dense_theta=[];dense_p=[];dense_bias=[];plan_count=0;start_wall=now_ns();initial_state=state_frame(c)
            def record(r,o,controller):
                nonlocal plan_count
                records.append(r);presented.append(o is not None);frames.append(state_frame(controller))
                if hasattr(controller,'model'):
                    predictions.append(np.full(4,np.nan) if controller.last_prediction is None else controller.last_prediction.copy());hashes.append(np.frombuffer(model_digest(controller.model),dtype=np.uint8).copy())
                    if controller.plans:
                        plan=compact_plan(controller.plans.pop());_save_npz(out/f'{name}_plan_{plan_count:02}.npz',**plan);plan_count+=1
                    if len(records)%50==0:dense_theta.append(controller.model.theta.copy());dense_p.append(controller.model.p.copy());dense_bias.append(controller.model.bias_p)
                else:predictions.append(np.full(4,np.nan))
            faultfun=(lambda t:75_000_000<=t<76_000_000) if fault is not None else None
            for second in range(horizon):
                d.check();e.group.gain=.6 if reg=='LOSS' and second>=16 else 1.;driver.run(c,1,deadline=d,fault=faultfun,on_record=record)
                if (second+1)%16==0 and second<horizon-1:
                    _save_npz(out/f'{name}_segment_{second+1:02}.npz',**arrays(records[-800:]),frames=np.array(frames[-800:]),pre_prediction=np.array(predictions[-800:]),presented=np.array(presented[-800:]),state_hashes=np.array(hashes[-800:],np.uint8))
            data=arrays(records);_save_npz(out/f'{name}.npz',**data,frames=np.array(frames),initial_state=initial_state,pre_prediction=np.array(predictions),presented=np.array(presented),state_hashes=np.array(hashes,np.uint8),dense_theta=np.array(dense_theta),dense_p=np.array(dense_p),dense_bias=np.array(dense_bias),command_ns=np.array(getattr(c,'command_ns',[])),update_ns=np.array(getattr(c,'update_ns',[])))
            u=data['delivered'];violations=int((u<0).sum()+(u>120).sum()+(u.sum(1)>240).sum()+(abs(np.diff(np.vstack([initial.history[-1],u]),axis=0))>30).sum());safe=int(np.array(frames)[:,2].sum()) if hasattr(c,'model') else int(np.array(frames)[:,6].sum())
            summaries.append(dict(condition=reg,controller=kind,fault=fault,name=name,bins=len(records),plans=plan_count,violations=violations,safe_bins=safe,model_failure=getattr(c,'failure',None),wall_s=(now_ns()-start_wall)/1e9,noise=e.provenance()['noise_hashes'],exposure_pA_s=float(u.sum()*.02)))
            atomic_json(out/'progress.json',dict(complete_branches=len(summaries),last_branch=name,complete_trial=False))
            del c,records,data;gc.collect()
        d.check();atomic_json(out/'trial.json',dict(status='complete',network=n,replicate=rep,phase=phase,branches=summaries,checkpoint=checkpoint,engine=e.provenance(),peak_rss_bytes=peak_rss_bytes(),wall_s=(now_ns()-began)/1e9))
    except BaseException as exc:
        atomic_json(out/'failure.json',dict(status='failed',network=n,replicate=rep,phase=phase,error=f'{type(exc).__name__}: {exc}'));raise
    finally:
        if e is not None:e.close()


def jobs(phase):
    if phase=='engineering':return [(0,60)]
    if phase not in ('primary','validation','faults'):raise ValueError('Unknown phase')
    return [(n,r) for n in (range(10) if phase=='primary' else range(10,15) if phase=='validation' else range(3)) for r in ((47,48) if phase=='primary' else (49,50) if phase=='validation' else (49,))]


def inner(phase,root):
    d=Deadline.from_environment();root=Path(root);root.mkdir(exist_ok=False);meta=provenance();meta.update(phase=phase,jobs=jobs(phase),protocol_sha256=hashlib.sha256(Path('docs/research/011_M005B_CONTROL_PROTOCOL.md').read_bytes()).hexdigest(),deadline_ns=d.end_ns,clock_id=d.clock_id,workers=3,controller_bank=BANK)
    atomic_json(root/'provenance.json',meta);commands=[[sys.executable,'-m','neuromancer.m005b_study','worker',str(n),str(rep),phase,str(root)] for n,rep in jobs(phase)];result=supervise(commands,root/'supervision',d,workers=3)
    if result['status']!='COMPLETED':raise RuntimeError('Incomplete scientific acquisition: '+result['status'])
    trials=[json.loads((root/f'n{n}_r{rep}'/'trial.json').read_text()) for n,rep in jobs(phase)];assert all(t['status']=='complete' and t['peak_rss_bytes']<2*1024**3 for t in trials);d.check();atomic_json(root/'complete.json',dict(status='complete',trials=len(trials),phase=phase))


def capture(phase,output,prior=None,gate=None):
    if phase=='faults' and prior is None:raise ValueError('Faults must inherit the original development deadline')
    if phase in ('primary','validation') and prior is not None:raise ValueError('Unexpected inherited acquisition deadline')
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    if phase=='validation':
        if gate is None or not json.loads(Path(gate).read_text())['scientific_pass']:raise ValueError('Development scientific gate closed')
    begin=now_ns();d=Deadline(begin+(1200 if phase=='engineering' else 5400 if phase=='validation' else 10800)*10**9,clock_domain()) if prior is None else Deadline(**json.loads(Path(prior).read_text())['deadline'])
    d.check();env=dict(os.environ,NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id);command=[sys.executable,'-m','neuromancer.m005b_study','inner',phase,str(output)];fault=None;proc=None
    launch=dict(phase=phase,deadline=dict(end_ns=d.end_ns,clock_id=d.clock_id),started_ns=begin,command=command,source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip());atomic_json(output.parent/(phase+'_launch.json'),launch)
    with (output.parent/(phase+'_capture.log')).open('wb') as log:
        proc=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);awake=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(proc.pid)])
        try:
            while proc.poll() is None:
                d.check();progress=output/'supervision/progress.json'
                if progress.exists():
                    workers=json.loads(progress.read_text())['workers'];pids=[w['pid'] for w in workers if w.get('pid') and not w.get('terminal')];rss={}
                    if pids:
                        p=subprocess.run(['ps','-o','pid=,rss=','-p',','.join(map(str,pids))],capture_output=True,text=True,timeout=2);rss={int(s.split()[0]):int(s.split()[1])*1024 for s in p.stdout.splitlines()}
                    completed=[json.loads(f.read_text()) for f in output.glob('n*_r*/trial.json')];completed_peak=max([x['peak_rss_bytes'] for x in completed],default=0)
                    mission=output.parent;qualification=Path('reports/evidence/v1_finish')
                    if mission.is_relative_to(qualification):mission=qualification
                    allocation=sum(f.stat().st_blocks*512 for f in mission.rglob('*') if f.is_file() and not f.is_symlink());roots=list(Path('reports/evidence').glob('m005a*'))+list(Path('reports/evidence').glob('m005b*'))+[mission]+list(Path('runs').glob('m005a*'))+list(Path('runs').glob('m005b*'));combined=sum(f.stat().st_blocks*512 for r in roots for f in r.rglob('*') if f.is_file() and not f.is_symlink());failures=list(output.glob('n*_r*/failure.json'))
                    sample=dict(ns=now_ns(),native_clock=get_clock().sample(),rss_bytes=rss,aggregate_rss_bytes=sum(rss.values()),completed_peak_rss_bytes=completed_peak,mission_allocated_bytes=allocation,combined_allocated_bytes=combined,complete_trials=len(list(output.glob('n*_r*/trial.json'))),failures=[str(f) for f in failures])
                    with (output.parent/(phase+'_resource.jsonl')).open('a') as stream:stream.write(json.dumps(sample)+'\n')
                    if completed_peak>=2*1024**3 or max(rss.values(),default=0)>=2*1024**3 or sum(rss.values())>6*1024**3 or allocation>750*1024**2 or combined>int(1.2*1024**3) or failures:raise RuntimeError('Resource/worker fault')
                time.sleep(min(1.,max(.01,d.remaining())))
        except BaseException as exc:
            fault=repr(exc)
            try:os.killpg(proc.pid,signal.SIGINT)
            except ProcessLookupError:pass
            try:proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                progress=output/'supervision/progress.json'
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
    finish=now_ns();status='COMPLETE' if proc.returncode==0 and fault is None and finish<d.end_ns else 'PARTIAL';atomic_json(output.parent/(phase+'_closure.json'),dict(status=status,returncode=proc.returncode,fault=fault,started_ns=begin,finished_ns=finish,elapsed_s=(finish-begin)/1e9,deadline=dict(end_ns=d.end_ns,clock_id=d.clock_id)))
    if status!='COMPLETE':raise RuntimeError('Incomplete study; preserve and stop')


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='op',required=True)
    q=sub.add_parser('worker');q.add_argument('n',type=int);q.add_argument('rep',type=int);q.add_argument('phase');q.add_argument('root')
    q=sub.add_parser('inner');q.add_argument('phase');q.add_argument('root')
    q=sub.add_parser('acquire');q.add_argument('--phase',choices=('primary','faults','validation','engineering'),required=True);q.add_argument('--output',required=True);q.add_argument('--prior');q.add_argument('--gate')
    a=p.parse_args()
    if a.op=='worker':worker(a.n,a.rep,a.phase,a.root)
    elif a.op=='inner':inner(a.phase,a.root)
    else:capture(a.phase,a.output,a.prior,a.gate)
if __name__=='__main__':main()
