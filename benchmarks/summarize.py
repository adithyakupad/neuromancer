"""Compare identical benchmark stages; no scientific endpoint analysis."""
import json,sys
from pathlib import Path
import numpy as np

def summarize(root):
 p=Path(root);m=json.loads((p/'micro/result.json').read_text());n=json.loads((p/'neural/result.json').read_text());out={}
 for key in ('planner','bank','rls','fir'):
  a=np.array([x['wall_s'] for x in m[key]])*1000;out[key+'_ms']={k:float(v) for k,v in zip(('p50','p95','p99','max'),np.quantile(a,[.5,.95,.99,1]))}
 for chunk in (False,True):
  a=np.array([x['wall_s'] for x in n['rows'] if x['chunked']==chunk]);out['chunked_s' if chunk else 'block_s']=float(np.median(a))
 out['noise_s']=float(np.median([x['wall_s'] for x in m['noise']]));out['noise_peak_traced_bytes']=max(x['peak_traced_bytes'] for x in m['noise']);out['neural_peak_rss_bytes']=json.loads((p/'neural/process.json').read_text())['peak_rss_bytes'];out['signature']=m['signature'];out['neural_signatures']=[x['signature'] for x in n['rows']];out['noise_hashes']=[(x['fine'],x['effective']) for x in m['noise']]
 out['workers']={str(i):json.loads((p/f'workers{i}.json').read_text()) for i in (1,2)};out['storage']=m['storage'];out['startup_s']=[x['wall_s'] for x in json.loads((p/'startup.json').read_text())];first=json.loads((p/'micro_supervision/terminal.json').read_text());remaining=json.loads((p/'complete.json').read_text())['remaining_s'];out['workflow_s']=(first['deadline_ns']-remaining*1e9-first['started_ns'])/1e9;return out
if __name__=='__main__':
 results=[summarize(p) for p in sys.argv[1:]];r={'stages':results}
 if len(results)==2:
  a,b=results;r['exact_equivalence']=all(a[k]==b[k] for k in ('signature','neural_signatures','noise_hashes'));r['speedups']={k:a[k]/b[k] for k in ('block_s','chunked_s','noise_s','workflow_s')};r['planner_p95_reduction']=1-b['planner_ms']['p95']/a['planner_ms']['p95'];assert r['exact_equivalence']
 print(json.dumps(r,indent=2))
