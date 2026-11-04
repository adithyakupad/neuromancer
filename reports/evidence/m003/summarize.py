"""Descriptive exports of frozen M003 metrics; no selection or new gates."""
import argparse
import json
from pathlib import Path
import numpy as np
from neuromancer.identify import bootstrap
from analyze import save,csv_write


def main(output):
    output=Path(output)
    result=json.loads((output/'comparison.json').read_text())
    with np.load(output/'identification_data.npz',allow_pickle=False) as archive:d={k:archive[k] for k in archive.files}
    selected=np.flatnonzero(d['identities'][:,1]!=21)
    nets=sorted(set(d['identities'][selected,0]));effect=d['rates']-d['rates'][:,0,None]
    prediction=d['forecast']-d['forecast'][:,:,0,None]
    network=[]
    for n in nets:
        indices=np.flatnonzero((d['identities'][:,0]==n)&(d['identities'][:,1]!=21))
        per=[]
        for h in (1,10,50,100):
            error=prediction[indices,:,:,:h].mean(axis=3)-effect[indices,None,:,:h].mean(axis=3)
            per.append((error[:,:,1:]**2).mean(axis=(0,2,3)))
        network.append(per)
        np.testing.assert_allclose(per[2],np.array(next(v for v in result['networks'] if v['network_id']==n)['evoked_mse'])[:,2],rtol=0,atol=1e-12)
    random=[];sectors=[];exposure=[];unseen=[]
    for i in selected:
        n,r=map(int,d['identities'][i]);e=effect[i,:,:50].mean(axis=1);p=prediction[i,:,:,:50].mean(axis=2)
        random.append(dict(network_id=n,replicate_id=r,**{m:float(np.mean((p[j,5]-e[5])**2)) for j,m in enumerate(('CONSTANT','AR','ARX','SHUFFLED'))}))
        for a,name in enumerate(('S','P01','P12','P23','P03','R')):
            for s in range(4):sectors.append(dict(network_id=n,replicate_id=r,condition=name,sector=s,actual_hz=float(e[a,s]),ARX_hz=float(p[2,a,s])))
            currents=d['delivered'][i,a].sum(axis=1)
            exposure.append(dict(network_id=n,replicate_id=r,condition=name,max_total_pA=float(currents.max()),mean_total_pA=float(currents.mean()),charge_pA_s=float(currents.sum()*.02)))
        sequence=d['desired'][i,5];fit=d['prefix_desired'][i]
        collisions=sum(np.array_equal(sequence,fit[k:k+100]) for k in range(750,2350-99,25))
        unseen.append(dict(network_id=n,replicate_id=r,identical_fit_sequence_windows=int(collisions)))
    random_n=[]
    for n in nets:random_n.append([np.mean([v[m] for v in random if v['network_id']==n]) for m in ('CONSTANT','AR','ARX','SHUFFLED')])
    condition=json.loads((output/'conditioning.json').read_text());ranges={}
    for model in ('AR','ARX','SHUFFLED'):
        c=[v for v in condition if v['family']==model]
        assert all(v['valid'] for v in c)
        ranges[model]={key:[min(v[key] for v in c),max(v[key] for v in c)] for key in ('rank','condition','penalized_condition','spectral_radius','features','parameters')}
    designs=[]
    for i,(n,r) in enumerate(d['identities']):
        k=np.arange(753,2350);u=d['prefix_delivered'][i];x=np.hstack([u[k-lag] for lag in range(4)])
        z=(x-x.mean(axis=0))/np.maximum(x.std(axis=0),1);singular=np.linalg.svd(z,compute_uv=False)
        rank=int(np.linalg.matrix_rank(z));condition=float(singular[0]/singular[-1]);assert rank==16 and condition<=1e6
        designs.append(dict(network_id=int(n),replicate_id=int(r),rank=rank,condition=condition,singular_values=singular.tolist()))
    summary=dict(stage=result['stage'],input_designs=designs,horizon_bins=[1,10,50,100],network_mean_evoked_mse_by_horizon=bootstrap(network),random_condition_mse=bootstrap(random_n),
        conditioning_ranges=ranges,unseen_random_sequence_checks=unseen,charge_units='pA*s = pC per channel command, not physical electrode charge',
        all_primary_networks=len(nets),notes='Descriptive exports after frozen primary analysis; no new scientific gates.')
    save(output/'descriptive_summary.json',summary)
    csv_write(output/'random_condition_metrics.csv',random);csv_write(output/'sector_responses.csv',sectors);csv_write(output/'delivered_exposure.csv',exposure)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
