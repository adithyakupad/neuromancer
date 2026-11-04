"""Independent rechecks of completed evidence; never uses outcomes to select actions."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from neuromancer.authority_diagnosis import TARGETS,action_schedule,action_audit


def main(raw,analysis):
    raw=Path(raw);analysis=Path(analysis)
    summary=json.loads((raw/'summary.json').read_text())
    assert summary['status']=='complete' and len(summary['trials'])==50
    for name,expected in summary['artifact_sha256'].items():
        assert hashlib.sha256((raw/name).read_bytes()).hexdigest()==expected,name
    prior=json.loads(Path('reports/evidence/m002_1/preservation.json').read_text())
    for name,expected in prior['sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==expected,name
    trials=json.loads((analysis/'trial_provenance.json').read_text())
    parameter_ids={};noise_ids={};checkpoints={}
    for trial in trials:
        n,r=trial['network_id'],trial['replicate_id']
        params=trial['engine']['metadata']['parameter_hashes']
        assert parameter_ids.setdefault(n,params)==params
        noise_ids[n,r]=trial['engine']['noise_hashes']
        checkpoints[n,r]=trial['checkpoint_hashes']['eta']
        assert len(trial['receipt_ledger'])==16
        assert all(x['constraint_violations']==0 for x in trial['receipt_ledger'])
    assert len({json.dumps(v,sort_keys=True) for v in parameter_ids.values()})==10
    assert len(set(checkpoints.values()))==50
    assert len({json.dumps(v,sort_keys=True) for v in noise_ids.values()})==50
    schedules=np.stack([action_schedule(t) for t in TARGETS])
    outcomes=json.loads((analysis/'outcomes.json').read_text())
    assert len(outcomes)==800
    names=json.loads((analysis/'comparison.json').read_text())['action_names']
    with np.load(analysis/'authority_data.npz',allow_pickle=False) as data:
        counts=data['spike_counts'];observed=data['observed_counts']
        assert counts.shape==(10,5,2,8,1000)
        np.testing.assert_array_equal(counts[:,:,0,0],counts[:,:,1,0])
        for record in outcomes:
            n,r=record['network_id'],record['replicate_id']
            g=0 if record['gain']==.6 else 1;a=names.index(record['action'])
            stim=data['stimulation'][n,r]
            rec=data['recording'][n,r].reshape(4,5,5)[:,:4,:].ravel()
            active=stim[TARGETS[a]>0].ravel()
            fixed=np.setdiff1d(np.arange(800),stim.ravel())
            members={'observed_E':rec,'fixed_unstim_E':fixed,'all_E':np.arange(800),
                'all_I':np.arange(800,1000),'hidden_fixed_unstim_E':np.setdiff1d(fixed,rec),
                'action_unstim_E':np.setdiff1d(np.arange(800),active)}
            if len(active):members['direct_active_E']=active
            delta=counts[n,r,g,a].astype(float)-counts[n,r,g,0]
            for label,indices in members.items():
                assert abs(delta[indices].sum()/(5*len(indices))-record['paired_response_hz'][label])<1e-12
            np.testing.assert_array_equal(data['delivered_current_pA'][n,r,g,a],schedules[a])
            assert action_audit(data['delivered_current_pA'][n,r,g,a])['constraint_violations']==0
            assert observed[n,r,g,a].reshape(250,4,5)[:,:,:4].sum()==counts[n,r,g,a,rec].sum()
        assert np.all(np.isfinite(data['group_current_mean_pA']))
    report=dict(status='PASS',raw_artifact_hashes_verified=len(summary['artifact_sha256']),
        original_files_byte_identical=len(prior['sha256']),complete_branches=800,
        independent_checkpoint_noise_ids=50,fixed_network_parameter_sets=10,
        rechecked_population_contrasts=800,rechecked_actual_schedules=800,
        constraints_violated=0,all_observation_counts_reconciled=True)
    (analysis/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main(sys.argv[1],sys.argv[2])
