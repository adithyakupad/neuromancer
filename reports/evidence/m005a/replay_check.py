"""Bounded cold neural replay of one already-acquired TUNE branch."""
import argparse,json,time,hashlib
from pathlib import Path
import numpy as np
from neuromancer._brian import BrianEngine
from neuromancer.substrate import Config
from neuromancer.control import Policy,calibrate,project
from neuromancer.calibration import prefix_schedule
from neuromancer.diagnostic import schedule,provenance
from neuromancer.state_experiment import arrays


def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    a.output.mkdir(exist_ok=False,parents=True);name='PI20_10';folder=a.raw/'n0_r40'
    deadline=time.time()+1200
    engine=BrianEngine(Config(network_id=0,replicate_id=40,trial_id='m005a-n0-r40'));began=time.perf_counter();count=0
    try:
        pref=engine.run_commands(schedule(engine,prefix_schedule()));d=arrays(pref)
        with np.load(folder/'prefix.npz') as old:
            for key in old.files:np.testing.assert_array_equal(d[key],old[key]);count+=1
        c=calibrate([r.observation for r in pref[:2350]],[r.receipt for r in pref[:2350]])
        policy=Policy(c,name);results=[];dec=[];intent=[]
        for k in range(32):
            if time.time()>deadline:raise TimeoutError('Verification absolute-wall cap')
            engine.group.gain=1. if k<16 else .6
            dec.append(policy.record());target=policy.desired();previous=engine.previous.copy();rows=[]
            for _ in range(50):
                u,_=project(target,previous);rows.append(u);previous=u
            block=engine.run_commands(schedule(engine,rows))
            for r in block:policy.accept(r.observation,r.observation.available_us)
            results.extend(block);intent.extend([target]*50)
        d=arrays(results);d.update(decisions=np.array(dec),intent=np.array(intent),terminal=np.array(policy.record()))
        with np.load(folder/f'LOSS_{name}.npz') as old:
            for key in d:np.testing.assert_array_equal(d[key],old[key]);count+=1
        np.savez_compressed(a.output/'replay.npz',**d)
        source=provenance();source['protocol_sha256']=hashlib.sha256(Path('docs/research/009_M005A_CONTROL_PROTOCOL.md').read_bytes()).hexdigest()
        (a.output/'verification.json').write_text(json.dumps(dict(status='PASS',controller=name,simulated_seconds=83,
            exact_arrays=count,wall_s=time.perf_counter()-began,source=source,engine=engine.provenance(),
            interpretation='duplicate technical replay, not a new statistical replicate'),indent=2)+'\n')
    finally:engine.close()


if __name__=='__main__':main()
