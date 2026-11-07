"""Derived static seed/parameter audit and reproducible per-kind latency reduction."""
import hashlib,json
from dataclasses import asdict
from pathlib import Path
import numpy as np
from neuromancer.substrate import Config
from neuromancer._brian import realization,innovations,digest
from neuromancer.supervisor import Deadline,atomic_json
R=Path(__file__).resolve().parent

def main():
 d=Deadline.from_environment();d.check();config=Config(network_id=0,replicate_id=60,trial_id='m005b1-smoke-n0-r60');summary=json.loads((R/'smoke/summary.json').read_text());params=realization(config);hashes={k:digest(v) for k,v in params.items()};old=json.loads(Path('reports/evidence/m005a_7/trials/n0_r45/trial.json').read_text())['engine']['metadata']['parameter_hashes'];assert hashes==old
 assert not np.intersect1d(params['recording'],params['stimulation']).size
 checks={}
 for block in (0,50,51,52):
  effective,fine=innovations(config,block);expected=dict(fine=fine,effective=digest(effective))
  assert summary['branches']['RLS']['noise'][str(block)]==expected;checks[str(block)]=expected
 result=dict(status='PASS',config=asdict(config),parameter_hashes=hashes,unchanged_n0_parameter_hashes=True,disjoint_membership=True,noise_blocks_regenerated=checks,scope='Post-run deterministic static reconstruction, not a newly measured runtime parameter snapshot',source_revision=summary['source']['head'])
 atomic_json(R/'lineage.json',result)
 perf={}
 def stats(x):
  x=np.asarray(x,float)/1e6;return dict(n=len(x),p50_ms=float(np.quantile(x,.5)),p95_ms=float(np.quantile(x,.95)),p99_ms=float(np.quantile(x,.99)),max_ms=float(x.max()),over20ms=int((x>20).sum()),over250ms=int((x>250).sum()))
 for kind in ('FIXED','RLS','BIAS','RLS_REPLAY'):
  a=dict(np.load(R/'smoke'/f'{kind}.npz'));p=[dict(np.load(R/'smoke'/f'{kind}_plan{j}.npz')) for j in range(2)];perf[kind]=dict(command=stats(a['command_ns']),observation_update=stats(a['update_ns']),planner=stats([x['elapsed_ns'].item() for x in p]),complete_decision=stats(a['command_ns'][[0,50]]+np.array([0,a['update_ns'][49]])))
 assert perf==json.loads((R/'performance_by_kind.json').read_text());d.check()
if __name__=='__main__':main()
