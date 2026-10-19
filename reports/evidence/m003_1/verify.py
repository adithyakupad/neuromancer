"""Independent equations and lineage audit; does not import M003.1 predictors."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import numpy as np

FAMILIES=('STATIC','FIR','ARX','AR','STATIC_SHUFFLED','FIR_SHUFFLED','ARX_SHUFFLED')


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def raw_form(m):
    w=np.array(m['coef'])[1:]/np.array(m['scale'])[:,None]
    return np.array(m['output_mean'])+np.array(m['coef'])[0]-np.array(m['mean'])@w,w


def predict(m,y,u,plan):
    intercept,w=raw_form(m);p=m['p'];q=m['q'];out=np.tile(intercept,(len(plan),1))
    if not p:
        full=np.vstack([u[-(q-1):] if q>1 else np.empty((0,4)),plan]);start=len(full)-len(plan)
        kernel=w.reshape(q,4,4)
        for c in range(4):
            for s in range(4):out[:,s]+=np.convolve(full[:,c],kernel[:,c,s],mode='full')[start:start+len(plan)]
        return out
    history=list(y[-p:].copy());past=list(u[-max(q-1,1):].copy())
    for k,a in enumerate(plan):
        for l in range(p):out[k]+=history[-l-1]@w[4*l:4*l+4]
        for l in range(q):out[k]+=(a if l==0 else past[-l])@w[4*p+4*l:4*p+4*l+4]
        history.append(out[k]);past.append(a)
    return out


def coefficient(m,y,u,cache):
    key=(m['family'],m['size'])
    if key not in cache:
        shifted=u.copy()
        if m['family'].endswith('_SHUFFLED'):shifted[800:2350]=np.roll(shifted[800:2350],500,axis=0)
        k=np.arange(800,2350);blocks=[y[k-l] for l in range(1,m['p']+1)]+[shifted[k-l] for l in range(m['q'])]
        x=np.column_stack(blocks);mu=x.mean(axis=0);scale=np.maximum(x.std(axis=0),1);ym=y[800:2350].mean(axis=0)
        z=np.column_stack([np.ones(1550),(x-mu)/scale]);s=np.linalg.svd(z,compute_uv=False)
        cache[key]=(mu,scale,ym,z.T@z/1550,z.T@(y[800:2350]-ym)/1550,s)
    mu,scale,ym,gram,rhs,s=cache[key];d=m['diagnostics'];lam=d['lambda_value']
    np.testing.assert_allclose(mu,m['mean'],atol=1e-12,rtol=0);np.testing.assert_allclose(scale,m['scale'],atol=1e-12,rtol=0);np.testing.assert_allclose(ym,m['output_mean'],atol=1e-12,rtol=0)
    penalized=gram+np.diag(np.r_[0.,np.full(len(mu),lam)]);beta=np.linalg.solve(penalized,rhs)
    np.testing.assert_allclose(beta,m['coef'],atol=1e-7,rtol=1e-6)
    rank=int((s>1550*np.finfo(float).eps*s[0]).sum())
    assert d['rank']==rank and abs(d['condition']-s[0]/s[-1])<1e-5
    eigen=np.linalg.eigvalsh(penalized);assert abs(d['penalized_condition']-np.sqrt(eigen[-1]/eigen[0]))<1e-5
    radius=0.
    if m['p']:
        _,w=raw_form(m);p=m['p'];companion=np.zeros((4*p,4*p));companion[:4]=w[:4*p].T
        if p>1:companion[4:,:-4]=np.eye(4*(p-1))
        radius=float(np.abs(np.linalg.eigvals(companion)).max())
    assert abs(radius-d['spectral_radius'])<1e-10
    assert d['valid']==bool(rank==len(mu)+1 and s[0]/s[-1]<=1e6 and np.sqrt(eigen[-1]/eigen[0])<=1e8 and radius<.999)
    assert d['fit_rows']==[800,2350]
    return True


def independently_select(rows):
    available=[v for v in rows if v['loss'] is not None];minimum=min(v['loss'] for v in available)
    return sorted([v for v in available if v['loss']<=minimum+1e-12],key=lambda v:(v['features'],-v['lambda']))[0]


def main(raw,models,analysis):
    began=time.perf_counter();raw=Path(raw);models=Path(models);analysis=Path(analysis)
    for name,h in json.load(open('reports/evidence/m003_1/preservation.json'))['sha256'].items():assert digest(name)==h,name
    source=json.load(open(raw/'provenance.json'));summary=json.load(open(raw/'summary.json'));assert summary['status']=='complete'
    expected={(n,r) for n in range(10) for r in (22,23,24)}|{(n,25) for n in range(3)}
    assert {(n,r) for n,r,g in source['jobs']}==expected and len(source['jobs'])==33
    assert source['preregistration_sha256']==digest('docs/research/006_M003_1_MODEL_NECESSITY_PROTOCOL.md')
    for path,h in source['source_hashes'].items():assert digest(Path('src')/path)==h
    for path,h in summary['artifact_sha256'].items():assert digest(raw/path)==h
    manifest=json.load(open(models/'manifest.json'))
    for name,h in manifest['artifact_sha256'].items():assert digest(models/name)==h
    assert manifest['source_sha256']==digest('reports/evidence/m003_1/fit_models.py') and manifest['model_source_sha256']==digest('src/neuromancer/necessity.py')
    spec=importlib.util.spec_from_file_location('old_count_audit','reports/evidence/m003/verify.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    historical=json.load(open('reports/evidence/m003/results/D/trial_provenance.json'))
    result=json.load(open(analysis/'comparison.json'));selection=json.load(open(models/'selection.json'));trials=json.load(open(analysis/'trial_metrics.json'))
    with np.load(analysis/'data.npz',allow_pickle=False) as a:data={k:a[k] for k in a.files}
    assert {tuple(v) for v in data['identities']}==expected
    noise=set();coefficients=forecasts=0;mses=[];scores={f:{} for f in FAMILIES};max_identity=0.
    for i,(n,r) in enumerate(data['identities']):
        folder=raw/f'n{n}_r{r}';modeldir=models/folder.name;trial=json.load(open(folder/'trial.json'));cache={}
        prior=next(v for v in historical if v['network_id']==n)
        assert trial['engine']['metadata']['parameter_hashes']==prior['engine']['metadata']['parameter_hashes']
        assert not np.intersect1d(data['recording'][i],data['stimulation'][i]).size
        noise.add(json.dumps(trial['engine']['noise_hashes'],sort_keys=True));assert set(trial['engine']['noise_hashes'])==set(map(str,range(69)))
        assert trial['engine']['config']['dt_us']==100
        for filename,mapping in [('prefix',{'counts':'prefix_counts','rates':'prefix_rates','delivered':'prefix_delivered','desired':'prefix_desired'}),('plans',{'planned':'planned','desired':'desired'}),('confirmation',{'counts':'counts','rates':'rates','delivered':'delivered','neurons':'neurons'})]:
            with np.load(folder/f'{filename}.npz',allow_pickle=False) as a:
                for field,key in mapping.items():np.testing.assert_array_equal(a[field],data[key][i])
        np.testing.assert_array_equal(data['planned'][i],data['delivered'][i]);y=data['prefix_rates'][i];u=data['prefix_delivered'][i]
        np.testing.assert_allclose(old.filter_counts(data['prefix_counts'][i]),y,atol=1e-12,rtol=0,equal_nan=True)
        for rows in (u,*data['delivered'][i]):
            assert rows.min()>=0 and rows.max()<=120 and rows.sum(axis=1).max()<=240 and np.abs(np.diff(np.vstack([np.zeros(4),rows]),axis=0)).max()<=30
        for a in range(6):
            np.testing.assert_allclose(old.filter_counts(data['counts'][i,a],y[-1]),data['rates'][i,a],atol=1e-12,rtol=0)
            for c,ids in enumerate(data['recording'][i]):assert data['counts'][i,a,:,c].sum()==data['neurons'][i,a,ids].sum()
            assert abs(data['delivered'][i,a].sum()*.02-trial['receipts'][a]['exposure_pA_s'])<1e-10
            if a in (1,2,3,4):assert abs(data['delivered'][i,a].sum()*.02-24)<1e-10
            if r==25:
                for key in ('counts','rates','neurons'):np.testing.assert_array_equal(data[key][i,a],data[key][i,0])
        for a,b,stop in ((1,2,1),(3,4,10)):
            np.testing.assert_array_equal(data['delivered'][i,a,:stop],data['delivered'][i,b,:stop])
            for key in ('counts','rates'):np.testing.assert_array_equal(data[key][i,a,:stop],data[key][i,b,:stop])
            np.testing.assert_allclose(data['forecast'][i,:,a,:stop],data['forecast'][i,:,b,:stop],atol=1e-12,rtol=0)
        selected=json.load(open(modeldir/'selected.json'));actual=data['rates'][i];own=np.empty((7,6,100,4))
        for mi,family in enumerate(FAMILIES):
            model=selected[family];coefficient(model,y,u,cache);coefficients+=1
            for a in range(6):
                own[mi,a]=predict(model,y,u,data['planned'][i,a]);forecasts+=1
                np.testing.assert_allclose(own[mi,a],data['forecast'][i,mi,a],atol=1e-8,rtol=0)
                for k in range(100):
                    history=np.vstack([y[-4:],actual[a,:k]]);past=np.vstack([u[-50:],data['delivered'][i,a,:k]])
                    np.testing.assert_allclose(predict(model,history,past,data['planned'][i,a,k:k+1])[0],data['ordinary'][i,mi,a,k],atol=1e-8,rtol=0)
            for hi,h in enumerate((1,10,50,100)):
                errors=np.array([predict(model,y[:k],u[:k],u[k:k+h]).mean(axis=0)-y[k:k+h].mean(axis=0) for k in range(2750,3101,10)])
                width=np.quantile(np.abs(errors),.95,axis=0,method='higher')
                np.testing.assert_allclose(width,data['width'][i,mi,hi],atol=1e-8,rtol=0)
                assert abs(np.abs(errors).mean()-trials[i]['calibration_mae'][mi][hi])<1e-8
                assert abs((np.abs(errors)<=width).mean()-trials[i]['calibration_coverage'][mi][hi])<1e-10
        effects=own-own[:,0,None];truth=actual-actual[0]
        for hi,h in enumerate((1,10,50,100)):
            pe=effects[:,:,:h].mean(axis=2);tr=truth[:,:h].mean(axis=1);err=pe-tr[None]
            np.testing.assert_allclose((err[:,1:]**2).mean(axis=(1,2)),np.array(trials[i]['evoked_mse'])[:,hi],atol=1e-8,rtol=0)
            np.testing.assert_allclose(err[:,1:].mean(axis=(1,2)),np.array(trials[i]['evoked_bias'])[:,hi],atol=1e-8,rtol=0)
            absolute=(own[:,:,:h].mean(axis=2)-actual[None,:,:h].mean(axis=2))
            np.testing.assert_allclose((absolute**2).mean(axis=(1,2)),np.array(trials[i]['absolute_mse'])[:,hi],atol=1e-8,rtol=0)
            np.testing.assert_allclose((np.abs(absolute)<=data['width'][i,:,hi,None,:]).mean(axis=(1,2)),np.array(trials[i]['coverage'])[:,hi],atol=1e-10,rtol=0)
            dynamic=np.array([np.mean(((pe[:,a]-pe[:,b])-(tr[a]-tr[b]))**2,axis=1) for a,b in ((1,2),(3,4))]).T
            np.testing.assert_allclose(dynamic,np.array(trials[i]['dynamic_contrast_mse'])[:,hi],atol=1e-8,rtol=0)
        residual=actual[None]-data['ordinary'][i]
        np.testing.assert_allclose((residual**2).mean(axis=(1,2,3)),trials[i]['ordinary_mse'],atol=1e-8,rtol=0)
        np.testing.assert_allclose(residual.mean(axis=(1,2,3)),trials[i]['residual_mean'],atol=1e-8,rtol=0)
        correlations=[]
        for mi in range(7):
            values=[]
            for a in range(6):
                for c in range(4):
                    left=residual[mi,a,:-1,c];right=residual[mi,a,1:,c];left=left-left.mean();right=right-right.mean();den=np.linalg.norm(left)*np.linalg.norm(right)
                    values.append(float(left@right/den) if den else 0.)
            correlations.append(np.mean(values))
        np.testing.assert_allclose(correlations,trials[i]['residual_lag1_acf'],atol=1e-10,rtol=0)
        own_mse=((effects[:,1:,:50].mean(axis=2)-truth[None,1:,:50].mean(axis=2))**2).mean(axis=(1,2))
        np.testing.assert_allclose(own_mse,np.array(trials[i]['evoked_mse'])[:,2],atol=1e-8,rtol=0)
        for a in range(6):
            # Zero initial neural/input *contrast*, driven only by the plan difference.
            m=selected['ARX'];_,w=raw_form(m);e=np.zeros((100,4));plan=data['planned'][i,a]-data['planned'][i,0]
            for k in range(100):
                for lag in range(1,m['p']+1):
                    if k>=lag:e[k]+=e[k-lag]@w[4*(lag-1):4*lag]
                for lag in range(m['q']):
                    if k>=lag:e[k]+=plan[k-lag]@w[4*m['p']+4*lag:4*m['p']+4*lag+4]
            difference=float(np.abs(e-effects[2,a]).max());max_identity=max(max_identity,difference);assert difference<1e-9
        if r!=25:mses.append((int(n),own_mse))
        candidate_file=modeldir/'candidates.json'
        if candidate_file.exists():
            for family,records in json.load(open(candidate_file)).items():
                for m in records:
                    coefficient(m,y,u,cache);coefficients+=1
                    if m['validation_mse'] is not None:
                        values=np.array([predict(m,y[:k],u[:k],u[k:k+50]).mean(axis=0)-y[k:k+50].mean(axis=0) for k in range(2350,2701,10)])
                        assert abs(np.mean(values**2)-m['validation_mse'])<1e-8
                    scores[family].setdefault((m['size'],m['diagnostics']['lambda_value']),[]).append(m['validation_mse'])
        if time.perf_counter()-began>900:raise TimeoutError('Independent verification cap')
    assert len(noise)==33
    for family,choices in scores.items():
        rows=[dict(size=s,**{'lambda':l},features=next(v['features'] for v in selection['scores'][family] if v['size']==s and v['lambda']==l),loss=float(np.mean(v)) if all(x is not None for x in v) else None) for (s,l),v in choices.items()]
        selected=independently_select(rows);assert all(selected[k]==selection['models'][family][k] for k in ('size','lambda','features'))
    minimum=min(selection['models'][f]['loss'] for f in ('STATIC','FIR'));competitor='STATIC' if selection['models']['STATIC']['loss']<=minimum+1e-12 else 'FIR';assert competitor==selection['primary_competitor']
    network=np.array([np.mean([v for n,v in mses if n==i],axis=0) for i in range(10)]);j=FAMILIES.index(competitor);delta=network[:,j]-network[:,2]
    index=np.random.default_rng(20261101).integers(0,10,(10000,10));ci=np.quantile(delta[index].mean(axis=1),[.025,.975]);relative=delta/np.maximum(network[:,j],.04)
    np.testing.assert_allclose([delta.mean(),*ci],[result['absolute'][k] for k in ('mean','lower','upper')],atol=1e-8,rtol=0)
    np.testing.assert_allclose(network,np.array([n['evoked_mse'] for n in result['networks']])[:,:,2],atol=1e-8,rtol=0)
    points=delta.mean()>=.04 and relative.mean()>=.10 and (delta>0).sum()>=8;decision='PASS' if points and ci[0]>0 else 'HOLD' if points else 'FAIL';assert decision==result['scientific_gate']
    record=dict(status='PASS',trials=33,branches=198,coefficient_checks=coefficients,common_forecasts=forecasts,independent_scientific_gate=decision,
        zero_state_ARX_max_difference_hz=max_identity,distinct_noise_ledgers=len(noise),historical_files_preserved=849,wall_s=time.perf_counter()-began,source_sha256=digest(__file__),
        limitations='Independent equations in the same session, not external investigator or simulator replication.')
    (analysis/'verification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('models');p.add_argument('analysis');a=p.parse_args();main(a.raw,a.models,a.analysis)
