"""Bounded cold neural replay of one already-acquired confirmation branch."""
import argparse,json,time
from pathlib import Path
import numpy as np
from neuromancer._brian import BrianEngine
from neuromancer.substrate import Config
from neuromancer.control import Policy,calibrate,project
from neuromancer.calibration import prefix_schedule
from neuromancer.diagnostic import schedule,provenance
from neuromancer.state_experiment import arrays


def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('selection',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    a.output.mkdir(exist_ok=False,parents=True);name=json.loads(a.selection.read_text())['controller'];folder=a.raw/'n0_r41'
    engine=BrianEngine(Config(network_id=0,replicate_id=41,trial_id='m005a-n0-r41'));began=time.perf_counter();count=0
    try:
        pref=engine.run_commands(schedule(engine,prefix_schedule()));d=arrays(pref)
        with np.load(folder/'prefix.npz') as old:
            for key in old.files:np.testing.assert_array_equal(d[key],old[key]);count+=1
        c=calibrate([r.observation for r in pref[:2350]],[r.receipt for r in pref[:2350]])
        policy=Policy(c,name);results=[];dec=[];intent=[]
        for k in range(32):
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
        (a.output/'verification.json').write_text(json.dumps(dict(status='PASS',controller=name,simulated_seconds=83,
            exact_arrays=count,wall_s=time.perf_counter()-began,source=provenance(),engine=engine.provenance(),
            interpretation='duplicate technical replay, not a new statistical replicate'),indent=2)+'\n')
    finally:engine.close()


if __name__=='__main__':main()
