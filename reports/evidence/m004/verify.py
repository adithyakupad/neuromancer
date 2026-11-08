"""Independent normal-equation/forecast/CUSUM verification; no study estimators."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import numpy as np

spec=importlib.util.spec_from_file_location('previous_observation_audit',Path(__file__).parents[1]/'m003_2/verify.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
read=previous.read
NAMES=('FROZEN','SW250','SW500','RLS995','RLS999','SHUFFLED','ARX')


def xmatrix(u,k,q=10):
    return np.column_stack([u[k-j] for j in range(q)])


def normalize(record,x):return np.column_stack([np.ones(len(x)),(x-np.array(record['mean']))/np.array(record['scale'])])


def independent_fit(y,u,stop=1950,arx=False,shuffle=False):
    k=np.arange(790,stop);x=xmatrix(u,k,4 if arx else 10)
    if arx:x=np.column_stack([*[y[k-j] for j in range(1,5)],x])
    if shuffle:x=np.roll(x,250,axis=0)
    mu=x.mean(axis=0);scale=np.maximum(x.std(axis=0),1);ym=y[k].mean(axis=0);z=np.c_[np.ones(len(x)),(x-mu)/scale];v=y[k]-ym
    theta=fit_rows(z,v);penalty=np.eye(len(theta))*len(z)*.1;penalty[0,0]=0;a=z.T@z+penalty;h=z.T@v
    return dict(coef=theta,mean=mu,scale=scale,output_mean=ym),z,v,a,h


def fit_rows(z,v):
    penalty=np.eye(z.shape[1])*np.sqrt(len(z)*.1);penalty[0,0]=0
    return np.linalg.lstsq(np.vstack([z,penalty]),np.vstack([v,np.zeros((z.shape[1],4))]),rcond=None)[0]


def check_record(record,reference):
    for key in ('coef','mean','scale','output_mean'):np.testing.assert_allclose(record[key],reference[key],rtol=1e-8,atol=1e-9)


def arx_predict(record,y,u,plan):
    past=list(y[-4:]);current=list(u[-3:]);answer=[]
    for action in plan:
        x=np.r_[np.concatenate(past[-4:][::-1]),action,np.concatenate(current[-3:][::-1])]
        value=record['output_mean']+np.r_[1.,(x-record['mean'])/record['scale']]@record['coef']
        answer.append(value);past.append(value);current.append(action)
    return np.array(answer)


def cusum(residual,amplitude,sigma,nu,h):
    s=0.;last=-10;rows=[]
    for j,e in enumerate(residual):
        t=40+j;armed=amplitude[j]>=30
        if armed:s=max(0.,s+e/sigma-nu)
        statistic=s;alarm=armed and s>=h and t-last>=5
        if alarm:last=t;s=0.
        rows.append([statistic,armed,alarm])
    return np.array(rows)


def verify_trial(folder,replay):
    report=json.loads((folder/'trial.json').read_text());n=report['network_id'];rep=report['replicate_id'];condition=report['condition'];assert report['status']=='complete'
    d=read(folder/'public.npz');previous.check_observations(d);y=d['rates'];u=d['delivered'];assert len(y)==3950 and not u[:750].any()
    np.testing.assert_array_equal(u,read(folder/'plans.npz')['planned']);slew=np.diff(np.vstack([np.zeros(4),u]),axis=0)
    assert (u>=0).all() and (u<=120).all() and (u.sum(axis=1)<=240).all() and (abs(slew)<=30).all()
    oldpath=Path(f'reports/evidence/m003_1/results/raw/n{n}_r22/trial.json') if n<10 else Path(f'reports/evidence/m003/results/V/raw/n{n}_r18/trial.json')
    old=json.loads(oldpath.read_text());assert report['engine']['metadata']['parameter_hashes']==old['engine']['metadata']['parameter_hashes']
    gain=read(folder/'evaluator.npz')['gain'];expected=np.ones(3950)
    if condition in ('LOSS','WEAK'):expected[2950:]=.6
    elif condition=='UP':expected[2950:]=1.4
    elif condition=='NULL':expected[:]=0
    np.testing.assert_array_equal(gain,expected)
    for origin in (54,64,74):
        k=origin*50;plans=read(folder/f'probe{origin}_plans.npz');prev=u[k-1]
        np.testing.assert_array_equal(plans['previous'],prev);np.testing.assert_array_equal(plans['planned'][0],u[k:k+50])
        np.testing.assert_array_equal(plans['planned'][1],np.maximum(prev[None]-30*np.arange(1,51)[:,None],0))
        active=read(folder/f'probe{origin}_active.npz');sham=read(folder/f'probe{origin}_sham.npz')
        for branch in (active,sham):
            previous.check_observations(branch,y[k-1]);delta=np.diff(np.vstack([prev,branch['delivered']]),axis=0)
            assert (abs(delta)<=30).all() and (branch['delivered'].sum(axis=1)<=240).all()
        for field in ('counts','rates','sector','delivered'):np.testing.assert_array_equal(active[field],d[field][k:k+50])
        left,right=d['event_offset'][k],d['event_offset'][k+50]
        np.testing.assert_array_equal(active['event_time_us'],d['event_time_us'][left:right])
        np.testing.assert_array_equal(active['event_channel'],d['event_channel'][left:right])
        if condition in ('NULL','WEAK'):
            for field in ('counts','rates','sector','event_time_us','event_channel'):np.testing.assert_array_equal(active[field],sham[field])
    init=json.loads((replay/'initial.json').read_text());online=read(replay/'online.npz')
    refs={};fitcount=0
    for name,key,stop,ar,shuf in [('FROZEN','fir',1950,False,False),('SHUFFLED','shuffled',1950,False,True),('ARX','arx',1950,True,False),('PROVISIONAL','provisional',1550,False,False)]:
        ref,z,v,a,h=independent_fit(y,u,stop,ar,shuf);check_record(init[key],ref);refs[name]=(ref,z,v,a,h);fitcount+=1
    record,z,v,a,h=refs['FROZEN'];provisional=refs['PROVISIONAL'][0];cal=[]
    for k in range(1550,1950,50):cal.append((normalize(provisional,xmatrix(u,np.arange(k,k+50)))@provisional['coef']+provisional['output_mean']).mean(axis=0)-y[k:k+50].mean(axis=0))
    cal=np.array(cal);np.testing.assert_allclose(cal,online['calibration_residual'],atol=1e-10)
    np.testing.assert_allclose(online['width'],np.quantile(abs(cal),.95,axis=0,method='higher'),atol=1e-10)
    sigma=max(cal.mean(axis=1).std(),.1);coefs=online['theta'];rolling=[];amplitudes=[];residual=[];batch_checks=0;one_checks=0
    # Each RLS reference keeps discounted normal equations, never the rank-one inverse update.
    for m in range(6):
        np.testing.assert_allclose(coefs[m,0],refs['SHUFFLED' if m==5 else 'FROZEN'][0]['coef'],atol=1e-9)
    aa=[a.copy(),a.copy()];hh=[h.copy(),h.copy()]
    for b,k in enumerate(range(1950,3950,50)):
        xx=xmatrix(u,np.arange(k,k+50));zz=normalize(record,xx);forecast=[]
        for m in range(6):
            ref=refs['SHUFFLED'][0] if m==5 else record
            value=normalize(ref,xx)@coefs[m,b]+ref['output_mean'];np.testing.assert_allclose(value,online['rolling'][m,b],atol=1e-9);forecast.append(value)
            if m in (0,1,2,5):np.testing.assert_allclose(value,online['one_step'][m,b*50:(b+1)*50],atol=1e-9);one_checks+=50
        value=arx_predict(refs['ARX'][0],y[:k],u[:k],u[k:k+50]);np.testing.assert_allclose(value,online['rolling'][6,b],atol=1e-9)
        xa=np.column_stack([*[y[np.arange(k,k+50)-j] for j in range(1,5)],xmatrix(u,np.arange(k,k+50),4)])
        ones=normalize(refs['ARX'][0],xa)@refs['ARX'][0]['coef']+refs['ARX'][0]['output_mean']
        np.testing.assert_allclose(ones,online['one_step'][6,b*50:(b+1)*50],atol=1e-9);one_checks+=50
        for offset,t in enumerate(range(k,k+50)):
            row=zz[offset];target=y[t]-record['output_mean']
            for j,rho in enumerate((.995,.999)):
                if offset%10==0:
                    theta=np.linalg.solve(aa[j],hh[j]);np.testing.assert_allclose(row@theta+record['output_mean'],online['one_step'][j+3,t-1950],rtol=1e-7,atol=1e-8);one_checks+=1
                aa[j]=rho*aa[j]+np.outer(row,row);hh[j]=rho*hh[j]+np.outer(row,target)
        for j in range(2):
            np.testing.assert_allclose(np.linalg.solve(aa[j],hh[j]),coefs[j+3,b+1],rtol=1e-7,atol=1e-8);batch_checks+=1
        for m,window in ((1,250),(2,500)):
            indices=np.r_[np.arange(790,1950),np.arange(1950,k+50)][-window:]
            swz=normalize(record,xmatrix(u,indices));swv=y[indices]-record['output_mean'];theta=fit_rows(swz,swv)
            np.testing.assert_allclose(theta,coefs[m,b+1],atol=1e-8);batch_checks+=1
        np.testing.assert_array_equal(coefs[0,b+1],coefs[0,0]);np.testing.assert_array_equal(coefs[5,b+1],coefs[5,0])
        if k//50 in (54,64,74):
            j=(54,64,74).index(k//50);sham=read(folder/f'probe{k//50}_plans.npz')['planned'][1]
            sx=np.vstack([u[k-9:k],sham]);sx=xmatrix(sx,np.arange(9,59))
            for m in range(6):
                ref=refs['SHUFFLED'][0] if m==5 else record
                predicted=normalize(ref,sx)@coefs[m,b]+ref['output_mean']
                np.testing.assert_allclose(predicted,online['contrast'][m,j,1],atol=1e-9)
                np.testing.assert_array_equal(online['contrast'][m,j,0],online['rolling'][m,b])
            np.testing.assert_allclose(arx_predict(refs['ARX'][0],y[:k],u[:k],sham),online['contrast'][6,j,1],atol=1e-9)
        amplitudes.append(u[k:k+50].sum(axis=1).mean());residual.append((forecast[0].mean(axis=0)-y[k:k+50].mean(axis=0)).mean())
    for j in range(2):
        np.testing.assert_allclose(online['p'][j,0],np.linalg.inv(a),atol=1e-10)
        np.testing.assert_allclose(online['p'][j,1],np.linalg.inv(aa[j]),rtol=1e-7,atol=1e-8)
    for j,(nu,threshold) in enumerate(( (nu,h) for nu in (.25,.5) for h in (3,5,8,12))):
        np.testing.assert_allclose(cusum(residual,amplitudes,sigma,nu,threshold),online['detector'][j],atol=1e-8)
    metadata=json.loads((replay/'replay.json').read_text());assert metadata['status']=='complete'
    for name,m in metadata['models'].items():
        assert m['received']==2000 and not m['failed'] and m['skips']==0
        assert m['updates']==(0 if name in ('FROZEN','SHUFFLED') else 2000)
        assert m['refits']==(40 if name.startswith('SW') else 0)
    return dict(fits=fitcount,batch_coefficient_checks=batch_checks,one_step_vectors=one_checks,rolling_vectors=7*40*50,observation_archives=7)


def main():
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--replay',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();began=time.perf_counter();counts={};preserve=json.loads(Path('reports/evidence/m004/preservation.json').read_text())['files']
    for name,h in preserve.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h
    provenance=json.loads((args.raw/'provenance.json').read_text());assert len(provenance['jobs']) in (56,20)
    for name,h in provenance['source_hashes'].items():assert hashlib.sha256((Path('src')/name).read_bytes()).hexdigest()==h
    seal=json.loads((args.replay/'seal.json').read_text())
    for name,h in seal['artifact_sha256'].items():assert hashlib.sha256((args.replay/name).read_bytes()).hexdigest()==h
    expected={f'n{n}_r{r}_{c}' for n,r,c in provenance['jobs']};assert {d.name for d in args.raw.glob('n*_r*')}==expected
    for folder in sorted(args.raw.glob('n*_r*')):
        result=verify_trial(folder,args.replay/folder.name)
        for k,v in result.items():counts[k]=counts.get(k,0)+v
        print(folder.name,flush=True)
    pairs=0
    for n,r,c in provenance['jobs']:
        if c not in ('LOSS','UP'):continue
        base=args.raw/f'n{n}_r{r}_STATIC'
        if not base.exists():continue
        a=read(base/'public.npz');b=read(args.raw/f'n{n}_r{r}_{c}'/'public.npz')
        for field in ('counts','rates','sector'):np.testing.assert_array_equal(a[field][:2950],b[field][:2950])
        ma=json.loads((base/'trial.json').read_text());mb=json.loads((args.raw/f'n{n}_r{r}_{c}'/'trial.json').read_text())
        assert ma['engine']['noise_hashes']==mb['engine']['noise_hashes']
        oa=read(args.replay/f'n{n}_r{r}_STATIC'/'online.npz');ob=read(args.replay/f'n{n}_r{r}_{c}'/'online.npz')
        np.testing.assert_array_equal(oa['theta'][:,:21],ob['theta'][:,:21])
        np.testing.assert_array_equal(oa['rolling'][:,:21],ob['rolling'][:,:21])
        np.testing.assert_array_equal(oa['one_step'][:,:1001],ob['one_step'][:,:1001])
        np.testing.assert_array_equal(oa['detector'][:,:20],ob['detector'][:,:20]);pairs+=1
    result=dict(execution='PASS',trials=len(expected),matched_future_change_prefix_pairs=pairs,historical_files_unchanged=len(preserve),
        checks=counts,wall_s=time.perf_counter()-began,limitation='Separate equations in this session, not external/biological replication')
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
