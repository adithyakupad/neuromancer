"""Supplementary engineering workflow; synthetic calibration, not efficacy study."""
import argparse,hashlib,json,resource,sys,time
from pathlib import Path
import numpy as np
from neuromancer._brian import BrianEngine
from neuromancer.substrate import Config,Command
from neuromancer.control import ControlCalibration,Policy,project
from neuromancer.predictive import Initialization,PredictiveController
from v1_1 import fixture,measured
from neuromancer.supervisor import Deadline,atomic_json

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);d=Deadline.from_environment();rows=[];dig=hashlib.sha256()
 cal=ControlCalibration(8.,.1,.0275,1/.0275,9.,(0.,.8,1.6,2.4,3.2),True,'synthetic-not-a-research-calibration')
 for rep in range(3):
  d.check();engine,init=measured(lambda:BrianEngine(Config()));policy=Policy(cal,'PI10_5',start_us=0,aggregate_bins=5);previous=np.zeros(4);decisions=[];observations=[];commands=[];states=[];start=time.perf_counter();cpu=time.process_time()
  for k in range(50):
   d.check();t=engine.time_us
   current,lat=measured(lambda:project(policy.desired(),previous));decisions.append(lat)
   result=engine.advance(Command('trial',str(k),t,tuple(current)),t+20000)
   policy.accept(result.observation,t+20000);previous=current;commands.append(current);observations.append(result.observation.counts);states.append(policy.record())
  wall=time.perf_counter()-start;cpu=time.process_time()-cpu
  path=a.output/f'workflow{rep}.npz';_,write=measured(lambda:np.savez_compressed(path,observations=observations,commands=commands,states=states));loaded,read=measured(lambda:dict(np.load(path)))
  for key in ('observations','commands','states'):dig.update(np.ascontiguousarray(loaded[key]).tobytes())
  engine.reset();assert engine.time_us==0;engine.close();rows.append(dict(initialization=init,wall_s=wall,cpu_s=cpu,decisions=decisions,write=write,read=read,bytes=path.stat().st_size))
 rec,z,v,p,u,y=fixture();initial=Initialization(rec,p,np.zeros((9,4)),cal,'benchmark');lat=[];updates=[];controller=PredictiveController(initial,'RLS');actions=[]
 # Public synthetic observations/receipts; no Brian state is passed to predictor.
 from neuromancer.observation import Observation
 from neuromancer.substrate import Receipt
 for k in range(500):
  d.check();t=controller.time_us;c,l=measured(lambda:controller.command(t));lat.append(dict(**l,planning=k%50==0));o=Observation('benchmark',t,t+20000,t+20000,(1,)*20,(10.,)*20,(20000,)*20,(True,)*20,(),(),(10.,)*4,(10.,)*4,True);r=Receipt('benchmark',c.command_id,t,t,t+20000,c.current_pA,c.current_pA,'delivered','');_,l=measured(lambda:controller.accept(o,r,t+20000));updates.append(l);actions.append(c.current_pA)
 assert controller.failure is None
 dig.update(np.asarray(actions).tobytes());dig.update(controller.model.theta.tobytes());dig.update(controller.model.p.tobytes())
 atomic_json(a.output/'result.json',dict(rows=rows,controller_commands=lat,controller_updates=updates,signature=dig.hexdigest(),controller_failures=controller.failure,fallbacks=sum(x['safe'] for x in controller.events),rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),limitations='PI synthetic calibration,100ms aggregation; no scientific tracking endpoint; predictive stream synthetic,10 planning decisions/500 bins'))
if __name__=='__main__':main()
