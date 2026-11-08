"""59 simulated seconds, non-confirmatory development engineering fixture only."""
import hashlib,json,time
from dataclasses import asdict
from pathlib import Path
import numpy as np
from neuromancer._brian import BrianEngine
from neuromancer.substrate import Config
from neuromancer.calibration import prefix_schedule
from neuromancer.diagnostic import schedule,provenance,peak_rss_bytes
from neuromancer.state_experiment import arrays
from neuromancer.predictive import initialize,PredictiveController,public_step
from neuromancer.reachability import state_hashes
from neuromancer.supervisor import Deadline,atomic_json
R=Path(__file__).resolve().parent

def main():
 d=Deadline.from_environment();d.check();began=time.perf_counter();engine=BrianEngine(Config(network_id=0,replicate_id=60,trial_id='m005b1-smoke-n0-r60'));root=R/'smoke';root.mkdir(exist_ok=False)
 try:
  prefix=engine.run_commands(schedule(engine,prefix_schedule()));np.savez_compressed(root/'prefix.npz',**arrays(prefix));initial=initialize([r.observation for r in prefix],[r.receipt for r in prefix]);engine.save('smoke');checkpoint=state_hashes(engine)
  atomic_json(root/'initial.json',dict(record=initial.record,calibration=asdict(initial.calibration),trial_id=initial.trial_id));np.savez_compressed(root/'initial.npz',p=initial.information_inverse,history=initial.history)
  results={}
  for kind in ('FIXED','RLS','BIAS','RLS_REPLAY'):
   d.check();engine.restore('smoke');assert state_hashes(engine)==checkpoint;p=PredictiveController(initial,kind.split('_')[0]);rows=[];commands=[];pred=[];features=[];theta=[];information=[];bias_p=[];start=time.perf_counter()
   for k in range(100):
    d.check();c=p.command(engine.time_us);commands.append(c.current_pA);features.append(p.pending[1].copy());pred.append(np.full(4,np.nan) if p.last_prediction is None else p.last_prediction.copy());r=engine.advance(c,c.start_us+20000);p.accept(r.observation,r.receipt,r.observation.stop_us);rows.append(r);theta.append(p.model.theta.copy());information.append(p.model.p.copy());bias_p.append(p.model.bias_p)
   data=arrays(rows);data.update(commands=np.array(commands),pre_prediction=np.array(pred),features=np.array(features),theta_after=np.array(theta),p_after=np.array(information),bias_p=np.array(bias_p),command_ns=np.array(p.command_ns),update_ns=np.array(p.update_ns))
   np.savez_compressed(root/f'{kind}.npz',**data)
   for j,plan in enumerate(p.plans):np.savez_compressed(root/f'{kind}_plan{j}.npz',**{k:v for k,v in plan.items() if k!='origin_us'},origin_us=plan['origin_us'])
   atomic_json(root/f'{kind}_events.json',p.events);assert p.failure is None and not p.safe and p.model.failure is None and len(p.plans)==2
   results[kind]=dict(bins=len(rows),plans=len(p.plans),updates=p.model.updates,skips=p.model.skips,failure=p.failure,elapsed_s=time.perf_counter()-start,noise=engine.provenance()['noise_hashes'])
   if kind=='RLS_REPLAY':
    with np.load(root/'RLS.npz') as old:
     for key in data:
      if key not in ('command_ns','update_ns'):np.testing.assert_array_equal(data[key],old[key])
  assert results['FIXED']['noise']==results['RLS']['noise']==results['BIAS']['noise']==results['RLS_REPLAY']['noise']
  d.check();atomic_json(root/'summary.json',dict(status='PASS',scope='engineering_only_no_scientific_endpoint_scoring',networks=[0],noise=[60],simulated_seconds=59,branches=results,exact_replay=True,checkpoint=checkpoint,peak_rss_bytes=peak_rss_bytes(),wall_s=time.perf_counter()-began,source=provenance()))
 finally:engine.close()
if __name__=='__main__':main()
