"""Independent actual-acquisition budget, lifecycle, cohort and source auditor."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('output',type=Path);p.add_argument('selection',type=Path);a=p.parse_args()
    meta=json.loads((a.raw/'provenance.json').read_text());summary=json.loads((a.raw/'summary.json').read_text())
    supervisor=json.loads((a.raw/'supervision/terminal.json').read_text())
    assert summary['status']=='complete' and supervisor['status']=='COMPLETED' and supervisor['cleanup_verified']
    assert supervisor['deadline_ns']==meta['deadline_monotonic_ns']
    assert meta['deadline_monotonic_ns']-meta['started_monotonic_ns']==5400*10**9
    assert meta['wall_limit_s']==5400 and meta['replicates']==[41,42] and meta['networks']==list(range(10))
    assert supervisor['finished_ns']<supervisor['work_cutoff_ns']<supervisor['deadline_ns']
    assert len(supervisor['workers'])==20
    intervals=[];owned=[]
    for w in supervisor['workers']:
        assert w['terminal']=='COMPLETED' and w['state']=='REAPED' and w['returncode']==0
        events=w['events'];times=[e['monotonic_ns'] for e in events];assert times==sorted(times)
        assert [e['state'] for e in events]==['CREATED','RUNNING','REAPED']
        command=w['command'];assert command[-1]==str(supervisor['deadline_ns'])
        assert command[1:4]==['-m','neuromancer.control_experiment','--worker']
        intervals.extend([(events[1]['monotonic_ns'],1),(events[2]['monotonic_ns'],-1)])
        owned.append(w['pid'])
    count=peak=0
    for _,change in sorted(intervals):count+=change;peak=max(peak,count)
    assert count==0 and peak<=3
    selected=json.loads(a.selection.read_text())['controller']
    assert meta['names']==['ZERO','FIXED','MAX',selected]
    assert hashlib.sha256(a.selection.read_bytes()).hexdigest()==meta['selection_sha256']
    trials=[json.loads(f.read_text()) for f in a.raw.glob('n*_r*/trial.json')]
    assert {(m['network_id'],m['replicate_id']) for m in trials}=={(n,r) for n in range(10) for r in (41,42)}
    assert len(trials)==20
    for m in trials:
        assert m['status']=='complete' and len(m['branches'])==8
        assert m['peak_rss_bytes']<2*1024**3
        assert {(b['condition'],b['controller']) for b in m['branches']}=={(c,k) for c in ('STATIC','LOSS') for k in meta['names']}
        assert all(b['audit']['violations']==0 for b in m['branches'])
    current={f'neuromancer/{f.name}':hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('src/neuromancer').glob('*.py')}
    assert current==meta['source_hashes']
    closure=json.loads((a.raw.parent/'acquisition_closure.json').read_text())
    assert closure['returncode']==0 and 0<=closure['calendar_duration_s']<=5400
    assert closure['summary_sha256']==hashlib.sha256((a.raw/'summary.json').read_bytes()).hexdigest()
    assert closure['monotonic_duration_s']<=5400
    table=subprocess.check_output(['ps','-axo','pid=,stat='],text=True)
    states={int(line.split()[0]):line.split()[1] for line in table.splitlines()}
    assert not [pid for pid in owned if pid in states] # Group reaping also recorded by supervisor.
    preservation=json.loads(Path('reports/evidence/m005a_3/preservation.json').read_text())['historical_sha256']
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in preservation.items())
    result=dict(status='PASS',trials=20,branches=160,max_concurrent_workers=peak,
        supervisor_wall_s=(supervisor['finished_ns']-supervisor['started_ns'])/1e9,
        acquisition_wall_s=summary['wall_ns']/1e9,
        calendar_duration_s=closure['calendar_duration_s'],remaining_deadline_s=(supervisor['deadline_ns']-supervisor['finished_ns'])/1e9,
        peak_worker_rss_bytes=max(m['peak_rss_bytes'] for m in trials),
        historical_files_unchanged=len(preservation),owned_pids=owned,live_owned_pids=[],
        selected_controller=selected,source_revision=meta['head'])
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
