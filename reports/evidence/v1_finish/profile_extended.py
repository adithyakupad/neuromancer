"""Nonreserved exact-equivalence and throughput qualification, no study scoring."""
import json,time
from pathlib import Path
import numpy as np
from neuromancer._brian import BrianEngine
from neuromancer.substrate import Config
from neuromancer.calibration import prefix_schedule
from neuromancer.diagnostic import schedule,provenance,peak_rss_bytes
from neuromancer.state_experiment import arrays
from neuromancer.predictive import initialize,PredictiveController,public_step,PIReference
from neuromancer.tick_execution import TickExecution
from neuromancer.supervisor import Deadline,atomic_json
R=Path(__file__).resolve().parent

def main():
 d=Deadline.from_environment();d.check();e=BrianEngine(Config(network_id=0,replicate_id=60,trial_id='v1-engineering-n0-r60'));out=R/'profile_extended';out.mkdir(exist_ok=False)
 try:
  p=e.run_commands(schedule(e,prefix_schedule()));initial=initialize([x.observation for x in p],[x.receipt for x in p]);driver=TickExecution(e);e.save('qualified');results=[]
  for kind,fault in [('FIXED',False),('BIAS',False),('RLS_LOSS',False),('BAD_INFORMATION',False)]:
   cache={}
   for mode in ('original','optimized'):
    e.restore('qualified');controller=PIReference(initial.calibration,initial.trial_id,np.zeros(4)) if kind=='PI' else PredictiveController(initial,'RLS' if kind in ('RLS_LOSS','BAD_INFORMATION') else kind);records=[];states=[];began=time.perf_counter()
    def observe(r,presented,c):
     states.append(np.r_[c.model.theta.ravel(),c.model.p.ravel(),c.history.ravel(),c.time_us,c.q,c.safe,c.recover,c.model.updates,c.model.skips,c.failure is not None])
    faultfun=(lambda t:52_000_000<=t<52_200_000) if fault else None
    if mode=='original':
     for k in range(100):
      d.check();e.group.gain=.6 if kind=='RLS_LOSS' and k>=50 else 1.;cmd=controller.command(e.time_us)
      if kind=='BAD_INFORMATION' and k==0:controller.model.p=-np.eye(41)*100
      r=e.advance(cmd,e.time_us+20000);o=None if faultfun is not None and faultfun(r.observation.start_us) else r.observation;controller.accept(o,r.receipt,e.time_us);records.append(r);observe(r,o,controller)
    else:
     if kind=='BAD_INFORMATION':
      original=controller.command
      def injected(t):
       cmd=original(t)
       if t==51_000_000:controller.model.p=-np.eye(41)*100
       return cmd
      controller.command=injected
     for second in range(2):
      e.group.gain=.6 if kind=='RLS_LOSS' and second==1 else 1.
      records.extend(driver.run(controller,1,deadline=d,fault=faultfun,on_record=observe))
    elapsed=time.perf_counter()-began;data=arrays(records);data['states']=np.array(states);data['neural_terminal']=np.r_[np.asarray(e.group.v),np.asarray(e.group.I_E),np.asarray(e.group.I_I),np.asarray(e.group.eta),np.asarray(e.group.lastspike),np.asarray(e.group.not_refractory)];np.savez_compressed(out/f'{kind}_{fault}_{mode}.npz',**data);cache[mode]=data
    results.append(dict(kind=kind,fault=fault,mode=mode,seconds=2,wall_s=elapsed,controller_failure=getattr(controller,'failure',None),safe=getattr(controller,'safe',controller.policy.safe if kind=='PI' else False)))
   for key in cache['original']:np.testing.assert_array_equal(cache['original'][key],cache['optimized'][key])
  atomic_json(out/'qualification.json',dict(status='PASS',exact_neural_observations_actions_model_states=True,results=results,peak_rss_bytes=peak_rss_bytes(),source=provenance()))
 finally:e.close()
if __name__=='__main__':main()
