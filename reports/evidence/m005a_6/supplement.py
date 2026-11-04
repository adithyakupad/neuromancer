"""Complete prespecified calibration and network-bootstrap time-course summaries."""
import csv,json
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline
r=Path(__file__).resolve().parent;Deadline.from_environment().check()
def read(name):return list(csv.DictReader((r/name).open()))
def out(name,values):
 with (r/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(values[0]));w.writeheader();w.writerows(values)
n=read('network_diagnosis.csv');t=read('timecourses.csv');cal=[];curves=[]
for v in n:
 static=float(v['STATIC_FIXED_late_bias_hz'])-float(v['STATIC_ZERO_late_bias_hz']);loss=float(v['LOSS_FIXED_late_bias_hz'])-float(v['LOSS_ZERO_late_bias_hz']);cal.append(dict(network=int(v['network']),target_hz=float(v['target_hz']),qff_pA=float(v['qff_pA']),slope_hz_per_pA=float(v['slope_hz_per_pA']),fixed_static_bias_hz=float(v['STATIC_FIXED_late_bias_hz']),fixed_loss_bias_hz=float(v['LOSS_FIXED_late_bias_hz']),fixed_static_evoked_hz=static,fixed_loss_evoked_hz=loss,evaluator_scaled_response_hz=.6*static,scaling_residual_hz=loss-.6*static,evaluator_gain_scaled_q_pA=float(v['qff_pA'])/.6))
for name in ('ZERO','FIXED','MAX','PI10_5'):
 for cond in ('STATIC','LOSS'):
  for sec in range(32):
   x=np.array([np.mean([float(v['signed_error_hz']) for v in t if int(v['network'])==net and int(v['second'])==sec and v['controller']==name and v['condition']==cond]) for net in range(10)])
   g=np.random.Generator(np.random.PCG64(20261025));samples=x[g.integers(0,10,(10000,10))].mean(1);q=np.quantile(samples,[.025,.975]);curves.append(dict(controller=name,condition=cond,second=sec,mean_error_hz=float(x.mean()),ci_low_hz=float(q[0]),ci_high_hz=float(q[1]),interpretation='pointwise descriptive; not simultaneous bands'))
out('calibration_diagnostic.csv',cal);out('timecourse_intervals.csv',curves)
Deadline.from_environment().check()
