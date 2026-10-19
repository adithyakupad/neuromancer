"""Independent numerical recomputation from saved counts, not calibration/gate calls."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from neuromancer._brian import realization
from neuromancer.observation import RateFilter
from neuromancer.substrate import Config


def main(raw,output):
    began=time.perf_counter_ns();raw=Path(raw);output=Path(output)
    summary=json.loads((raw/'summary.json').read_text());assert summary['status']=='complete' and len(summary['trials'])==50
    for name,digest in summary['artifact_sha256'].items():assert hashlib.sha256((raw/name).read_bytes()).hexdigest()==digest,name
    historical=json.loads(Path('reports/evidence/m002_3/preservation.json').read_text())
    for name,digest in historical['sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
    source=json.loads((raw/'provenance.json').read_text())
    for name,digest in source['source_hashes'].items():assert hashlib.sha256((Path('src')/name).read_bytes()).hexdigest()==digest,name
    assert source['preregistration_sha256']==hashlib.sha256(Path('reports/evidence/m002_3/PREREGISTRATION.md').read_bytes()).hexdigest()
    assert summary==json.loads((output/'raw_summary.json').read_text())
    assert source==json.loads((output/'raw_provenance.json').read_text())
    assert source['design']['network_ids']==list(range(10)) and source['design']['replicate_ids']==list(range(8,13))
    frozen=Path('reports/evidence/m002_3/analyze_frozen.py').read_text()
    repaired=Path('reports/evidence/m002_3/analyze.py').read_text()
    assert repaired==frozen.replace("entry=dict(network_id=n,replicate_id=rep,gain=gain,condition=name,", "assert ledger['gain']==gain\n                    entry=dict(network_id=n,replicate_id=rep,condition=name,")
    lineage=json.loads((output/'analysis_lineage.json').read_text())
    assert lineage['source_sha256']==hashlib.sha256(Path('reports/evidence/m002_3/analyze.py').read_bytes()).hexdigest()
    previous=json.loads(Path('reports/evidence/m002_2/results/trial_provenance.json').read_text())
    trials=json.loads((output/'trial_provenance.json').read_text())
    report=json.loads((output/'comparison.json').read_text())
    with (output/'all_realization_errors.csv').open() as file:
        actual_errors={(int(row['network_id']),int(row['replicate_id']),float(row['gain']),row['target']):row for row in csv.DictReader(file)}
    assert len(actual_errors)==200

    with np.load(output/'calibration_data.npz',allow_pickle=False) as archive:data={k:archive[k] for k in archive.files}
    assert data['observed_counts'].shape==(10,5,2,4,300,20)
    assert data['prefix_counts'].shape==(10,5,2550,20)
    noises=set();eta=set();count=0;qualified=[];budgets=[]
    for n in range(10):
        parameters=realization(Config(network_id=n))
        assert np.intersect1d(parameters['stimulation'],parameters['recording']).size==0
        original=next(t for t in previous if t['network_id']==n)
        base=[];sectors=[];spans=[];sigmas=[];margins=[];valids=[];errors=[];stable=True
        for ri,rep in enumerate(range(8,13)):
            t=next(t for t in trials if t['network_id']==n and t['replicate_id']==rep)
            folder=raw/f'network_{n}_replicate_{rep}'
            assert t==json.loads((folder/'trial.json').read_text())
            with np.load(folder/'numerical.npz',allow_pickle=False) as archive:
                for key in archive.files:np.testing.assert_array_equal(data[key][n,ri],archive[key])
            config=t['engine']['config']
            assert config['root_seed']==20261018 and config['dt_us']==100 and config['efficacy']==1 and config['retain_spikes']
            assert t['engine']['metadata']['parameter_hashes']==original['engine']['metadata']['parameter_hashes']
            assert t['engine']['config']['replicate_id']==rep and t['engine']['config']['network_id']==n
            noise=json.dumps(t['engine']['noise_hashes'],sort_keys=True);noises.add(noise);eta.add(t['checkpoint_hashes']['eta'])
            assert set(t['engine']['noise_hashes'])==set(map(str,range(57)))
            for k in ('stimulation','recording'):np.testing.assert_array_equal(data[k][n,ri],parameters[k])
            pc=data['prefix_counts'][n,ri];assert pc.min()>=0
            sector_counts=pc.reshape(2550,4,5)[:,:,:4].sum(axis=-1)
            initial=sector_counts[350:750].sum(axis=0)/160
            b=initial.mean();base.append(b);sectors.append(initial)
            raw_prefix=sector_counts.sum(axis=-1)/1.6
            h=np.r_[0.,[raw_prefix[1000+400*j:1150+400*j].mean()-raw_prefix[800+400*j:950+400*j].mean() for j in range(4)]]
            target=b+np.array([.1,.9])*.6*h[-1];span=.48*h[-1]
            valid=bool(np.isfinite(h).all() and np.all(np.diff(h)>1e-9))
            saved=t['calibration'];np.testing.assert_allclose(saved['h_hz'],h,rtol=0,atol=1e-12)
            np.testing.assert_allclose(saved['targets_hz'],target,rtol=0,atol=1e-12)
            assert abs(saved['baseline_hz']-b)<1e-12 and abs(saved['span_hz']-span)<1e-12 and saved['valid']==valid
            q=[]
            if valid:
                for excursion in target-b:
                    assert 0<=excursion<=h[-1]
                    j=min(max(int(np.searchsorted(h,excursion,side='right'))-1,0),3)
                    q.append(30*j+30*(excursion-h[j])/(h[j+1]-h[j]))
                np.testing.assert_allclose(q,saved['lookup_pA'],rtol=0,atol=1e-10)
            else:
                assert saved['lookup_pA'] is None;q=[0.,0.]
            desired=np.zeros((2550,4))
            for j,dose in enumerate((30,60,90,120)):desired[950+400*j:1150+400*j,::2]=dose
            expected=desired.copy();prior=np.zeros(4)
            for row in expected:row[:]=np.minimum(np.maximum(row,prior-30),prior+30);prior=row.copy()
            np.testing.assert_array_equal(expected,data['prefix_delivered_pA'][n,ri])
            assert expected.sum()*.02==2400 and np.all(expected[-1]==0)
            filt=RateFilter();prefix_filtered=[filt.update(c,(k+1)*20000)[1] for k,c in enumerate(pc)]
            np.testing.assert_array_equal(prefix_filtered,data['prefix_filtered_hz'][n,ri])
            snapshot=filt.value.copy();late=np.empty((2,4))
            for gi,gain in enumerate((1.,.6)):
                for ai,name in enumerate(('S','C120','L','H')):
                    oc=data['observed_counts'][n,ri,gi,ai];nc=data['neuron_counts'][n,ri,gi,ai]
                    assert oc.min()>=0 and nc.min()>=0
                    for j,ids in enumerate(parameters['recording']):assert oc[:,j].sum()==nc[ids].sum()
                    sc=oc.reshape(300,4,5)[:,:,:4].sum(axis=-1)
                    rates=sc.sum(axis=-1)/1.6;late[gi,ai]=rates[50:].mean()
                    stable=stable and bool(np.all(sc.sum(axis=0)/120<100))
                    filt=RateFilter();filt.initialized=True;filt.value=snapshot.copy()
                    expected_filter=[filt.update(c,51_020_000+k*20000)[1] for k,c in enumerate(oc)]
                    np.testing.assert_array_equal(expected_filter,data['filtered_sector_rates_hz'][n,ri,gi,ai])
                    aq=(0.,120.,*q)[ai];prior=np.zeros(4);action=np.zeros((300,4))
                    for row in action:
                        row[::2]=aq;row[:]=np.minimum(np.maximum(row,prior-30),prior+30);prior=row.copy()
                    actual=data['delivered_current_pA'][n,ri,gi,ai]
                    np.testing.assert_allclose(action,actual,rtol=0,atol=1e-10)
                    assert actual.min()>=0 and actual.max()<=120 and actual.sum(axis=1).max()<=240
                    assert np.abs(np.diff(np.vstack([np.zeros(4),actual]),axis=0)).max()<=30
                    receipt=t['receipt_ledger'][gi*4+ai];exposure=float(actual.sum()*.02)
                    assert receipt['constraint_violations']==0 and abs(receipt['total_exposure_pA_s']-exposure)<1e-8
                    assert receipt['start_us']==51_000_000 and receipt['stop_us']==57_000_000
                    assert abs(receipt['effective_exposure_pA_s']-gain*exposure)<1e-8
                    assert receipt['safe_fallback']==(ai>=2 and not valid)
                    budgets.append(exposure);count+=1
            for key in ('observed_counts','neuron_counts','filtered_sector_rates_hz'):
                np.testing.assert_array_equal(data[key][n,ri,0,0],data[key][n,ri,1,0])
            np.testing.assert_array_equal(data['delivered_current_pA'][n,ri,0],data['delivered_current_pA'][n,ri,1])
            for gi,gain in enumerate((1.,.6)):
                for ti,name in enumerate(('L','H')):
                    row=actual_errors[n,rep,gain,name]
                    assert abs(float(row['target_hz'])-target[ti])<1e-12
                    assert abs(float(row['actual_late_hz'])-late[gi,ti+2])<1e-12
                    assert abs(float(row['signed_error_hz'])-(late[gi,ti+2]-target[ti]))<1e-12
                    assert (row['calibration_valid']=='True')==valid and (row['safe_fallback']=='True')==(not valid)
                    if span>0:assert abs(float(row['normalized_actual_error'])-abs(late[gi,ti+2]-target[ti])/span)<1e-10
                    else:assert row['normalized_actual_error']==''
            sigma=(data['observed_counts'][n,ri,0,0,50:].reshape(5,50,4,5)[:,:,:,:4].sum(axis=(1,2,3))/80).std(ddof=1)
            margins.append(late[1,1]-late[1,0]-(target[1]-b));spans.append(span);sigmas.append(sigma);valids.append(valid)
            errors.append(np.abs(late[:,2:]-target)/span if valid and span>0 else np.full((2,2),np.nan))
        margins=np.array(margins);errors=np.array(errors)
        comp=dict(baseline_valid=bool(np.all((np.array(base)>=1)&(np.array(base)<=30)) and np.max(sectors)<100 and stable),
            minimum_span=bool(np.mean(spans)>=1),noise=bool(np.mean(spans)>=2*np.sqrt(np.mean(np.array(sigmas)**2))),
            headroom=bool(margins.mean()-2.7764451051977987*margins.std(ddof=1)/np.sqrt(5)>=0),calibration=all(valids))
        for gi,gain in enumerate((1.,.6)):
            for ti,name in enumerate(('L','H')):comp[f'error_g{gain}_{name}']=bool(all(valids) and np.isfinite(errors[:,gi,ti]).all() and errors[:,gi,ti].mean()<=.25)
        assert comp==report['networks'][n]['components']
        qualified.append(all(comp.values()))
    assert count==400 and len(noises)==50 and len(eta)==50
    assert sum(qualified)==report['qualified_networks'] and report['constraint_violations']==0
    result=dict(status='PASS',checked_branches=count,checked_calibrations=50,checked_target_errors=200,distinct_noise_ledgers=len(noises),
        distinct_checkpoint_ou_states=len(eta),historical_files_unchanged=len(historical['sha256']),
        independently_recomputed_qualified_networks=sum(qualified),total_confirmation_exposure_pA_s=sum(budgets),
        execution_source_revision=source['head'],analysis_sha256=lineage['source_sha256'],
        verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),wall_s=(time.perf_counter_ns()-began)/1e9,
        limitations='Distinct analytical recomputation in this session, not external human or second-simulator replication; exact checkpoint queues/clocks also covered by unchanged regression tests.')
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main(*sys.argv[1:])
