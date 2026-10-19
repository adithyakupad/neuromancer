"""Final independent archive/membership/bootstrap checks; no fitting or new gates."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np


def main(output):
    output=Path(output);r=json.load(open(output/'comparison.json'));networks=r['networks']
    indices=np.random.default_rng(20261101).integers(0,10,(10000,10));checks=0
    for key,ci in r['network_summary'].items():
        a=np.array([v[key] for v in networks]);draws=a[indices].mean(axis=1)
        for name,value in [('mean',a.mean(axis=0)),('lower',np.quantile(draws,.025,axis=0)),('upper',np.quantile(draws,.975,axis=0))]:
            np.testing.assert_allclose(value,ci[name],atol=1e-12,rtol=0);checks+=1
    order=('STATIC','FIR','ARX','AR','STATIC_SHUFFLED','FIR_SHUFFLED','ARX_SHUFFLED');j=order.index(r['primary_competitor']);m=np.array([v['evoked_mse'] for v in networks])[:,:,2]
    relative=(m[:,j]-m[:,2])/np.maximum(m[:,j],.04);draws=relative[indices].mean(axis=1)
    np.testing.assert_allclose([relative.mean(),*np.quantile(draws,[.025,.975])],[r['relative'][k] for k in ('mean','lower','upper')],atol=1e-12,rtol=0)
    with np.load(output/'data.npz',allow_pickle=False) as a:d={k:a[k] for k in a.files}
    with np.load('reports/evidence/m003/results/D/identification_data.npz',allow_pickle=False) as a:prior={k:a[k] for k in ('identities','recording','stimulation')}
    collisions=[]
    for i,(n,rep) in enumerate(d['identities']):
        old=np.flatnonzero(prior['identities'][:,0]==n)[0]
        for field in ('recording','stimulation'):np.testing.assert_array_equal(d[field][i],prior[field][old])
        same=sum(np.array_equal(d['desired'][i,5],d['prefix_desired'][i,k:k+100]) for k in range(750,2251,25))
        collisions.append(dict(network_id=int(n),replicate_id=int(rep),identical_fitting_windows=int(same)))
    rows=list(csv.DictReader(open(output/'all_predictions.csv')));condition_stats=[]
    for model in order:
        for condition in ('S','SHORT','LONG','NEAR','FAR','R'):
            means=[];actual=[];predicted=[]
            for n in range(10):
                subset=[v for v in rows if int(v['network_id'])==n and v['is_null']=='False' and v['model']==model and v['condition']==condition];assert len(subset)==3
                means.append(np.mean([float(v['evoked1s_mse']) for v in subset]))
                actual.append(np.mean([[float(v[f'actual_sector{c}_hz']) for c in range(4)] for v in subset]))
                predicted.append(np.mean([[float(v[f'predicted_sector{c}_hz']) for c in range(4)] for v in subset]))
            ci=np.quantile(np.array(means)[indices].mean(axis=1),[.025,.975])
            condition_stats.append(dict(model=model,condition=condition,network_mse=means,mean_mse=float(np.mean(means)),lower=float(ci[0]),upper=float(ci[1]),mean_actual_effect_hz=float(np.mean(actual)),mean_predicted_effect_hz=float(np.mean(predicted))))
        combined=np.mean([v['network_mse'] for v in condition_stats if v['model']==model and v['condition']!='S'],axis=0)
        np.testing.assert_allclose(combined,m[:,order.index(model)],atol=1e-12,rtol=0)
    (output/'condition_metrics.json').write_text(json.dumps(condition_stats,indent=2)+'\n')
    preserved=json.load(open('reports/evidence/m003_1/preservation.json'))['sha256']
    for name,h in preserved.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h,name
    result=dict(status='PASS',network_bootstrap_fields_checked=checks+3,historical_files_preserved=len(preserved),
        exact_original_membership_trials=len(d['identities']),reserved_random_sequences=collisions,total_collisions=sum(v['identical_fitting_windows'] for v in collisions),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Post-score independent integrity/descriptive audit, no change to source data, fitting, primary or secondary endpoints.')
    (output/'bundle_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
