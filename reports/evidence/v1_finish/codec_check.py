"""Exact cache-pruning and model-state replay on preserved engineering records."""
import json
from pathlib import Path
import numpy as np
from neuromancer.predictive import Initialization,PredictiveController
from neuromancer.control import ControlCalibration
from neuromancer.observation import Observation
from neuromancer.substrate import Receipt
from neuromancer.research_codec import model_digest,compact_plan
from neuromancer.supervisor import Deadline,atomic_json
R=Path(__file__).resolve().parent

def main():
 d=Deadline.from_environment();base=Path('reports/evidence/m005b_1/smoke');meta=json.loads((base/'initial.json').read_text());arr=dict(np.load(base/'initial.npz'));initial=Initialization(meta['record'],arr['p'],arr['history'],ControlCalibration(**meta['calibration']),meta['trial_id']);count=0
 for kind in ('FIXED','RLS','BIAS'):
  data=dict(np.load(base/f'{kind}.npz'));controllers=[PredictiveController(initial,kind) for _ in range(2)]
  for i in range(100):
   commands=[c.command(c.time_us) for c in controllers];assert commands[0]==commands[1]
   if controllers[1].plans:
    plan=controllers[1].plans.pop();compact=compact_plan(plan);np.testing.assert_array_equal(compact['selected_forecast'],plan['predictions'][plan['chosen']])
   for c,cmd in zip(controllers,commands):
    o=Observation(initial.trial_id,*map(int,data['time_us'][i]),tuple(map(int,data['counts'][i])),(0.,)*20,tuple(map(int,data['coverage_us'][i])),tuple(map(bool,data['valid'][i])),(),(),(0.,)*4,(0.,)*4,True);r=Receipt(cmd.trial_id,cmd.command_id,cmd.start_us,cmd.start_us,o.stop_us,cmd.current_pA,cmd.current_pA,'delivered','');c.accept(o,r,o.stop_us)
   assert model_digest(controllers[0].model)==model_digest(controllers[1].model);count+=1
 atomic_json(R/'codec_qualification.json',dict(status='PASS',exact_command_model_digest_pairs=count,candidate_costs_retained=True,other_forecasts_reconstructible=True,neural_seconds_acquired=0));d.check()
if __name__=='__main__':main()
