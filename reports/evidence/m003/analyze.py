"""M003 evaluator: only this step opens reserved neural outcomes."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from neuromancer.identify import Predictor,FAMILIES,HORIZONS,bootstrap,qualification
from neuromancer.identification_experiment import NAMES


def save(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def csv_write(path,rows):
    with path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def classify_precision(gate,network_count):
    required=8 if network_count==10 else 4
    points=all(c['absolute']['mean']>=.04 and c['relative']['mean']>=.10 and c['positive_networks']>=required for c in gate['comparisons'].values())
    if gate['scientific_gate']=='FAIL' and points:gate={**gate,'scientific_gate':'HOLD'}
    return gate


def main(raw,models,output,stationary=None):
    began=time.perf_counter_ns();raw=Path(raw);models=Path(models);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    snapshot=json.loads((models/'manifest.json').read_text())
    for name,digest in snapshot['artifact_sha256'].items():assert hashlib.sha256((models/name).read_bytes()).hexdigest()==digest
    folders=sorted(raw.glob('n*_r*'),key=lambda f:tuple(map(int,f.name[1:].split('_r'))))
    source=json.loads((raw/'provenance.json').read_text());terminal=json.loads((raw/'summary.json').read_text())
    expected={(n,r) for n,r,g in source['jobs']}
    assert {tuple(map(int,f.name[1:].split('_r'))) for f in folders}==expected
    assert terminal['status']=='complete' and len(terminal['trials'])==len(expected)==snapshot['trial_count']
    metrics=[];trial_records=[];arrays={};rows=[];conditioning=[]
    for index,folder in enumerate(folders):
        n,rep=map(int,folder.name[1:].split('_r'));data={}
        for filename in ('prefix','plans','confirmation'):
            with np.load(folder/f'{filename}.npz',allow_pickle=False) as archive:data[filename]={k:archive[k] for k in archive.files}
        prefix=data['prefix'];actual=data['confirmation'];plans=data['plans']['planned']
        np.testing.assert_array_equal(actual['delivered'],plans)
        with np.load(models/folder.name/'forecasts.npz',allow_pickle=False) as archive:frozen={k:archive[k] for k in archive.files}
        selected=json.loads((models/folder.name/'selected.json').read_text())
        common=frozen['rates'];observed=actual['rates'];assert common.shape==(4,6,100,4) and observed.shape==(6,100,4)
        trial=json.loads((folder/'trial.json').read_text());trial_records.append(trial)
        evoked=observed-observed[0];forecast_effect=common-common[:,0,None]
        horizons=(1,10,50,100);mse=np.empty((4,4));bias=np.empty((4,4));ordinary=np.empty((4,6,100,4))
        for hi,h in enumerate(horizons):
            difference=forecast_effect[:,:, :h].mean(axis=2)-evoked[None,:,:h].mean(axis=2)
            mse[:,hi]=(difference[:,1:]**2).mean(axis=(1,2));bias[:,hi]=difference[:,1:].mean(axis=(1,2))
        coverage=np.empty((4,3));width=frozen['widths_hz']
        for mi,family in enumerate(FAMILIES):
            model=Predictor.load(selected[family]);conditioning.append(dict(network_id=n,replicate_id=rep,family=family,**model.diagnostics))
            for ai in range(6):
                for k in range(100):
                    y=np.vstack([prefix['rates'][-4:],observed[ai,:k]])
                    u=np.vstack([prefix['delivered'][-4:],actual['delivered'][ai,:k]])
                    ordinary[mi,ai,k]=model.forecast(y,u,plans[ai,k:k+1])[0]
            for hi,h in enumerate(HORIZONS):coverage[mi,hi]=(np.abs(common[mi,:,:h].mean(axis=1)-observed[:,:h].mean(axis=1))<=width[mi,hi]).mean()
        residual=observed[None]-ordinary
        ordinary_mse=(residual**2).mean(axis=(1,2,3))
        next_coverage=(np.abs(residual)<=width[:,0,None,None,:]).mean(axis=(1,2,3))
        residual_score=(observed[None,1:,:50].mean(axis=2)-common[:,1:,:50].mean(axis=2)).mean(axis=(1,2))
        flags=((observed[None,1:,:50].mean(axis=2)-common[:,1:,:50].mean(axis=2)).mean(axis=2)<frozen['residual_lower05_hz'][:,None]).mean(axis=1)
        item=dict(network_id=n,replicate_id=rep,is_null=rep==21,evoked_mse=mse.tolist(),evoked_bias_pred_minus_actual=bias.tolist(),
            ordinary_next_mse=ordinary_mse.tolist(),next_coverage=next_coverage.tolist(),common_coverage=coverage.tolist(),
            residual_score_observed_minus_predicted=residual_score.tolist(),residual_flag_fraction=flags.tolist(),
            residual_mean=residual.mean(axis=(1,2,3)).tolist(),residual_sd=residual.reshape(4,-1).std(axis=1,ddof=1).tolist(),
            residual_quantiles=np.quantile(residual.reshape(4,-1),[.025,.5,.975],axis=1).T.tolist(),
            interval_width_hz=(2*width).mean(axis=2).tolist())
        metrics.append(item)
        for mi,family in enumerate(FAMILIES):
            for ai,name in enumerate(NAMES):
                predicted_effect=forecast_effect[mi,ai,:50].mean(axis=0);effect=evoked[ai,:50].mean(axis=0)
                entry=dict(network_id=n,replicate_id=rep,is_null=rep==21,model=family,condition=name,
                    evoked1s_mse=float(np.mean((predicted_effect-effect)**2)),ordinary_next_mse=float(np.mean(residual[mi,ai]**2)),
                    actual_evoked1s_mean_hz=float(effect.mean()),predicted_evoked1s_mean_hz=float(predicted_effect.mean()),
                    common1s_observed_minus_predicted_hz=float((observed[ai,:50].mean(axis=0)-common[mi,ai,:50].mean(axis=0)).mean()))
                for j in range(4):entry[f'actual_sector{j}_hz']=float(effect[j]);entry[f'predicted_sector{j}_hz']=float(predicted_effect[j])
                rows.append(entry)
        per=dict(prefix_counts=prefix['counts'],prefix_rates=prefix['rates'],prefix_delivered=prefix['delivered'],
            prefix_desired=prefix['desired'],planned=plans,desired=data['plans']['desired'],
            counts=actual['counts'],rates=observed,delivered=actual['delivered'],neurons=actual['neurons'],
            recording=actual['recording'],stimulation=actual['stimulation'],forecast=common,ordinary=ordinary,
            interval_halfwidth=width,residual_threshold=frozen['residual_lower05_hz'])
        for key,value in per.items():
            if key not in arrays:arrays[key]=np.empty((len(folders),*value.shape),dtype=value.dtype)
            arrays[key][index]=value
    arrays['identities']=np.array([[m['network_id'],m['replicate_id']] for m in metrics],dtype=np.int64)
    np.savez_compressed(output/'identification_data.npz',**arrays)
    csv_write(output/'all_predictions.csv',rows);save(output/'trial_metrics.json',metrics);save(output/'trial_provenance.json',trial_records)
    save(output/'conditioning.json',conditioning);save(output/'selection.json',json.loads((models/'selection.json').read_text()))
    networks=[];network_rows=[]
    for n in sorted({m['network_id'] for m in metrics if not m['is_null']}):
        selected=[m for m in metrics if m['network_id']==n and not m['is_null']]
        record=dict(network_id=n,replicates=[m['replicate_id'] for m in selected])
        for key in ('evoked_mse','evoked_bias_pred_minus_actual','ordinary_next_mse','next_coverage','common_coverage','residual_score_observed_minus_predicted','residual_flag_fraction','residual_mean','residual_sd','interval_width_hz'):
            record[key]=np.mean([m[key] for m in selected],axis=0).tolist()
        networks.append(record)
        row=dict(network_id=n)
        for mi,family in enumerate(FAMILIES):row[family+'_evoked1s_mse']=record['evoked_mse'][mi][2];row[family+'_ordinary_next_mse']=record['ordinary_next_mse'][mi]
        network_rows.append(row)
    network_mse=np.array([n['evoked_mse'] for n in networks])[:,:,2]
    gate=classify_precision(qualification(network_mse),len(networks))
    nulls=[dict(network_id=m['network_id'],replicate_id=m['replicate_id'],ARX_false_response_rms_hz=float(np.sqrt(m['evoked_mse'][2][2])),warning_above_point2=bool(m['evoked_mse'][2][2]>.04)) for m in metrics if m['is_null']]
    summary=json.loads((raw/'summary.json').read_text());provenance=json.loads((raw/'provenance.json').read_text())
    result=dict(**gate,stage=provenance['stage'],execution_complete=summary['status']=='complete',trials=len(metrics),branches=6*len(metrics),
        networks=networks,null_controls=nulls,network_mean_evoked_mse=bootstrap(network_mse),
        ordinary_next_mse=bootstrap(np.array([n['ordinary_next_mse'] for n in networks])),
        common_coverage=bootstrap(np.array([n['common_coverage'] for n in networks])),
        next_coverage=bootstrap(np.array([n['next_coverage'] for n in networks])),
        scientific_wall_s=summary['wall_ns']/1e9,peak_worker_rss_bytes=max(t['peak_rss_bytes'] for t in trial_records),
        constraint_violations=sum(c['violations'] for t in trial_records for c in t['receipts']))
    if stationary:
        old=json.loads((Path(stationary)/'trial_metrics.json').read_text());paired=[]
        for m in metrics:
            ref=next(v for v in old if v['network_id']==m['network_id'] and v['replicate_id']==m['replicate_id'])
            paired.append((ref,m))
        x=np.array([v[0]['residual_score_observed_minus_predicted'][2] for v in paired]);z=np.array([v[1]['residual_score_observed_minus_predicted'][2] for v in paired])
        auc=lambda a,b:((b[:,None]<a[None,:])+.5*(b[:,None]==a[None,:])).mean()
        draws=np.random.default_rng(20261030).integers(0,len(x),(10000,len(x)))
        aucs=np.array([auc(x[d],z[d]) for d in draws])
        stress=dict(residual_auc=dict(mean=float(auc(x,z)),lower=float(np.quantile(aucs,.025)),upper=float(np.quantile(aucs,.975))))
        for key in ('evoked_mse','evoked_bias_pred_minus_actual','ordinary_next_mse','next_coverage','common_coverage','residual_score_observed_minus_predicted','residual_flag_fraction','residual_mean','residual_sd'):
            d=np.array([np.array(m[key])-np.array(ref[key]) for ref,m in paired]);stress[key+'_change']=bootstrap(d)
        stress['ARX_stationary_false_positive_fraction']=bootstrap([ref['residual_flag_fraction'][2] for ref,m in paired])
        stress['ARX_changed_true_positive_fraction']=bootstrap([m['residual_flag_fraction'][2] for ref,m in paired])
        result['efficacy_stress']=stress
    save(output/'comparison.json',result);csv_write(output/'network_metrics.csv',network_rows)
    save(output/'raw_summary.json',summary);save(output/'raw_provenance.json',provenance)
    save(output/'analysis_lineage.json',dict(source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        model_manifest_sha256=hashlib.sha256((models/'manifest.json').read_bytes()).hexdigest(),
        predictor_sha256=snapshot['predictor_sha256'],model_source_sha256=snapshot['source_sha256'],wall_ns=time.perf_counter_ns()-began,
        identities=arrays['identities'].tolist(),families=FAMILIES,horizon_bins=[1,10,50,100]))
    print(json.dumps({k:v for k,v in result.items() if k not in ('networks',)},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('raw');parser.add_argument('models');parser.add_argument('output');parser.add_argument('--stationary')
    args=parser.parse_args();main(args.raw,args.models,args.output,args.stationary)
