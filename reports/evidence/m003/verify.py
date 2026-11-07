"""Independent M003 algebra/count/timing/lineage audit; no predictor helper calls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np
from neuromancer._brian import realization
from neuromancer.substrate import Config


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_form(record):
    coef=np.array(record['coef']);mean=np.array(record['mean']);scale=np.array(record['scale'])
    weight=coef[1:]/scale[:,None] if len(scale) else np.empty((0,4))
    intercept=np.array(record['output_mean'])+coef[0]-(mean@weight if len(mean) else 0)
    return intercept,weight


def predict(record,y,u,plan):
    intercept,w=raw_form(record);p=record['p'];inputs=record['family'] in ('ARX','SHUFFLED')
    history=[row.copy() for row in y[-max(4,p):]];past=[row.copy() for row in u[-3:]];values=[]
    for action in plan:
        value=intercept.copy()
        for lag in range(p):value+=history[-lag-1]@w[4*lag:4*lag+4]
        if inputs:
            values_u=[action,*past[-1:-4:-1]]
            for lag,current in enumerate(values_u):value+=current@w[4*p+4*lag:4*p+4*lag+4]
        values.append(value);history.append(value);past.append(action)
    return np.array(values)


def coefficient_check(record,y,u):
    p=record['p'];family=record['family'];target=y[753:2350];mean_y=target.mean(axis=0)
    np.testing.assert_allclose(mean_y,record['output_mean'],rtol=0,atol=1e-12)
    if family=='CONSTANT':return
    changed=u.copy()
    if family=='SHUFFLED':changed[753:2350]=np.roll(changed[753:2350],500,axis=0)
    k=np.arange(753,2350);blocks=[y[k-lag] for lag in range(1,p+1)]
    if family in ('ARX','SHUFFLED'):blocks += [changed[k-lag] for lag in range(4)]
    x=np.hstack(blocks);mean=x.mean(axis=0);scale=np.maximum(x.std(axis=0),1.)
    np.testing.assert_allclose(mean,record['mean'],atol=1e-12,rtol=0);np.testing.assert_allclose(scale,record['scale'],atol=1e-12,rtol=0)
    z=np.column_stack([np.ones(len(x)),(x-mean)/scale]);lam=record['diagnostics']['lambda_value']
    penalty=np.diag(np.r_[0.,np.full(z.shape[1]-1,lam)])
    beta=np.linalg.solve(z.T@z/len(x)+penalty,z.T@(target-mean_y)/len(x))
    np.testing.assert_allclose(beta,record['coef'],rtol=1e-6,atol=1e-7)
    rank=int(np.linalg.matrix_rank(z));diag=record['diagnostics']
    assert rank==diag['rank']
    singular=np.linalg.svd(z,compute_uv=False);condition=float(singular[0]/singular[-1])
    assert abs(condition-diag['condition'])<=1e-6*max(1,condition)
    _,raw_weight=raw_form(record);companion=np.zeros((4*p,4*p))
    companion[:4]=np.hstack([raw_weight[4*l:4*l+4].T for l in range(p)])
    if p>1:companion[4:,:-4]=np.eye(4*(p-1))
    radius=float(np.abs(np.linalg.eigvals(companion)).max());assert abs(radius-diag['spectral_radius'])<1e-10
    eigenvalues=np.linalg.eigvalsh(z.T@z/len(x)+penalty);penalized=float(np.sqrt(eigenvalues[-1]/eigenvalues[0]))
    assert abs(penalized-diag['penalized_condition'])<=1e-6*max(1,penalized)
    assert diag['valid']==bool(rank==z.shape[1] and condition<=1e6 and penalized<=1e8 and radius<.999)



def filter_counts(counts,initial=None):
    sector=counts.reshape(len(counts),4,5)[:,:,:4].sum(axis=2)/.4
    result=np.full((len(counts),4),np.nan);alpha=math.exp(-.02/.1)
    if initial is None:
        state=counts[350:750].reshape(400,4,5)[:,:,:4].sum(axis=(0,2))/160
        result[749]=state;start=750
    else:state=initial.copy();start=0
    for k in range(start,len(counts)):
        state=alpha*state+(1-alpha)*sector[k];result[k]=state
    return result


def main(raw,models,analysis):
    began=time.perf_counter_ns();raw=Path(raw);models=Path(models);analysis=Path(analysis)
    summary=json.loads((raw/'summary.json').read_text());source=json.loads((raw/'provenance.json').read_text())
    assert summary['status']=='complete'
    for name,h in summary['artifact_sha256'].items():assert digest(raw/name)==h,name
    for name,h in source['source_hashes'].items():assert digest(Path('src')/name)==h,name
    for name,h in source['preregistration_files_sha256'].items():assert digest(Path(name))==h,name
    preserved=json.loads(Path('reports/evidence/m003/preservation.json').read_text())
    for name,h in preserved['sha256'].items():assert digest(Path(name))==h,name
    frozen=json.loads((models/'manifest.json').read_text())
    for name,h in frozen['artifact_sha256'].items():assert digest(models/name)==h,name
    assert frozen['source_sha256']==digest(Path('reports/evidence/m003/fit_models.py'))
    assert frozen['predictor_sha256']==digest(Path('src/neuromancer/identify.py'))
    line=json.loads((analysis/'analysis_lineage.json').read_text());assert line['source_sha256']==digest(Path('reports/evidence/m003/analyze.py'))
    assert line['model_manifest_sha256']==digest(models/'manifest.json')
    if source['stage']!='D':
        qualification_path=Path(source['cli'][source['cli'].index('--qualification')+1])
        assert digest(qualification_path)==source['qualification_sha256']
        assert json.loads(qualification_path.read_text())['scientific_gate']=='PASS'
    previous=json.loads(Path('reports/evidence/m002_3/results/trial_provenance.json').read_text())
    result=json.loads((analysis/'comparison.json').read_text());trials=json.loads((analysis/'trial_metrics.json').read_text())
    with np.load(analysis/'identification_data.npz',allow_pickle=False) as archive:data={k:archive[k] for k in archive.files}
    selection=json.loads((models/'selection.json').read_text());assert len({v['p'] for v in selection['families'].values()})==1
    noise=set();states=set();coefficients=0;forecasts=0;independent_mse=[];candidate_scores={f:{} for f in ('AR','ARX','SHUFFLED')}
    for index,(n,rep) in enumerate(data['identities']):
        n=int(n);rep=int(rep);folder=raw/f'n{n}_r{rep}';mf=models/folder.name;trial=json.loads((folder/'trial.json').read_text())
        assert [n,rep,trial['gain']] in source['jobs']
        parameters=realization(Config(network_id=n));assert not np.intersect1d(parameters['stimulation'],parameters['recording']).size
        for field in ('recording','stimulation'):np.testing.assert_array_equal(data[field][index],parameters[field])
        if n<10:
            prior=next(t for t in previous if t['network_id']==n)
            assert trial['engine']['metadata']['parameter_hashes']==prior['engine']['metadata']['parameter_hashes']
        if source['stage']=='G':
            stationary=Path(source['cli'][source['cli'].index('--stationary')+1])
            original_trial=json.loads((stationary/folder.name/'trial.json').read_text())
            assert trial['engine']['noise_hashes']==original_trial['engine']['noise_hashes']
            assert trial['checkpoint_hashes']==original_trial['checkpoint_hashes']
            with np.load(stationary/folder.name/'confirmation.npz',allow_pickle=False) as old:
                for key in ('counts','rates','neurons'):np.testing.assert_array_equal(old[key][0],data[key][index,0])

        noise.add(json.dumps(trial['engine']['noise_hashes'],sort_keys=True));states.add(trial['checkpoint_hashes']['eta'])
        assert set(trial['engine']['noise_hashes'])==set(map(str,range(69)))
        config=trial['engine']['config'];assert config['root_seed']==20261018 and config['dt_us']==100
        for filename,mapping in [('prefix',{'counts':'prefix_counts','rates':'prefix_rates','delivered':'prefix_delivered','desired':'prefix_desired'}),
                                 ('plans',{'planned':'planned','desired':'desired'}),
                                 ('confirmation',{'counts':'counts','rates':'rates','delivered':'delivered','neurons':'neurons'})]:
            with np.load(folder/f'{filename}.npz',allow_pickle=False) as archive:
                for key,target in mapping.items():np.testing.assert_array_equal(archive[key],data[target][index])
        for rows in [data['prefix_delivered'][index],*data['delivered'][index]]:
            assert rows.min()>=0 and rows.max()<=120 and np.max(rows.sum(axis=1))<=240
            assert np.abs(np.diff(np.vstack([np.zeros(4),rows]),axis=0)).max()<=30
        np.testing.assert_array_equal(data['planned'][index],data['delivered'][index])
        y=data['prefix_rates'][index];u=data['prefix_delivered'][index]
        np.testing.assert_allclose(filter_counts(data['prefix_counts'][index]),y,rtol=0,atol=1e-12,equal_nan=True)
        for a in range(6):
            np.testing.assert_allclose(filter_counts(data['counts'][index,a],y[-1]),data['rates'][index,a],rtol=0,atol=1e-12)
            for c,ids in enumerate(parameters['recording']):assert data['counts'][index,a,:,c].sum()==data['neurons'][index,a,ids].sum()
            assert abs(data['delivered'][index,a].sum()*.02-trial['receipts'][a]['exposure_pA_s'])<1e-10
        if rep==21:
            for a in range(6):
                for key in ('counts','rates','neurons'):np.testing.assert_array_equal(data[key][index,a],data[key][index,0])
        k=np.arange(753,2350);input_lags=np.hstack([u[k-lag] for lag in range(4)])
        zz=(input_lags-input_lags.mean(axis=0))/np.maximum(input_lags.std(axis=0),1)
        assert np.linalg.matrix_rank(zz)==16 and np.linalg.cond(zz)<=1e6
        selected=json.loads((mf/'selected.json').read_text());own=np.empty((4,6,100,4));own_mse=np.empty(4)
        actual=data['rates'][index]
        for mi,family in enumerate(('CONSTANT','AR','ARX','SHUFFLED')):
            record=selected[family];assert record['diagnostics']['valid']
            coefficient_check(record,y,u);coefficients+=1
            for a in range(6):
                own[mi,a]=predict(record,y,u,data['planned'][index,a]);forecasts+=1
                np.testing.assert_allclose(own[mi,a],data['forecast'][index,mi,a],rtol=0,atol=1e-8)
                for t in range(100):
                    history=np.vstack([y[-4:],actual[a,:t]]);past=np.vstack([u[-4:],data['delivered'][index,a,:t]])
                    expected=predict(record,history,past,data['planned'][index,a,t:t+1])[0]
                    np.testing.assert_allclose(expected,data['ordinary'][index,mi,a,t],rtol=0,atol=1e-9)
            widths=[];residuals50=None
            for h in (1,10,50):
                errors=np.array([predict(record,y[:j],u[:j],data['prefix_delivered'][index,j:j+h]).mean(axis=0)-y[j:j+h].mean(axis=0) for j in range(2750,3101,10)])
                widths.append(np.quantile(np.abs(errors),.95,axis=0,method='higher'))
                if h==50:residuals50=-errors.mean(axis=1)
            np.testing.assert_allclose(widths,data['interval_halfwidth'][index,mi],rtol=0,atol=1e-8)
            assert abs(np.quantile(residuals50,.05,method='lower')-data['residual_threshold'][index,mi])<1e-8
            predicted=(own[mi,1:,:50]-own[mi,0,:50]).mean(axis=1)
            truth=(actual[1:,:50]-actual[0,:50]).mean(axis=1)
            own_mse[mi]=np.mean((predicted-truth)**2)
        np.testing.assert_allclose(own_mse,np.array(trials[index]['evoked_mse'])[:,2],rtol=0,atol=1e-8)
        if rep!=21:independent_mse.append((n,own_mse))
        candidate_file=mf/'candidates.json'
        if candidate_file.exists():
            candidates=json.loads(candidate_file.read_text())
            for family,records in candidates.items():
                for key,record in records.items():
                    coefficient_check(record,y,u);coefficients+=1
                    val=record['validation_mse']
                    if val is not None:
                        errors=np.array([predict(record,y[:j],u[:j],data['prefix_delivered'][index,j:j+50]).mean(axis=0)-y[j:j+50].mean(axis=0) for j in range(2350,2701,10)])
                        assert abs(np.mean(errors**2)-val)<1e-8
                    candidate_scores[family].setdefault(key,[]).append(val)
    nids=sorted({n for n,v in independent_mse});mse=np.array([np.mean([v for nn,v in independent_mse if nn==n],axis=0) for n in nids])
    np.testing.assert_allclose(mse,np.array([row['evoked_mse'] for row in result['networks']])[:,:,2],rtol=0,atol=1e-8)
    rng=np.random.default_rng(20261030);draws=rng.integers(0,len(nids),(10000,len(nids)));passes=[];points=[]
    for name,col in (('AR',1),('SHUFFLED',3)):
        difference=mse[:,col]-mse[:,2];relative=difference/np.maximum(mse[:,col],.04)
        lower=float(np.quantile(difference[draws].mean(axis=1),.025));entry=result['comparisons'][name]
        assert abs(difference.mean()-entry['absolute']['mean'])<1e-8 and abs(lower-entry['absolute']['lower'])<1e-8
        point=bool(difference.mean()>=.04 and relative.mean()>=.10 and (difference>0).sum()>=(8 if len(nids)==10 else 4))
        points.append(point);passes.append(point and lower>0)
    decision='PASS' if all(passes) else 'HOLD' if all(points) else 'FAIL';assert decision==result['scientific_gate']
    if source['stage']=='D':
        valid={}
        for family,records in candidate_scores.items():
            valid[family]=[]
            for key,values in records.items():
                assert len(values)==30
                if all(v is not None for v in values):
                    p=int(key.split('_')[0][1:]);lam=float(key.split('lambda')[1]);valid[family].append((np.mean(values),p,lam))
        def best(rows):
            score=min(v[0] for v in rows);return min((r for r in rows if r[0]<=score+1e-12),key=lambda r:(r[1],-r[2]))
        chosen=best(valid['AR']);assert selection['families']['AR']=={'p':chosen[1],'lambda':chosen[2]}
        for family in ('ARX','SHUFFLED'):
            chosen_other=best([v for v in valid[family] if v[1]==chosen[1]])
            assert selection['families'][family]=={'p':chosen_other[1],'lambda':chosen_other[2]}
    assert len(noise)==len(trials)==len(states)
    verification=dict(status='PASS',trials=len(trials),branches=6*len(trials),coefficient_checks=coefficients,
        independent_forecasts=forecasts,distinct_noise_ledgers=len(noise),historical_files_preserved=len(preserved['sha256']),
        independently_recomputed_scientific_gate=decision,wall_s=(time.perf_counter_ns()-began)/1e9,
        source_sha256=digest(Path(__file__)),limitations='Independent equations/count recomputation in this session, not external human or independent neural simulator replication.')
    save=lambda path,value:path.write_text(json.dumps(value,indent=2)+'\n')
    save(analysis/'verification.json',verification);print(json.dumps(verification,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('models');p.add_argument('analysis');a=p.parse_args();main(a.raw,a.models,a.analysis)
