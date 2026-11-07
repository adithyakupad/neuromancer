"""Independent resource, source lineage and trial identity reconciliation."""
import hashlib,json,os,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from neuromancer.supervisor import Deadline
r=Path(__file__).resolve().parent;Deadline.from_environment().check()
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=read(r/'plan.json');c=read(r/'acquisition_closure.json');launch=read(r/'acquisition_launch.json');meta=read(r/'continuation/provenance.json');term=read(r/'continuation/supervision/terminal.json')
assert c['status']=='COMPLETE' and c['returncode']==0 and c['reason'] is None and 0<c['elapsed_s']<=4800
assert c['deadline_ns']-c['started_ns']==4800*10**9
assert c['clock_id']==term['deadline_clock_id']==meta['deadline_clock_id']
assert term['deadline_ns']==c['deadline_ns']==meta['deadline_monotonic_ns']
assert term['status']=='COMPLETED' and term['cleanup_verified'] and term['finished_ns']<term['work_cutoff_ns']<term['deadline_ns']
assert len(term['workers'])==17 and meta['trial_pairs']==p['missing']
intervals=[]
for w,pair in zip(term['workers'],p['missing']):
    assert w['returncode']==0 and w['terminal']=='COMPLETED' and w['parent_reaped']
    assert w['command'][4:6]==list(map(str,pair)) and w['command'][-1]==str(c['deadline_ns'])
    ev=w['events'];assert [e['state'] for e in ev]==['CREATED','RUNNING','REAPED']
    assert [e['monotonic_ns'] for e in ev]==sorted(e['monotonic_ns'] for e in ev)
    intervals.extend([(ev[1]['monotonic_ns'],1),(ev[2]['monotonic_ns'],-1)])
    try:os.killpg(w['pgid'],0)
    except ProcessLookupError:pass
    else:raise AssertionError('Owned group remains')
count=peak=0
for _,v in sorted(intervals):count+=v;peak=max(count,peak)
assert count==0 and peak<=3
assert sha('reports/evidence/m005a_3/tuning_analysis/selection.json')==p['selection_sha256']==launch['selection_sha256']==meta['selection_sha256']
assert launch['head']==meta['head']==c['head']
assert subprocess.check_output(['git','show',launch['head']+':docs/research/011_M005A_5_CONFIRMATION_CONTINUATION.md'])==Path('docs/research/011_M005A_5_CONFIRMATION_CONTINUATION.md').read_bytes()
current={'neuromancer/'+f.name:sha(f) for f in Path('src/neuromancer').glob('*.py')}
assert current==meta['source_hashes']
lineage=read(r/'lineage.json')['trials'];assert len(lineage)==20 and len({(t['network'],t['replicate']) for t in lineage})==20
for t in lineage:
    root=Path(t['source']);sm=read(root.parent/'provenance.json')
    expected={key:hashlib.sha256(subprocess.check_output(['git','show',t['source_revision']+':src/'+key])).hexdigest() for key in sm['source_hashes']}
    assert expected==sm['source_hashes']
    for name,h in t['sha256'].items():assert sha(root/name)==h==sha(r/'confirmation'/root.name/name)
    m=read(root/'trial.json');n=t['network'];old=read(f'reports/evidence/m005a/results/tune/n{n}_r40/trial.json')
    assert m['engine']['metadata']['parameter_hashes']==old['engine']['metadata']['parameter_hashes']
    assert m['peak_rss_bytes']<2*1024**3
    assert all(b['audit']['violations']==0 for b in m['branches'])
old=read('reports/evidence/m005a_3/confirmation/provenance.json')
# Clock/supervisor acquisition plumbing changes only: actual scientific sources identical.
changed=[k for k,v in old['source_hashes'].items() if current.get(k)!=v]
assert set(changed)=={'neuromancer/control_experiment.py','neuromancer/supervisor.py'}
for f,h in read(r/'preservation.json')['historical_sha256'].items():assert sha(f)==h
samples=[json.loads(line) for line in (r/'resource_samples.jsonl').read_text().splitlines()]
assert samples and all(s['clock_id']==c['clock_id'] and not s['faults'] and s['allocated_bytes']<=500*1024**2 and s['peak_rss_bytes']<2*1024**3 and all(v<2*1024**3 for v in s['rss_bytes'].values()) for s in samples)
pre=read(r/'preflight_supervision/terminal.json');assert pre['status']=='COMPLETED' and pre['cleanup_verified']
result=dict(status='PASS',new_trials=17,reused_trials=3,combined_trials=20,branches=160,max_concurrent_workers=peak,source_revision=launch['head'],clock_id=c['clock_id'],continuation_elapsed_s=c['elapsed_s'],old_plus_new_calendar_s=542.8625130653381+c['calendar_s'],remaining_deadline_s=(term['deadline_ns']-term['finished_ns'])/1e9,peak_worker_rss_bytes=max(read(f"{t['source']}/trial.json")['peak_rss_bytes'] for t in lineage),max_sampled_allocation_bytes=max(s['allocated_bytes'] for s in samples),resource_samples=len(samples),scientific_sources_unchanged=True,historical_files_preserved=len(read(r/'preservation.json')['historical_sha256']))
(r/'resource_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
