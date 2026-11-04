"""Original32s algorithm versus extended first32s; technical replay, not replicate."""
import json,time
from pathlib import Path
import numpy as np
from neuromancer._brian import BrianEngine
from neuromancer.substrate import Config
from neuromancer.control import Policy,calibrate,project
from neuromancer.calibration import prefix_schedule
from neuromancer.diagnostic import schedule,provenance
from neuromancer.state_experiment import arrays
from neuromancer.supervisor import Deadline
R=Path(__file__).resolve().parent;out=R/'replay';out.mkdir(exist_ok=False);source=R/'trials/n0_r45';dline=Deadline.from_environment();dline.check();began=time.perf_counter();count=0
engine=BrianEngine(Config(network_id=0,replicate_id=45,trial_id='m005a7-n0-r45'))
try:
 pref=engine.run_commands(schedule(engine,prefix_schedule()));data=arrays(pref)
 with np.load(source/'prefix.npz') as old:
  for key in old.files:np.testing.assert_array_equal(data[key],old[key]);count+=1
 c=calibrate([r.observation for r in pref[:2350]],[r.receipt for r in pref[:2350]]);p=Policy(c,'PI10_5');results=[];states=[];intent=[]
 for second in range(32):
  dline.check();engine.group.gain=.6 if second>=16 else 1.;states.append(p.record());desired=p.desired();prior=engine.previous.copy();commands=[]
  for _ in range(50):u,_=project(desired,prior);commands.append(u);prior=u
  block=engine.run_commands(schedule(engine,commands))
  for r in block:p.accept(r.observation,r.observation.available_us)
  results.extend(block);intent.extend([desired]*50)
 data=arrays(results);data.update(decisions=np.array(states),intent=np.array(intent))
 with np.load(source/'LOSS_PI10_5.npz') as old:
  for key,value in data.items():np.testing.assert_array_equal(value,old[key][:len(value)]);count+=1
  np.testing.assert_array_equal(p.record(),old['decisions'][32]);count+=1
 np.savez_compressed(out/'first32.npz',**data,terminal=np.array(p.record()))
 (out/'verification.json').write_text(json.dumps(dict(status='PASS',exact_arrays=count,simulated_seconds=83,wall_s=time.perf_counter()-began,interpretation='Original unsegmented prefix/original32s feedback loop equals extended prefix+first32s; not a new statistical replicate',source=provenance()),indent=2)+'\n');dline.check()
finally:engine.close()
