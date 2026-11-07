"""Completed-observation update plus next-command computation; no neural wait."""
import json
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline,atomic_json
B=Path('reports/evidence/v1_finish/m005b');d=Deadline(**json.loads((B/'analysis_launch.json').read_text())['deadline']);d.check();meta=json.loads((B/'primary/provenance.json').read_text());values={}
for n,r in meta['jobs']:
 f=B/'primary'/f'n{n}_r{r}'
 for branch in json.loads((f/'trial.json').read_text())['branches']:
  a=np.load(f/(branch['name']+'.npz'));cmd=a['command_ns'];update=a['update_ns'];assert len(cmd)==len(update)==3200;cycle=cmd.copy();cycle[1:]+=update[:-1];values.setdefault(branch['controller'],[]).extend(cycle[::50]/1e6)
 d.check()
result={k:dict(count=len(v),p50=float(np.median(v)),p95=float(np.quantile(v,.95)),p99=float(np.quantile(v,.99)),maximum=float(np.max(v))) for k,v in values.items()};atomic_json(B/'cycle_latency.json',dict(units='ms',definition='At fixed1s origins: prior completed-bin controller accept time plus next command time; first command excludes prefix fit. Excludes neural wait, observation construction and archival.250ms cap applies to planner release, not this descriptive sum.',controllers=result));d.check()
