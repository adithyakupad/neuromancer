"""Independent checks of all completed M002.2 data and unchanged historical evidence."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from neuromancer._brian import realization
from neuromancer.observation import RateFilter
from neuromancer.substrate import Config
from neuromancer.authority_diagnosis import evaluator_groups
from neuromancer.reachability import intervention_bank,NAMES,GAINS,REPLICATES,EXPECTED_EXPOSURE


def main(raw,output):
    raw=Path(raw);output=Path(output)
    complete=json.loads((raw/'summary.json').read_text())
    assert complete['status']=='complete' and len(complete['trials'])==30
    for name,digest in complete['artifact_sha256'].items():
        assert hashlib.sha256((raw/name).read_bytes()).hexdigest()==digest,name
    prior=json.loads(Path('reports/evidence/m002_2/preservation.json').read_text())
    for name,digest in prior['sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
    source=json.loads((raw/'provenance.json').read_text())
    for name,digest in source['source_hashes'].items():assert hashlib.sha256((Path('src')/name).read_bytes()).hexdigest()==digest,name
    for name,digest in source['preregistration_files_sha256'].items():
        assert hashlib.sha256((Path('reports/evidence/m002_2')/name).read_bytes()).hexdigest()==digest,name
    trials=json.loads((output/'trial_provenance.json').read_text())
    noise={};eta=set();params={};checks=0
    own_late=np.empty((10,3,2,12));own_baseline=np.empty((10,3))
    sigma_filtered=np.empty((10,3));sigma_epoch=np.empty((10,3))
    historical=json.loads(Path('reports/evidence/m002_1/results/trial_provenance.json').read_text())
    desired,bank=intervention_bank()
    with np.load(output/'reachability_data.npz',allow_pickle=False) as archive:
        data={key:archive[key] for key in archive.files}
        assert data['observed_counts'].shape==(10,3,2,12,300,20)
        for n in range(10):
            original=next(t for t in historical if t['network_id']==n and t['replicate_id']==0)
            parameters=realization(Config(network_id=n));groups=evaluator_groups(parameters)
            assert len(np.intersect1d(parameters['stimulation'],parameters['recording']))==0
            for r,rep in enumerate(REPLICATES):
                trial=next(t for t in trials if t['network_id']==n and t['replicate_id']==rep)
                identity=trial['engine']['metadata']['parameter_hashes']
                assert identity==original['engine']['metadata']['parameter_hashes']
                assert params.setdefault(n,identity)==identity
                eta.add(trial['checkpoint_hashes']['eta'])
                noise[n,rep]=trial['engine']['noise_hashes']
                np.testing.assert_array_equal(data['stimulation'][n,r],parameters['stimulation'])
                np.testing.assert_array_equal(data['recording'][n,r],parameters['recording'])
                np.testing.assert_array_equal(data['bin_start_us'][n,r],np.arange(15_000_000,21_000_000,20_000))
                base=data['baseline_counts'][n,r].reshape(400,4,5)[:,:,:4]
                initial=base.sum(axis=(0,2))/(20*8)
                assert abs(initial.mean()-trial['baseline_observed_E_hz'])<1e-12
                own_baseline[n,r]=initial.mean()
                sigma_filtered[n,r]=data['filtered_sector_rates_hz'][n,r,0,0,50:].mean(axis=-1).std(ddof=1)
                sigma_epoch[n,r]=data['raw_rate_hz'][n,r,0,0,50:].reshape(5,50).mean(axis=-1).std(ddof=1)
                for key in ('neuron_counts','observed_counts','filtered_sector_rates_hz','group_counts'):
                    np.testing.assert_array_equal(data[key][n,r,0,0],data[key][n,r,1,0])
                for g,gain in enumerate(GAINS):
                    for a,name in enumerate(NAMES):
                        rows=data['delivered_current_pA'][n,r,g,a]
                        np.testing.assert_array_equal(rows,bank[a])
                        np.testing.assert_array_equal(data['desired_target_pA'][n,r,a],desired[a])
                        assert rows.min()>=0 and rows.max()<=120 and rows.sum(axis=1).max()<=240
                        assert np.abs(np.diff(np.vstack([np.zeros(4),rows]),axis=0)).max()<=30
                        assert abs(rows.sum()*.02-EXPECTED_EXPOSURE[a])<1e-9
                        gc=data['group_counts'][n,r,g,a];nc=data['neuron_counts'][n,r,g,a]
                        assert (gc>=0).all() and (nc>=0).all()
                        for j,ids in enumerate(groups.values()):assert gc[:,j].sum()==nc[ids].sum()
                        oc=data['observed_counts'][n,r,g,a].reshape(300,4,5)[:,:,:4]
                        np.testing.assert_array_equal(gc[:,0],oc.sum(axis=(1,2)))
                        sector=oc.sum(axis=-1)/.4
                        np.testing.assert_allclose(sector.mean(axis=-1),data['raw_rate_hz'][n,r,g,a],rtol=0,atol=1e-12)
                        contrast=(nc[groups['observed_E']]-data['neuron_counts'][n,r,g,0,groups['observed_E']]).sum()/(80*6)
                        assert abs(contrast-data['whole_response_hz'][n,r,g,a])<1e-12
                        sham=data['observed_counts'][n,r,g,0].reshape(300,4,5)[:,:,:4]
                        own_late[n,r,g,a]=(oc[50:].sum()-sham[50:].sum())/(80*5)
                        assert abs(own_late[n,r,g,a]-data['late_response_hz'][n,r,g,a])<1e-12
                        filt=RateFilter();filt.value=initial.copy();filt.initialized=True
                        expected=[filt.update(counts,15_020_000+k*20_000)[1]
                                  for k,counts in enumerate(data['observed_counts'][n,r,g,a])]
                        np.testing.assert_array_equal(expected,data['filtered_sector_rates_hz'][n,r,g,a])
                        checks+=1
    assert checks==720 and len(eta)==30 and len(noise)==30
    assert len({json.dumps(v,sort_keys=True) for v in noise.values()})==30
    gate=json.loads((output/'comparison.json').read_text())['objective_gate']
    scale=.6*own_late[:,:,0,8].mean(axis=1);span=.8*scale;high=.9*scale
    reduced=own_late[:,:,1,8]
    lower=reduced.mean(axis=1)-4.3026527299*reduced.std(axis=1,ddof=1)/np.sqrt(3)
    np.testing.assert_allclose(gate['scale_hz'],scale,atol=1e-12,rtol=0)
    np.testing.assert_allclose(gate['reduced_response_lower95_hz'],lower,atol=1e-12,rtol=0)
    for label,sigma in [('filtered100ms',sigma_filtered),('epoch1s',sigma_epoch)]:
        rms=np.sqrt((sigma**2).mean(axis=1))
        expected=(span>=1)&(span>=2*rms)&(high<=lower)&((own_baseline>=1)&(own_baseline<=30)).all(axis=1)
        assert gate['scales'][label]['network_pass']==expected.tolist()
    report=dict(status='PASS',complete_branches=checks,original_files_byte_identical=len(prior['sha256']),
        raw_hashes_verified=len(complete['artifact_sha256']),fixed_network_parameter_sets=len(params),
        independent_noise_checkpoints=len(eta),causal_filters_exact_recomputed=720,
        actual_schedules_checked=720,constraint_violations=0,all_group_and_neuron_counts_reconciled=True,
        source_and_preregistration_hashes_verified=True,original_parameter_hashes_verified=True,target_gates_independently_recomputed=True)
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main(sys.argv[1],sys.argv[2])
