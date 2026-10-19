"""M003.1 evaluator opens reserved outcomes only after saved model forecasts."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from neuromancer.necessity import FAMILIES,forecast,gate
from neuromancer.necessity_experiment import NAMES
from fit_models import save,digest


def csv_write(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def bootstrap(value):
    a=np.asarray(value);index=np.random.default_rng(20261101).integers(0,len(a),(10000,len(a)));draws=a[index].mean(axis=1)
    return dict(mean=a.mean(axis=0).tolist(),lower=np.quantile(draws,.025,axis=0).tolist(),upper=np.quantile(draws,.975,axis=0).tolist())


def main(raw,models,output):
    start=time.perf_counter();raw=Path(raw);models=Path(models);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((models/'manifest.json').read_text())
    for name,h in manifest['artifact_sha256'].items():assert digest(models/name)==h
    selection=json.loads((models/'selection.json').read_text());comp=FAMILIES.index(selection['primary_competitor'])
    source=json.loads((raw/'provenance.json').read_text());expected={(n,r) for n,r,g in source['jobs']}
    folders=sorted(raw.glob('n*_r*'),key=lambda p:tuple(map(int,p.name[1:].split('_r'))));assert {tuple(map(int,p.name[1:].split('_r'))) for p in folders}==expected
    trials=[];predrows=[];exposures=[];archives={};provenance=[];conditions=[]
    for folder in folders:
        n,r=map(int,folder.name[1:].split('_r'));snapshot=json.loads((models/folder.name/'snapshot.json').read_text())
        assert snapshot['selected_sha256']==digest(models/folder.name/'selected.json') and snapshot['forecasts_sha256']==digest(models/folder.name/'forecasts.npz')
        for name,h in snapshot['input_sha256'].items():assert digest(folder/name)==h
        data={}
        for name in ('prefix','plans','confirmation'):
            with np.load(folder/f'{name}.npz',allow_pickle=False) as z:data[name]={k:z[k] for k in z.files}
        prefix=data['prefix'];actual=data['confirmation'];plans=data['plans']['planned'];np.testing.assert_array_equal(plans,actual['delivered'])
        with np.load(models/folder.name/'forecasts.npz',allow_pickle=False) as z:common=z['rates'];width=z['widths'];ablation=z['ARX_mean_history'];calibration_mae=z['calibration_mae'];calibration_coverage=z['calibration_coverage']
        selected=json.loads((models/folder.name/'selected.json').read_text());rates=actual['rates'];effect=rates-rates[0];prediction=common-common[:,0,None]
        ordinary=np.empty_like(common)
        for mi,family in enumerate(FAMILIES):
            for a in range(6):
                for k in range(100):
                    history=np.vstack([prefix['rates'][-4:],rates[a,:k]]);past=np.vstack([prefix['delivered'][-50:],actual['delivered'][a,:k]])
                    ordinary[mi,a,k]=forecast(selected[family],history,past,plans[a,k:k+1])[0]
        error=rates[None]-ordinary;mse=[];bias=[];absolute=[];coverage=[];dynamic=[]
        for hi,h in enumerate((1,10,50,100)):
            pe=prediction[:,:,:h].mean(axis=2);truth=effect[:,:h].mean(axis=1);delta=pe-truth[None]
            mse.append((delta[:,1:]**2).mean(axis=(1,2)));bias.append(delta[:,1:].mean(axis=(1,2)))
            absolute.append(((common[:,:,:h].mean(axis=2)-rates[None,:,:h].mean(axis=2))**2).mean(axis=(1,2)))
            coverage.append((np.abs(common[:,:,:h].mean(axis=2)-rates[None,:,:h].mean(axis=2))<=width[:,hi,None,:]).mean(axis=(1,2)))
            dynamic.append(np.array([np.mean(((pe[:,a]-pe[:,b])-(truth[a]-truth[b]))**2,axis=1) for a,b in ((1,2),(3,4))]).T)
        acf=np.empty((7,6,4));constant=0
        for m in range(7):
            for a in range(6):
                for c in range(4):
                    left=error[m,a,:-1,c];right=error[m,a,1:,c]
                    if left.std()==0 or right.std()==0:acf[m,a,c]=0;constant+=1
                    else:acf[m,a,c]=np.corrcoef(left,right)[0,1]
        item=dict(calibration_mae=calibration_mae.tolist(),calibration_coverage=calibration_coverage.tolist(),network_id=n,replicate_id=r,is_null=r==25,evoked_mse=np.array(mse).T.tolist(),evoked_bias=np.array(bias).T.tolist(),
            absolute_mse=np.array(absolute).T.tolist(),coverage=np.array(coverage).T.tolist(),dynamic_contrast_mse=np.moveaxis(dynamic,0,1).tolist(),
            ordinary_mse=(error**2).mean(axis=(1,2,3)).tolist(),ordinary_coverage=(np.abs(error)<=width[:,0,None,None,:]).mean(axis=(1,2,3)).tolist(),
            residual_mean=error.mean(axis=(1,2,3)).tolist(),residual_lag1_acf=acf.mean(axis=(1,2)).tolist(),constant_residual_series=constant,
            interval_width=(2*width).mean(axis=2).tolist(),origin_history_contrast_difference=float(np.max(np.abs(prediction[2]-(ablation-ablation[0])))))
        assert item['origin_history_contrast_difference']<1e-9;trials.append(item)
        trial=json.loads((folder/'trial.json').read_text());provenance.append(trial)
        for a,name in enumerate(NAMES):
            receipt=trial['receipts'][a];exposures.append(dict(network_id=n,replicate_id=r,condition=name,**{k:receipt[k] for k in ('exposure_pA_s','model_charge_pC','maximum_total_pA','maximum_slew_pA','violations')}))
            for mi,family in enumerate(FAMILIES):
                pe=prediction[mi,a,:50].mean(axis=0);truth=effect[a,:50].mean(axis=0)
                row=dict(network_id=n,replicate_id=r,is_null=r==25,model=family,condition=name,evoked1s_mse=float(np.mean((pe-truth)**2)),ordinary_mse=float(np.mean(error[mi,a]**2)))
                for c in range(4):row[f'actual_sector{c}_hz']=float(truth[c]);row[f'predicted_sector{c}_hz']=float(pe[c])
                predrows.append(row)
        for name,m in selected.items():conditions.append(dict(network_id=n,replicate_id=r,model=name,**m['diagnostics']))
        arrays=dict(prefix_counts=prefix['counts'],prefix_rates=prefix['rates'],prefix_delivered=prefix['delivered'],prefix_desired=prefix['desired'],desired=data['plans']['desired'],planned=plans,
            counts=actual['counts'],rates=rates,delivered=actual['delivered'],neurons=actual['neurons'],recording=actual['recording'],stimulation=actual['stimulation'],forecast=common,ordinary=ordinary,width=width,ARX_mean_history=ablation)
        for key,value in arrays.items():archives.setdefault(key,[]).append(value)
        if time.perf_counter()-start>900:raise TimeoutError('Analysis wall cap; raw/models retained')
    np.savez_compressed(output/'data.npz',**{k:np.array(v) for k,v in archives.items()},identities=np.array([[t['network_id'],t['replicate_id']] for t in trials]))
    networks=[]
    metrics=('calibration_mae','calibration_coverage','evoked_mse','evoked_bias','absolute_mse','coverage','dynamic_contrast_mse','ordinary_mse','ordinary_coverage','residual_mean','residual_lag1_acf','interval_width')
    for n in range(10):
        subset=[t for t in trials if t['network_id']==n and not t['is_null']];assert len(subset)==3
        networks.append(dict(network_id=n,**{key:np.mean([t[key] for t in subset],axis=0).tolist() for key in metrics}))
    primary=np.array([v['evoked_mse'] for v in networks])[:,:,2];outcome=gate(primary[:,comp],primary[:,2])
    result=dict(**outcome,primary_competitor=selection['primary_competitor'],trials=len(trials),branches=len(trials)*6,
        comparisons={f:gate(primary[:,FAMILIES.index(f)],primary[:,2]) for f in ('STATIC','FIR','AR','ARX_SHUFFLED')},
        network_summary={key:bootstrap([n[key] for n in networks]) for key in metrics},networks=networks,
        null_controls=[dict(network_id=t['network_id'],replicate_id=t['replicate_id'],false_response_rms=np.sqrt(np.array(t['evoked_mse'])[:,2]).tolist()) for t in trials if t['is_null']],
        maximum_origin_history_effect_difference=max(t['origin_history_contrast_difference'] for t in trials),
        acquisition_wall_s=json.loads((raw/'summary.json').read_text())['wall_ns']/1e9,fit_wall_s=manifest['wall_s'],analysis_wall_s=time.perf_counter()-start,
        peak_worker_rss_bytes=max(t['peak_rss_bytes'] for t in provenance),constraint_violations=sum(e['violations'] for e in exposures))
    save(output/'comparison.json',result);save(output/'trial_metrics.json',trials);save(output/'trial_provenance.json',provenance);save(output/'conditioning.json',conditions);save(output/'selection.json',selection)
    csv_write(output/'all_predictions.csv',predrows);csv_write(output/'delivered_exposure.csv',exposures)
    csv_write(output/'network_metrics.csv',[dict(network_id=n['network_id'],**{f:primary[i,j] for j,f in enumerate(FAMILIES)}) for i,n in enumerate(networks)])
    save(output/'lineage.json',dict(analysis_sha256=digest(Path(__file__)),model_manifest_sha256=digest(models/'manifest.json'),raw_summary_sha256=digest(raw/'summary.json'),model_source_sha256=digest(Path('src/neuromancer/necessity.py'))))
    print(json.dumps({k:result[k] for k in ('scientific_gate','primary_competitor','absolute','relative','positive_networks')},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('models');p.add_argument('output');a=p.parse_args();main(a.raw,a.models,a.output)
