"""Reproduce seed independence and private evaluator channel-assignment checks."""
import hashlib
import json
from pathlib import Path
import numpy as np

streams={};checks=0
for root in (Path('reports/evidence/m004/results/dev_raw'),Path('reports/evidence/m004/results/validation_raw')):
    for trial in sorted(root.glob('n*_r*')):
        meta=json.loads((trial/'trial.json').read_text());cfg=meta['engine']['config'];key=(meta['network_id'],meta['replicate_id'])
        assert (cfg['network_id'],cfg['replicate_id'])==key and cfg['root_seed']==20261018 and cfg['dt_us']==100
        ledger=meta['engine']['noise_hashes'];assert set(ledger)=={str(i) for i in range(79)}
        digest=hashlib.sha256(json.dumps(ledger,sort_keys=True).encode()).hexdigest()
        if key in streams:assert streams[key]['ledger_sha256']==digest
        else:streams[key]=dict(network=key[0],replicate=key[1],ledger_sha256=digest,first_fine_sha256=ledger['0']['fine'])
        with np.load(trial/'evaluator.npz') as f:recording=f['recording'].copy();stim=f['stimulation'].copy()
        assert not set(recording.ravel()) & set(stim.ravel())
        for t in (54,64,74):
            for branch in ('active','sham'):
                with np.load(trial/f'probe{t}_{branch}.npz') as f:
                    for c,ids in enumerate(recording):assert f['counts'][:,c].sum()==f['neurons'][ids].sum();checks+=1
assert len(streams)==36 and len({s['first_fine_sha256'] for s in streams.values()})==36
result=dict(status='PASS',independent_network_noise_identities=36,shared_streams_only_for_matched_conditions=True,blocks_per_primary_trajectory=79,
    channel_population_count_checks=checks,all_memberships_disjoint=True,streams=list(streams.values()),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
Path('reports/evidence/m004/seed_membership_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('Independent seed/membership audit PASS',len(streams),checks)
