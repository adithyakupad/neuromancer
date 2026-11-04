"""Final validation guards on preserved smoke records; no new neural simulation."""
from pathlib import Path
import json,sys
from dataclasses import replace
import numpy as np
from neuromancer.predictive import Initialization,PredictiveController
from neuromancer.control import ControlCalibration
from neuromancer.observation import Observation
from neuromancer.substrate import Receipt
from neuromancer.supervisor import Deadline,atomic_json
R=Path(__file__).resolve().parent;S=R/'smoke'
def main():
 d=Deadline.from_environment();d.check();meta=json.loads((S/'initial.json').read_text());arr=dict(np.load(S/'initial.npz'));initial=Initialization(meta['record'],arr['p'],arr['history'],ControlCalibration(**meta['calibration']),meta['trial_id']);count=0
 for kind in ('FIXED','RLS','BIAS','RLS_REPLAY'):
  p=PredictiveController(initial,kind.split('_')[0]);data=dict(np.load(S/f'{kind}.npz'))
  for i in range(100):
   c=p.command(p.time_us);np.testing.assert_array_equal(c.current_pA,data['commands'][i]);o=Observation(initial.trial_id,*map(int,data['time_us'][i]),tuple(map(int,data['counts'][i])),(0.,)*20,tuple(map(int,data['coverage_us'][i])),tuple(map(bool,data['valid'][i])),(),(),(0.,)*4,(0.,)*4,True);r=Receipt(c.trial_id,c.command_id,c.start_us,c.start_us,c.start_us+20000,c.current_pA,c.current_pA,'delivered','');p.accept(o,r,o.stop_us);np.testing.assert_array_equal(p.model.theta,data['theta_after'][i]);np.testing.assert_array_equal(p.model.p,data['p_after'][i]);count+=1
  assert p.failure is None
 # Causal future-output mutation: identical histories through cutoff must remain identical.
 sys.path.insert(0,str(Path('tests').resolve()));from test_predictive import fixture,observation,receipt
 init,*_=fixture();a=PredictiveController(init,'RLS');b=PredictiveController(init,'RLS')
 for i in range(100):
  ca=a.command(a.time_us);cb=b.command(b.time_us)
  if i<=20:assert ca==cb;np.testing.assert_array_equal(a.model.theta,b.model.theta)
  a.accept(observation(a.time_us,10.),receipt(ca),a.time_us+20000);b.accept(observation(b.time_us,10. if i<20 else 40.),receipt(cb),b.time_us+20000)
 atomic_json(R/'final_replay.json',dict(status='PASS',exact_commands_and_states=count,final_source_valid_input_replay=True,new_neural_seconds=0,future_mutation_cutoff_bin=20,unchanged_pre_mutation_commands=21));d.check()
if __name__=='__main__':main()
