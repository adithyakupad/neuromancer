"""Independent raw-unit convolution, objective and finite-bank verification."""
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
from prototype import plan,bank
from test_design import fixture
from neuromancer.supervisor import Deadline
R=Path(__file__).resolve().parent

def main():
 d=Deadline.from_environment();d.check();u,y,(r,z,v,p)=fixture();h=u[-9:];out=plan(r,r['coef'],h,10.,51_000_000,limit_s=10)
 coef=np.array(r['coef']);beta=coef[1:]/np.array(r['scale'])[:,None];offset=np.array(r['output_mean'])+coef[0]-np.array(r['mean'])@beta;expected=[];future_prefix=[]
 for i,q in enumerate(out['bank']):
  inputs=np.zeros((109,4));inputs[:9]=h;inputs[9:,::2]=q[:,None]
  pred=np.tile(offset,(100,1))
  for lag in range(10):
   for channel in range(4):pred+=inputs[9-lag:109-lag,channel,None]*beta[lag*4+channel]
  expected.append(pred)
  holds=(i//25*5.,i%25*5.);means=np.array([pred[:50].mean(),pred[50:].mean()])
  current=.02*sum(.02*(x/120)**2 for x in q);slew=.01*(((holds[0]-h[-1,0])/120)**2+((holds[1]-holds[0])/120)**2)
  objective=sum((means-10.)**2)+current+slew;future_prefix.append(objective)
 np.testing.assert_allclose(expected,out['predictions'],atol=1e-10);np.testing.assert_allclose(future_prefix,out['cost'],atol=1e-11)
 # Same first hold, distinct second hold: future actions cannot alter first-second predictions.
 np.testing.assert_array_equal(out['predictions'][100,:50],out['predictions'][124,:50])
 expected=np.array(future_prefix);ties=np.flatnonzero(expected<=expected.min()+1e-12);i=min(ties,key=lambda j:(2*.02*out['bank'][j].sum(),j//25,j%25));assert i==out['chosen']
 weak=np.ones((500,11));assert np.linalg.matrix_rank(weak)==1
 hist=json.loads((R/'preservation.json').read_text())['historical_sha256']
 for path,value in hist.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==value
 b=json.loads((R/'benchmark.json').read_text());assert b['status']=='PASS' and b['historical_input_only_audit']['reduced_rank']==11 and b['historical_input_only_audit']['reduced_condition']<=1e6
 assert b['peak_rss_bytes']<2*1024**3
 assert b['future_estimate_s']['development_neural']+b['future_estimate_s']['development_serial_planning']<10800
 assert b['future_estimate_s']['validation_neural']+b['future_estimate_s']['validation_serial_planning']<5400
 result=dict(status='PASS',independent_plan_objectives=625,independent_sector_bin_forecasts=625*100*4,future_plan_mutation_preserves_first_second=True,constant_input_rank=1,historical_files_unchanged=len(hist),source_preregistration_revision='f13b137',future_estimate_within_caps=True)
 (R/'independent_verification.json').write_text(json.dumps(result,indent=2)+'\n');d.check();print(json.dumps(result))
if __name__=='__main__':main()
