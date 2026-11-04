"""Bounded record-retention probe; fixed development network/noise, no science."""
import argparse,hashlib,json,time,resource,sys
from pathlib import Path
import numpy as np
from neuromancer._brian import BrianEngine
from neuromancer.substrate import Config
from neuromancer.diagnostic import run_hold
from neuromancer.supervisor import Deadline,atomic_json
from v1_1 import measured
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False);d=Deadline.from_environment();rows=[]
for retain in (False,True):
 for rep in range(3):
  d.check();e,init=measured(lambda:BrianEngine(Config(retain_spikes=retain)));(rs,_),t=measured(lambda:run_hold(e,1,60));obs=np.array([r.observation.counts for r in rs]);events=[(r.observation.event_time_us,r.observation.channel_id) for r in rs];payload=obs.tobytes()+json.dumps(events).encode();rows.append(dict(retain=retain,repeat=rep,initialization=init,**t,observation_signature=hashlib.sha256(payload).hexdigest(),population_count=int(sum(e.monitor.count)),retained_events=len(e.monitor.i),retained_event_payload_bytes=np.asarray(e.monitor.i).nbytes+np.asarray(e.monitor.t).nbytes));e.close()
assert len({x['observation_signature'] for x in rows})==1 and len({x['population_count'] for x in rows})==1
atomic_json(args.output/'result.json',dict(rows=rows,peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),limits='one process high-water across all cases; not incremental retention RSS; no neural model changes'))
