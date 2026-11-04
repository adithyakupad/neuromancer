"""Publish derived evaluator-only oracle paths; original scientific outputs unchanged."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from neuromancer.online_identify import features,standardized

p=argparse.ArgumentParser()
p.add_argument('--dev',type=Path,required=True);p.add_argument('--dev-replay',type=Path,required=True)
p.add_argument('--validation',type=Path,required=True);p.add_argument('--validation-replay',type=Path,required=True);p.add_argument('--analysis',type=Path,required=True)
a=p.parse_args();out=a.analysis/'derived_oracle';out.mkdir(exist_ok=False);count=0
metrics={f"n{r['network']}_r{r['replicate']}_{r['condition']}_{int(float(r['origin_s']))}":float(r['mse_hz2']) for r in csv.DictReader((a.analysis/'rolling.csv').open()) if r['model']=='ORACLE'}
for raw,replay in ((a.dev,a.dev_replay),(a.validation,a.validation_replay)):
    for trial in sorted(raw.glob('n*_r*')):
        with np.load(trial/'public.npz') as f:u=f['delivered'].copy();y=f['rates'].copy()
        with np.load(trial/'evaluator.npz') as f:g=f['gain'].copy()
        record=json.loads((replay/trial.name/'initial.json').read_text())['fir'];coef=np.array(record['coef']);effective=u*g[:,None];paths=[];probes=[]
        for k in range(1950,3950,50):
            pred=standardized(record,features(effective,np.arange(k,k+50)))@coef+record['output_mean'];paths.append(pred)
            error=float(np.mean((pred.mean(axis=0)-y[k:k+50].mean(axis=0))**2))
            assert abs(error-metrics[f'{trial.name}_{k//50}'])<1e-12;count+=1
        for t in (54,64,74):
            k=t*50
            with np.load(trial/f'probe{t}_plans.npz') as f:plans=f['planned'].copy()
            branches=[]
            for plan in plans:
                uu=np.vstack([effective[k-9:k],plan*g[k:k+50,None]])
                branches.append(standardized(record,features(uu,np.arange(9,59)))@coef+record['output_mean'])
            probes.append(branches)
        np.savez_compressed(out/f'{trial.name}.npz',rolling=np.array(paths),probes=np.array(probes))
(out/'publication.json').write_text(json.dumps(dict(status='PASS',rolling_metric_checks=count,
    purpose='Derived serialization after primary analysis, not learner input/refit/new result',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
print('Derived oracle archives PASS',count)
