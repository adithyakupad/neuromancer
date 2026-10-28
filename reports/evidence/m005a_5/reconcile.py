"""Immutable combined view: original three plus exactly seventeen new trials."""
import hashlib,json,os,subprocess
from pathlib import Path
from neuromancer.supervisor import Deadline,atomic_json
r=Path(__file__).resolve().parent;Deadline.from_environment().check()
plan=json.loads((r/'plan.json').read_text());closure=json.loads((r/'acquisition_closure.json').read_text())
assert closure['status']=='COMPLETE' and closure['elapsed_s']<=4800
old=Path('reports/evidence/m005a_3/confirmation');new=r/'continuation';combined=r/'confirmation'
combined.mkdir(exist_ok=False)
assert {(int(p.name.split('_')[0][1:]),int(p.name.split('_')[1][1:])) for p in new.glob('n*_r*')}==set(map(tuple,plan['missing']))
lineage=[]
for pair in [(n,k) for n in range(10) for k in (41,42)]:
    n,k=pair;session='original' if list(pair) in plan['reused'] else 'continuation';source=(old if session=='original' else new)/f'n{n}_r{k}'
    m=json.loads((source/'trial.json').read_text());assert (m['network_id'],m['replicate_id'])==pair and m['status']=='complete' and len(m['branches'])==8
    assert {(b['condition'],b['controller']) for b in m['branches']}=={(c,name) for c in ('STATIC','LOSS') for name in plan['names']}
    dest=combined/source.name;dest.mkdir();hashes={}
    for f in source.iterdir():
        assert f.is_file() and f.suffix!='.tmp' and f.name not in ('partial.npz','failure.json')
        os.link(f,dest/f.name);hashes[f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
    source_meta=json.loads(((old if session=='original' else new)/'provenance.json').read_text())
    lineage.append(dict(network=n,replicate=k,session=session,source=str(source),source_revision=source_meta['head'],sha256=hashes))
meta=json.loads((new/'provenance.json').read_text());meta.update(simulated_seconds=6140,trial_pairs=[[n,k] for n in range(10) for k in (41,42)],combined_view=True,acquisition_sessions=['original','continuation'],interpretation='One ten-network cohort, two noise repeats; chronological sessions are not independent cohorts')
atomic_json(combined/'provenance.json',meta);atomic_json(r/'lineage.json',dict(status='PASS',trials=lineage,total_trials=20,branches=160,reused=3,new=17))
Deadline.from_environment().check()
