"""Independent count, causal PI, exposure, split and numerical gate auditor.

Does not call control.Policy/calibrate/project or scientific analysis functions.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import time
import numpy as np


def close(a,b): np.testing.assert_allclose(a,b,rtol=1e-12,atol=2e-12,equal_nan=True)


def inspect_public(path,start,bins,filter_initial=None):
    d=dict(np.load(path)); times=start+20000*np.arange(bins)
    np.testing.assert_array_equal(d['time_us'],np.column_stack([times,times+20000,times+20000]))
    assert d['valid'].all() and (d['coverage_us']==20000).all()
    off=d['event_offset']; counts=np.empty((bins,20),int)
    for k in range(bins):
        t=d['event_time_us'][off[k]:off[k+1]];ch=d['event_channel'][off[k]:off[k+1]]
        assert ((t>=times[k])&(t<times[k]+20000)&(t%100==0)).all()
        assert ((ch>=0)&(ch<20)).all()
        counts[k]=np.bincount(ch,minlength=20)
    np.testing.assert_array_equal(counts,d['counts'])
    sector=counts.reshape(bins,4,5)[:,:,:4].sum(axis=2)/.4
    close(d['sector'],sector)
    filtered=np.full((bins,4),np.nan); value=filter_initial
    for k in range(bins):
        if start==0 and k==749:
            value=sector[350:750].mean(axis=0)
        elif value is not None:
            value=np.exp(-.2)*value+(1-np.exp(-.2))*sector[k]
        if value is not None:filtered[k]=value
    close(filtered,d['rates'])
    u=d['delivered']; np.testing.assert_array_equal(d['requested'],u)
    assert np.isfinite(u).all() and (u>=0).all() and (u<=120).all() and (u.sum(axis=1)<=240).all()
    assert (abs(np.diff(np.vstack([np.zeros(4),u]),axis=0))<=30).all()
    return d,sector.mean(axis=1)


def calibration(prefix,raw,c):
    h=[0.]+[float(raw[1000+400*j:1150+400*j].mean()-raw[800+400*j:950+400*j].mean()) for j in range(4)]
    b=raw[350:750].mean();noise=raw[350:750].reshape(8,50).mean(axis=1).std(ddof=1)
    q=np.array([0.,30.,60.,90.,120.]); a=np.dot(q,h)/np.dot(q,q);ff=1/a if a>0 else 0
    valid=bool(np.isfinite(h).all() and 1<=b<=30 and a>0 and max(abs(q*a-h))<=.5 and min(np.diff(h))>=-.3 and 0<=ff<=120)
    close([b,noise,a,ff,b+1],[c[k] for k in ('baseline_hz','noise_hz','slope_hz_per_pA','feedforward_pA','target_hz')]);close(h,c['h_hz']);assert c['valid']==valid
    desired=np.zeros((2550,4))
    for j,level in enumerate((30,60,90,120)):desired[950+400*j:1150+400*j,[0,2]]=level
    prior=np.zeros(4)
    for k in range(2550):
        prior=np.minimum(np.maximum(desired[k],prior-30),prior+30)
        close(prior,prefix['delivered'][k])


def policy_replay(data,raw,c,name):
    kp,ki=(tuple(map(float,name[2:].split('_'))) if name.startswith('PI') else (0.,0.))
    q=0. if name=='ZERO' else 120. if name=='MAX' else c['feedforward_pA'];integral=0.;error=np.nan;blocked=False;saturated=False
    safe=not c['valid'] and name not in ('ZERO','MAX');previous=np.zeros(4)
    for second in range(32):
        dec=[51000000+1000000*second,q,integral,error,float(blocked),float(saturated),float(safe),second if not safe else 0]
        close(dec,data['decisions'][second])
        intent=np.array([0.,0.,0.,0.]) if safe else np.array([q,0.,q,0.])
        for k in range(second*50,(second+1)*50):
            close(data['intent'][k],intent)
            # All scientific requests are C02: box-clipping is also the exact
            # full budget projection because the other two channels stayzero.
            previous=np.clip(intent,np.maximum(0,previous-30),np.minimum(120,previous+30))
            close(previous,data['delivered'][k])
        if safe:continue
        error=c['target_hz']-raw[second*50:(second+1)*50].mean();blocked=False;saturated=False
        if name.startswith('PI'):
            new=float(np.clip(integral+ki*error,-120,120));candidate=c['feedforward_pA']+kp*error+new
            blocked=bool((candidate>120 and error>0) or (candidate<0 and error<0))
            if not blocked:integral=new
            candidate=c['feedforward_pA']+kp*error+integral;q=float(np.clip(candidate,0,120));saturated=candidate!=q
    close([83000000,q,integral,error,float(blocked),float(saturated),float(safe),32 if not safe else 0],data['terminal'])


def score(raw,target,a,b):
    e=raw.reshape(32,50).mean(axis=1)[a:b]-target
    return float(abs(e).mean()),float(e.mean()),float(np.sqrt((e*e).mean())),float(raw.reshape(32,50).mean(axis=1)[a:b].mean())


def audit(raw_root,analysis):
    started=time.perf_counter();meta=json.loads((raw_root/'provenance.json').read_text());trials=[];all_scores={};branches=0
    for folder in sorted(raw_root.glob('n*_r*')):
        m=json.loads((folder/'trial.json').read_text());assert m['status']=='complete';n,r=m['network_id'],m['replicate_id']
        assert 0<=n<10 and r in meta['replicates']
        assert m['engine']['config']['dt_us']==100
        from neuromancer._brian import realization,digest,innovations
        from neuromancer.substrate import Config
        cfg=Config(network_id=n,replicate_id=r)
        params=realization(cfg);assert {k:digest(v) for k,v in params.items()}==m['engine']['metadata']['parameter_hashes']
        assert len(np.intersect1d(params['recording'],params['stimulation']))==0
        prefix,baseline=inspect_public(folder/'prefix.npz',0,2550);c=m['calibration'];calibration(prefix,baseline,c)
        cached={};noise=None
        for branch in m['branches']:
            condition,name=branch['condition'],branch['controller'];d,raw=inspect_public(folder/f'{condition}_{name}.npz',51000000,1600,prefix['rates'][-1])
            policy_replay(d,raw,c,name);branches+=1;cached[condition,name]=d
            assert len(branch['noise'])==83
            if noise is None:
                noise=branch['noise']
                # Recompute representative absolute-time OUblocks includingthe
                # change boundary; all83hashesmatch betweenbranches.
                for block in (0,50,51,66,67,82):
                    effective,fine=innovations(cfg,block)
                    assert noise[str(block)]==dict(fine=fine,effective=digest(effective))
            else:assert branch['noise']==noise
            exposure=float(d['delivered'].sum()*.02);close(exposure,branch['audit']['exposure_pA_s']);assert branch['audit']['violations']==0
            for window,(a,b) in {'full':(0,32),'stationary':(8,32),'pre':(8,16),'immediate':(16,20),'late':(20,32)}.items():
                all_scores[n,r,condition,name,window]=(*score(raw,c['target_hz'],a,b),c,exposure)
        for name in meta['names']:
            a,b=cached['STATIC',name],cached['LOSS',name]
            for field in ('counts','rates','sector','delivered','decisions','intent'):
                close(a[field][:(17 if field=='decisions' else 800)],b[field][:(17 if field=='decisions' else 800)])
        for field in ('counts','rates','sector','delivered','intent'):
            close(cached['STATIC','ZERO'][field],cached['LOSS','ZERO'][field])
        trials.append((n,r))
    assert len(trials)==10*len(meta['replicates']) and len(set(trials))==len(trials)
    rows=list(csv.DictReader((analysis/'metrics.csv').open()));assert len(rows)==len(all_scores)
    for row in rows:
        key=(int(row['network']),int(row['replicate']),row['condition'],row['controller'],row['window']);values=all_scores[key]
        close(values[:4],[float(row[k]) for k in ('mae_hz','bias_hz','rmse_hz','rate_hz')]);close(values[-1],float(row['online_exposure_pA_s']))
    # Separately recompute all per-network scientificcomponents.
    summary=json.loads((analysis/'summary.json').read_text());selected=summary['selected']
    gates=list(csv.DictReader((analysis/'network_qualification.csv').open()))
    def mean(n,condition,name,window,index):
        return float(np.mean([all_scores[n,r,condition,name,window][index] for r in meta['replicates']]))
    gate_pass={};benefits={}
    for condition,window in [('STATIC','stationary'),('LOSS','late')]:
        good=0;benefit=[]
        for n in range(10):
            c=[all_scores[n,r,condition,'ZERO','late'][4] for r in meta['replicates']]
            valid=all(v['valid'] and 1<=v['baseline_hz']<=30 for v in c)
            noise=np.sqrt(np.mean([v['noise_hz']**2 for v in c]));authority=mean(n,condition,'MAX','late',3)-mean(n,condition,'ZERO','late',3)
            mae=mean(n,condition,selected,window,0);bias=mean(n,condition,selected,window,1);zero=mean(n,condition,'ZERO',window,0)
            comp=dict(calibration_baseline_valid=valid,noise_valid=1>=2*noise,authority=authority>=1.2,error=mae<=.35,bias=abs(bias)<=.2,zero_benefit=(zero-mae)/max(zero,.1)>=.3)
            row=next(r for r in gates if int(r['network'])==n and r['condition']==condition)
            for k,v in comp.items():assert (row[k]=='True')==v
            assert (row['qualified']=='True')==all(comp.values());good+=all(comp.values());benefit.append(zero-mae)
        gate_pass[condition]=good>=8 and bootstrap(benefit)[0]>0
        assert summary['regimes'][condition]['qualified']==good
        close(summary['regimes'][condition]['zero_benefit_ci_hz'],bootstrap(benefit))
        assert summary['regimes'][condition]['pass_gate']==gate_pass[condition]
    benefit=np.array([mean(n,'LOSS','FIXED','late',0)-mean(n,'LOSS',selected,'late',0) for n in range(10)])
    relative=benefit/np.maximum([mean(n,'LOSS','FIXED','late',0) for n in range(10)],.1)
    required=bool(benefit.mean()>=.1 and relative.mean()>=.2 and bootstrap(benefit)[0]>0 and (benefit>0).sum()>=8)
    assert summary['recovery_advantage']['pass_gate']==required
    close(summary['recovery_advantage']['ci_hz'],bootstrap(benefit))
    assert summary['stationary_pass']==gate_pass['STATIC'] and summary['recovery_pass']==(gate_pass['LOSS'] and required)
    assert summary['scientific_pass']==(gate_pass['STATIC'] and gate_pass['LOSS'] and required)
    if meta['stage']=='TUNE':
        selected_record=json.loads((analysis/'selection.json').read_text());scores={}
        for name in ('PI10_5','PI20_10','PI30_15'):
            scores[name]=np.mean([.5*(mean(n,'STATIC',name,'stationary',0)+mean(n,'LOSS',name,'late',0)) for n in range(10)])
            close(scores[name],selected_record['candidates'][name]['mean_score'])
        assert min(scores,key=lambda k:(round(scores[k],12),int(k[2:].split('_')[0])))==selected
    return dict(status='PASS',stage=meta['stage'],trials=len(trials),branches=branches,metric_rows=len(rows),
                verified='event counts/filter/calibration/causal PI/actions/cost/matched prefixes/OU samples/parameters/allnetworkgates/selection',wall_s=time.perf_counter()-started)


def bootstrap(x):
    values=np.array(x);g=np.random.Generator(np.random.PCG64(20261025));indices=g.integers(0,len(values),(10000,len(values)))
    return np.quantile(values[indices].mean(axis=1),[.025,.975])


def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('analysis',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=audit(a.raw,a.analysis)
    historical=json.loads(Path('reports/evidence/m005a/preservation.json').read_text())
    for path,digest in historical['historical_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    result['historical_files_unchanged']=len(historical['historical_sha256'])
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':main()
