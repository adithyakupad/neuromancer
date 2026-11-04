"""Freeze M003 selection and forecasts using prefix/plan files only."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
import numpy as np
from neuromancer.identify import fit,GRID,FAMILIES,HYPER_ORIGINS,CAL_ORIGINS,HORIZONS


def save(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def prefix(folder):
    with np.load(folder/'prefix.npz',allow_pickle=False) as archive:data={k:archive[k] for k in archive.files}
    if data['rates'].shape!=(3350,4) or data['counts'].shape!=(3350,20):raise ValueError('Incomplete prefix')
    np.testing.assert_array_equal(data['delivered'],data['planned'])
    assert np.isfinite(data['rates'][749:]).all() and data['counts'].min()>=0
    return data


def errors(model,data,origins,h):
    #Future commands are the predeclared plan, not future delivery receipts.
    return np.array([model.forecast(data['rates'][:k],data['delivered'][:k],data['planned'][k:k+h]).mean(axis=0)-data['rates'][k:k+h].mean(axis=0) for k in origins])


def candidate_key(p,lam):return f'p{p}_lambda{lam}'


def choose(scores,p=None):
    eligible=[row for row in scores if row['mean'] is not None and (p is None or row['p']==p)]
    if not eligible:raise ValueError('No valid global candidate; no scientific qualification')
    best=min(row['mean'] for row in eligible)
    return min((row for row in eligible if row['mean']<=best+1e-12),key=lambda row:(row['p'],-row['lambda']))


def shared_selection(scores):
    ar=choose(scores['AR']);shared=ar['p']
    return {'AR':ar,**{family:choose(scores[family],shared) for family in ('ARX','SHUFFLED')}}


def main(raw,output,selection=None,reuse=None):
    began=time.perf_counter_ns();raw=Path(raw);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    folders=sorted(raw.glob('n*_r*'),key=lambda f:tuple(map(int,f.name[1:].split('_r'))))
    summary=json.loads((raw/'summary.json').read_text())
    if not folders or summary['status']!='complete' or len(folders)!=len(summary['trials']):raise ValueError('Incomplete acquisition')
    if reuse:
        reuse=Path(reuse);selection_record=json.loads((reuse/'selection.json').read_text());save(output/'selection.json',selection_record)
        for folder in folders:
            target=output/folder.name;target.mkdir()
            original=json.loads((reuse/folder.name/'snapshot.json').read_text())
            for filename in ('prefix.npz','plans.npz'):
                assert hashlib.sha256((folder/filename).read_bytes()).hexdigest()==original['input_sha256'][filename]
            for filename in ('selected.json','forecasts.npz','snapshot.json'):
                shutil.copyfile(reuse/folder.name/filename,target/filename)
    else:
        all_candidates={};scores={family:[] for family in FAMILIES[1:]}
        selection_record=json.loads(Path(selection).read_text()) if selection else None
        for folder in folders:
            target=output/folder.name;target.mkdir();data=prefix(folder);candidates={}
            is_null=folder.name.endswith('_r21')
            if selection_record or is_null:continue
            for family in FAMILIES[1:]:
                candidates[family]={}
                for p,lam in GRID:
                    model=fit(data['rates'],data['delivered'],family,p,lam);record=model.record()
                    loss=None;reason=None
                    if model.diagnostics['valid']:
                        try:loss=float(np.mean(errors(model,data,HYPER_ORIGINS,50)**2))
                        except ValueError as error:reason=str(error)
                    record.update(validation_mse=loss,validation_error=reason)
                    candidates[family][candidate_key(p,lam)]=record
            save(target/'candidates.json',candidates);all_candidates[folder.name]=candidates
        if selection_record is None:
            if len(all_candidates)!=30:raise ValueError('Selection needs all30 development prefixes')
            for family in FAMILIES[1:]:
                for p,lam in GRID:
                    values=[records[family][candidate_key(p,lam)]['validation_mse'] for records in all_candidates.values()]
                    scores[family].append(dict(p=p,lambda_value=lam,**{'lambda':lam},mean=float(np.mean(values)) if all(v is not None for v in values) else None,per_trial=values))
            families=shared_selection(scores);shared=families['AR']['p']
            selection_record=dict(shared_p=shared,families={f:{'p':v['p'],'lambda':v['lambda']} for f,v in families.items()},scores=scores,
                rule='Shared lag selected by AR-only chronology, then independent penalties at that lag; no reserved data read')
        assert len({r['p'] for r in selection_record['families'].values()})==1
        save(output/'selection.json',selection_record)
        for folder in folders:
            target=output/folder.name;data=prefix(folder);models={};widths=[];thresholds=[]
            for family in FAMILIES:
                cfg=selection_record['families'].get(family,dict(p=1,**{'lambda':.001}))
                model=fit(data['rates'],data['delivered'],family,cfg['p'],cfg['lambda'])
                if not model.diagnostics['valid']:raise ValueError(f'{folder.name}/{family}: selected estimator invalid')
                models[family]=model
                residuals=[errors(model,data,CAL_ORIGINS,h) for h in HORIZONS]
                widths.append([np.quantile(np.abs(e),.95,axis=0,method='higher').tolist() for e in residuals])
                thresholds.append(float(np.quantile(-residuals[-1].mean(axis=1),.05,method='lower')))
            save(target/'selected.json',{f:m.record() for f,m in models.items()})
            with np.load(folder/'plans.npz',allow_pickle=False) as archive:plans=archive['planned']
            forecasts=np.array([[m.forecast(data['rates'],data['delivered'],plan) for plan in plans] for m in models.values()])
            np.savez_compressed(target/'forecasts.npz',rates=forecasts,widths_hz=np.array(widths),residual_lower05_hz=thresholds)
            save(target/'snapshot.json',dict(input_sha256={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ('prefix.npz','plans.npz')},
                model_sha256=hashlib.sha256((target/'selected.json').read_bytes()).hexdigest(),
                forecast_sha256=hashlib.sha256((target/'forecasts.npz').read_bytes()).hexdigest(),
                trained_stop_us=47_000_000,interval_calibration_stop_us=63_000_000,forecast_origin_us=67_000_000,
                reserved_outcomes_read=False))
    files={str(f.relative_to(output)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(output.rglob('*')) if f.is_file()}
    save(output/'manifest.json',dict(status='complete',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        predictor_sha256=hashlib.sha256(Path(__import__('neuromancer.identify',fromlist=['x']).__file__).read_bytes()).hexdigest(),
        fitting_or_reuse='reuse' if reuse else 'fit',trial_count=len(folders),wall_ns=time.perf_counter_ns()-began,artifact_sha256=files))
    print(json.dumps(selection_record['families'],indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('raw',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--selection',type=Path);parser.add_argument('--reuse',type=Path)
    args=parser.parse_args();main(args.raw,args.output,args.selection,args.reuse)
