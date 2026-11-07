"""Explicit machine-readable synthetic fallback and failure-to-identify evidence."""
import json,sys
from pathlib import Path
from dataclasses import replace
import numpy as np
from neuromancer.predictive import PredictiveController,FIRModel
from neuromancer.supervisor import Deadline,atomic_json
R=Path(__file__).resolve().parent;sys.path.insert(0,str(Path('tests').resolve()))
from test_predictive import fixture,observation,receipt

def main():
 d=Deadline.from_environment();d.check();initial,*_=fixture();records={}
 for fault in ('missing','late','mask','negative','information','forecast','deadline'):
  class Clock:
   def __init__(self):self.t=0
   def __call__(self):self.t+=100_000_000;return self.t
  c=PredictiveController(initial,'RLS',**({'clock':Clock()} if fault=='deadline' else {}));commands=[];states=[]
  for k in range(55):
   command=c.command(c.time_us);commands.append(command.current_pA);obs=observation(c.time_us)
   if k==0:
    if fault=='missing':obs=None
    elif fault=='late':obs=replace(obs,available_us=obs.stop_us+20000)
    elif fault=='mask':obs=replace(obs,valid=(False,)*20)
    elif fault=='negative':obs=replace(obs,counts=(-1,)*20)
    elif fault=='information':c.model.p=-100*np.eye(41)
    elif fault=='forecast':c.model.theta[:]=1e5
   c.accept(obs,receipt(command),c.time_us+20000);states.append(c.events[-1])
  u=np.array(commands);assert (u>=0).all() and (u<=120).all() and (u.sum(1)<=240).all() and (abs(np.diff(np.vstack([initial.history[-1],u]),axis=0))<=30).all()
  numerical=fault in ('information','forecast','deadline')
  if numerical:assert c.failure is not None and c.safe and not u[-1].any()
  else:assert c.failure is None and not c.safe and states[0]['safe'] and states[4]['recover']==4
  records[fault]=dict(requested_and_delivered=u.tolist(),events=states,latched=c.failure,rearmed=not c.safe,updates=c.model.updates,skips=c.model.skips,expected_injection=True)
 # Two different actuator gains are observationally indistinguishable with zero input.
 truth_gain1=np.full((200,4),8.);truth_gain06=truth_gain1.copy();assert np.array_equal(truth_gain1,truth_gain06)
 m=FIRModel(initial.record,initial.information_inverse,'RLS');x=np.zeros(40);z=m.standardized(x)
 for y in truth_gain06:m.update(x,y)
 rank=int(np.linalg.matrix_rank(np.tile(z,(200,1))));assert rank==1
 records['weak_zero_input']=dict(equal_outputs_under_distinct_gains=True,online_design_rank=rank,observations=200,updates=m.updates,kernel_identification='NOT_IDENTIFIABLE',physical_gain_fed_to_model=False)
 # Wrong-sign, nonnegative actuator: target9 cannot be reached from baseline8.
 records['wrong_sign_unreachable']=dict(baseline_hz=8,target_hz=9,gain_hz_per_pA=-.0275,allowed_q=[0,120],maximum_attainable_hz=8,minimum_possible_absolute_error_hz=1,expected_failure=True,scope='analytical_synthetic_plant_not_neural_outcome')
 atomic_json(R/'failure_fixtures.json',dict(status='PASS_EXPECTED_FAILURES_RETAINED',fixtures=records));d.check()
if __name__=='__main__':main()
