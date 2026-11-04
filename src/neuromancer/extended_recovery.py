"""M005A.7 evaluator stepping; uses the unchanged observation-only Policy."""
from dataclasses import asdict
import gc
import json
from pathlib import Path
import sys
import time
import numpy as np
from .calibration import prefix_schedule
from .control import Policy, calibrate, project
from .control_experiment import _save_npz, _check_worker
from .diagnostic import schedule, peak_rss_bytes
from .online_experiment import branch_audit
from .reachability import state_hashes
from .state_experiment import arrays
from .substrate import Config
from .supervisor import atomic_json

BRANCHES = (('STATIC','PI10_5'),('LOSS','PI10_5'),('STATIC','FIXED'),('LOSS','FIXED'),('LOSS','MAX'))
HORIZON = 64


def gain_for(condition: str, second: int) -> float:
    if condition not in ('STATIC','LOSS') or type(second) is not int or not 0 <= second < HORIZON:
        raise ValueError('Invalid evaluator phase')
    return .6 if condition == 'LOSS' and second >= 16 else 1.


def step_second(engine, policy: Policy, condition: str):
    """Advance exactly one already-decided second, then update the same policy."""
    t=engine.time_us
    if t != policy.expected_us or t < 51_000_000 or (t-51_000_000)%1_000_000:
        raise ValueError('Neural/controller phase mismatch')
    second=(t-51_000_000)//1_000_000
    engine.group.gain=gain_for(condition,second) # Evaluator only; never passed to Policy.
    began=time.perf_counter_ns();desired=policy.desired();decision=policy.record();rows=[];prior=engine.previous.copy()
    for _ in range(50):
        action,status=project(desired,prior)
        if 'invalid' in status:raise RuntimeError('Invalid requested action')
        rows.append(action);prior=action
    planning=time.perf_counter_ns()-began
    block=engine.run_commands(schedule(engine,rows));began=time.perf_counter_ns()
    for r in block:
        policy.accept(r.observation,r.observation.available_us)
        if policy.safe and policy.calibration.valid:raise RuntimeError('Unexpected scientific fallback')
    timing=(planning,time.perf_counter_ns()-began,sum(r.neural_wall_ns for r in block),sum(r.observation_wall_ns for r in block))
    return block,desired,decision,timing


def run_trial(n: int, rep: int, output: str, deadline_ns: int):
    from ._brian import BrianEngine
    if n not in range(10) or rep not in (45,46):raise ValueError('Unregistered trial')
    folder=Path(output)/f'n{n}_r{rep}';folder.mkdir(exist_ok=False);engine=None;began=time.perf_counter_ns()
    try:
        _check_worker(deadline_ns)
        engine=BrianEngine(Config(network_id=n,replicate_id=rep,trial_id=f'm005a7-n{n}-r{rep}'))
        prefix=[];commands=prefix_schedule()
        for start in range(0,2550,800):
            _check_worker(deadline_ns);part=engine.run_commands(schedule(engine,commands[start:start+800]));prefix.extend(part)
            if len(part)==800:_save_npz(folder/f'prefix_progress_{start//800}.npz',**arrays(part))
        calibration=calibrate([r.observation for r in prefix[:2350]],[r.receipt for r in prefix[:2350]])
        atomic_json(folder/'calibration.json',asdict(calibration));_save_npz(folder/'prefix.npz',**arrays(prefix))
        engine.save('control');checkpoint=state_hashes(engine);branches=[]
        for condition,name in BRANCHES:
            _check_worker(deadline_ns);engine.restore('control');assert state_hashes(engine)==checkpoint
            policy=Policy(calibration,name);results=[];intent=[];dec=[];timing=[];start_ns=time.perf_counter_ns()
            for second in range(HORIZON):
                _check_worker(deadline_ns)
                part,desired,decision,tm=step_second(engine,policy,condition);results.extend(part);intent.extend([desired.copy() for _ in part]);dec.append(decision);timing.append(tm)
                if (second+1)%16==0 and second+1<HORIZON:
                    _save_npz(folder/f'{condition}_{name}_progress_{second+1}.npz',**arrays(results[-800:]),intent=np.array(intent[-800:]),decisions=np.array(dec[-16:]),terminal=np.array(policy.record()))
                    atomic_json(folder/'progress.json',dict(condition=condition,controller=name,completed_seconds=second+1,complete_branch=False))
            data=arrays(results);audit=branch_audit(data['delivered'],np.zeros(4));assert audit['violations']==0
            _save_npz(folder/f'{condition}_{name}.npz',**data,intent=np.array(intent),decisions=np.array(dec),terminal=np.array(policy.record()),timings_ns=np.array(timing))
            branches.append(dict(condition=condition,controller=name,audit=audit,wall_ns=time.perf_counter_ns()-start_ns,noise=engine.provenance()['noise_hashes']))
        _check_worker(deadline_ns)
        record=dict(status='complete',network_id=n,replicate_id=rep,horizon_s=HORIZON,calibration=asdict(calibration),checkpoint=checkpoint,engine=engine.provenance(),branches=branches,wall_ns=time.perf_counter_ns()-began,peak_rss_bytes=peak_rss_bytes())
        atomic_json(folder/'trial.json',record);return record
    except Exception as exc:
        record=dict(status='failed',network_id=n,replicate_id=rep,error=f'{type(exc).__name__}: {exc}')
        atomic_json(folder/'failure.json',record);return record
    finally:
        if engine is not None:engine.close()
        del engine;gc.collect()


if __name__=='__main__':
    n,rep,out,end=sys.argv[1:];r=run_trial(int(n),int(rep),out,int(end));raise SystemExit(0 if r['status']=='complete' else 1)
