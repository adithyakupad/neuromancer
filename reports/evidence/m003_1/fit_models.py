"""Prefix-only M003.1 selection; never opens confirmation or private trial files."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from neuromancer.necessity import FAMILIES,LAMBDAS,fit,forecast,select


def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def errors(model,data,origins,h):
    return np.array([forecast(model,data['rates'][:k],data['delivered'][:k],data['planned'][k:k+h]).mean(axis=0)-data['rates'][k:k+h].mean(axis=0) for k in origins])


def main(raw,output):
    began=time.perf_counter();raw=Path(raw);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    summary=json.loads((raw/'summary.json').read_text());assert summary['status']=='complete' and len(summary['trials'])==33
    folders=sorted(raw.glob('n*_r*'),key=lambda p:tuple(map(int,p.name[1:].split('_r'))));assert len(folders)==33
    data={};candidates={};scores={};chosen={}
    for folder in folders:
        with np.load(folder/'prefix.npz',allow_pickle=False) as archive:data[folder.name]={k:archive[k] for k in archive.files}
        d=data[folder.name];assert d['rates'].shape==(3350,4)
        np.testing.assert_array_equal(d['delivered'],d['planned']);assert np.isfinite(d['rates'][749:]).all()
        (output/folder.name).mkdir();candidates[folder.name]={}
    for family in FAMILIES:
        base=family.split('_')[0]
        sizes=[chosen[base]['size']] if family.endswith('_SHUFFLED') else {'STATIC':(1,),'FIR':(10,50),'ARX':(1,4),'AR':(1,4)}[family]
        scores[family]=[]
        for size in sizes:
            for lam in LAMBDAS:
                values=[];features=None
                for folder in folders:
                    if folder.name.endswith('_r25'):continue
                    d=data[folder.name];model=fit(d['rates'],d['delivered'],family,size,lam);loss=None;error=None
                    features=model['diagnostics']['features']
                    if model['diagnostics']['valid']:
                        try:loss=float(np.mean(errors(model,d,range(2350,2701,10),50)**2))
                        except ValueError as exc:error=str(exc)
                    model.update(validation_mse=loss,validation_error=error)
                    candidates[folder.name].setdefault(family,[]).append(model);values.append(loss)
                scores[family].append(dict(size=size,**{'lambda':lam},features=features,loss=float(np.mean(values)) if all(v is not None for v in values) else None,per_trial=values))
        if time.perf_counter()-began>900:raise TimeoutError('Frozen fitting wall cap; partial candidates retained')
        for folder in folders:
            if candidates[folder.name]:save(output/folder.name/'candidates.json',candidates[folder.name])
        save(output/'partial_scores.json',scores)
        chosen[family]=select(scores[family]);print(family,{k:v for k,v in chosen[family].items() if k!='per_trial'},flush=True)
    competitor=min((f for f in ('STATIC','FIR')),key=lambda f:(chosen[f]['loss'],chosen[f]['features'],-chosen[f]['lambda']))
    # Explicit tolerance for the preregistered simpler-model tie.
    if abs(chosen['STATIC']['loss']-chosen['FIR']['loss'])<=1e-12:competitor='STATIC'
    selection=dict(models={f:{k:r[k] for k in ('size','lambda','features','loss')} for f,r in chosen.items()},primary_competitor=competitor,scores=scores,
        fitting_rows=[800,2350],hypervalidation_origins=list(range(2350,2701,10)),reserved_outcomes_read=False)
    save(output/'selection.json',selection)
    for folder in folders:
        if time.perf_counter()-began>900:raise TimeoutError('Frozen fitting wall cap')
        d=data[folder.name];models={};widths=[];calibration_mae=[];calibration_coverage=[]
        with np.load(folder/'plans.npz',allow_pickle=False) as archive:plans=archive['planned']
        for family in FAMILIES:
            cfg=chosen[family];model=fit(d['rates'],d['delivered'],family,cfg['size'],cfg['lambda'])
            if not model['diagnostics']['valid']:raise ValueError(f'Invalid selected {folder.name}/{family}')
            models[family]=model
            residuals=[errors(model,d,range(2750,3101,10),h) for h in (1,10,50,100)]
            w=np.array([np.quantile(np.abs(e),.95,axis=0,method='higher') for e in residuals]);widths.append(w)
            calibration_mae.append([float(np.abs(e).mean()) for e in residuals])
            calibration_coverage.append([float((np.abs(e)<=w[h]).mean()) for h,e in enumerate(residuals)])
        selected=output/folder.name;save(selected/'selected.json',models)
        if candidates[folder.name]:save(selected/'candidates.json',candidates[folder.name])
        predicted=np.array([[forecast(m,d['rates'],d['delivered'],plan) for plan in plans] for m in models.values()])
        replaced=np.tile(d['rates'][800:2350].mean(axis=0),(len(d['rates']),1));model=models['ARX']
        ablation=np.array([forecast(model,replaced,d['delivered'],plan) for plan in plans])
        np.testing.assert_allclose(predicted[2]-predicted[2,0],ablation-ablation[0],rtol=0,atol=1e-9)
        np.savez_compressed(selected/'forecasts.npz',rates=predicted,widths=np.array(widths),ARX_mean_history=ablation,calibration_mae=np.array(calibration_mae),calibration_coverage=np.array(calibration_coverage))
        save(selected/'snapshot.json',dict(input_sha256={name:digest(folder/name) for name in ('prefix.npz','plans.npz')},
            selected_sha256=digest(selected/'selected.json'),forecasts_sha256=digest(selected/'forecasts.npz'),reserved_outcomes_read=False,
            forecast_origin_us=67_000_000,fit_stop_us=47_000_000,interval_target_stop_us=64_000_000))
    save(output/'manifest.json',dict(status='complete',wall_s=time.perf_counter()-began,source_sha256=digest(Path(__file__)),
        model_source_sha256=digest(Path('src/neuromancer/necessity.py')),artifact_sha256={str(p.relative_to(output)):digest(p) for p in sorted(output.rglob('*')) if p.is_file()}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('output');a=p.parse_args();main(a.raw,a.output)
