"""Independent stdlib verification of M008 records; imports no supervisor code."""
import argparse,collections,csv,hashlib,json,os,statistics,subprocess
from pathlib import Path

def load(p):return json.loads(p.read_text())
def percentile(xs,q):
    if not xs:return None
    a=sorted(xs);z=(len(a)-1)*q;i=int(z);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(z-i)
def distribution(xs):return dict(n=len(xs),median=statistics.median(xs) if xs else None,p95=percentile(xs,.95),maximum=max(xs) if xs else None,minimum=min(xs) if xs else None)
def events(path):return [json.loads(line) for line in path.read_text().splitlines()]

def verify_traced(root):
    manifest=load(root/'manifest.json');outer=load(root/'outer.json');assert len(outer)==35
    assert all(not r['watchdog'] and r['returncode']==0 for r in outer)
    rows=[]
    for item in outer:
        folder=root/f"{item['index']:02d}_{item['condition']}";r=load(folder/'returned.json');context=load(folder/'context.json');trace=load(folder/'supervision/lifecycle.json');worker=events(folder/'worker/events.jsonl');w=r['workers'][0]
        assert r==load(folder/'supervision/terminal.json')
        assert r['cleanup_verified'] and w['parent_reaped'] and w['state']=='REAPED'
        assert r['finished_ns']<=r['deadline_ns'] and not r['post_deadline_cleanup']
        assert r['deadline_ns']-r['work_cutoff_ns']==800000000
        assert r['deadline_ns']==context['deadline_ns'] and r['deadline_clock_id']==context['clock_id']
        for seq in (trace['events'],worker):
            times=[e['monotonic_ns'] for e in seq];assert times==sorted(times)
            assert all(e['clock_id']==context['clock_id'] and e['remaining_ns']==context['deadline_ns']-e['monotonic_ns'] for e in seq)
        after=next(e for e in trace['events'] if e['kind']=='cutoff_check' and e['phase']=='after_loop')
        cleanup=next(e for e in trace['events'] if e['kind']=='cleanup_begin')
        late=after['monotonic_ns']>=r['work_cutoff_ns'] or cleanup['monotonic_ns']>=r['work_cutoff_ns']
        assert r['status']==('DEADLINE_EXCEEDED' if late else 'COMPLETED')
        if item['condition'] in ('wake_delay','parent_delay','import_delay','persist_delay'):assert late
        assert load(folder/'checked.json')['cleanup_verified']
        by={e['kind']:e for e in worker};spawn=next(e for e in trace['events'] if e['kind']=='process_create_begin')
        row=dict(index=item['index'],condition=item['condition'],status=r['status'],startup_ms=(by['worker_entry']['monotonic_ns']-spawn['monotonic_ns'])/1e6,imports_ms=None,sleep_envelope_overshoot_ms=None,atexit_to_observation_upper_ms=None,exit_to_observation_bound_ms=None,observed_exit_margin_ms=(r['work_cutoff_ns']-w['first_observed_exit_ns'])/1e6,cleanup_ms=(r['finished_ns']-cleanup['monotonic_ns'])/1e6,total_supervision_ms=(r['finished_ns']-r['started_ns'])/1e6)
        if 'imports_completed' in by:row['imports_ms']=(by['imports_completed']['monotonic_ns']-by['imports_begin']['monotonic_ns'])/1e6
        if 'sleep_wake' in by:row['sleep_envelope_overshoot_ms']=(by['sleep_wake']['monotonic_ns']-by['sleep_request']['monotonic_ns'])/1e6-by['sleep_request']['requested_s']*1000
        if 'worker_atexit' in by:row['atexit_to_observation_upper_ms']=(w['first_observed_exit_ns']-by['worker_atexit']['monotonic_ns'])/1e6
        if w.get('last_running_poll_ns') is not None:row['exit_to_observation_bound_ms']=(w['first_observed_exit_ns']-w['last_running_poll_ns'])/1e6
        for kind in ('progress','terminal'):
            starts=[e['monotonic_ns'] for e in trace['events'] if e['kind']==kind+'_write_begin'];ends=[e['monotonic_ns'] for e in trace['events'] if e['kind']==kind+'_write_end'];assert len(starts)==len(ends)
            row[kind+'_write_max_ms']=max((b-a)/1e6 for a,b in zip(starts,ends,strict=True))
        rows.append(row)
    summary={}
    for condition in sorted({r['condition'] for r in rows}):
        group=[r for r in rows if r['condition']==condition]
        summary[condition]=dict(statuses=dict(collections.Counter(r['status'] for r in group)),metrics={k:distribution([r[k] for r in group if r[k] is not None]) for k in rows[0] if k.endswith('_ms')})
    return dict(status='PASS',trials=len(rows),summary=summary,rows=rows,clock_id=manifest['clock_id'],limitations='Actual kernel exit time is interval-censored; atexit-to-observation includes remaining interpreter teardown. Sleep envelope includes trace writes. Trace publication envelope includes trace persistence.')

def verify_repeats(root,handshake=False):
    results=load(root/'results.json');assert len(results)==20
    assert all(r['returncode']==0 and not r['outer_watchdog'] for r in results)
    rows=[]
    for i in range(20):
        folder=root/f'repeat{i:02d}/pytest/test_real_worker_lifecycle_bef0';r=load(folder/'returned.json');w=r['workers'][0]
        assert r['status']=='COMPLETED' and r['cleanup_verified'] and w['parent_reaped'] and w['state']=='REAPED'
        assert r['finished_ns']<=r['deadline_ns']
        observed=w.get('first_observed_exit_ns',w['events'][-1]['monotonic_ns']);assert observed<r['work_cutoff_ns']
        if handshake:
            assert not load(folder/'outer_watchdog.json')['watchdog_intervened']
            assert not load(folder/'handshake_driver.json')['errors']
            markers={e['kind']:e for e in events(folder/'worker/events.jsonl')};release=load(folder/'worker/release.json')
            assert markers['ready']['monotonic_ns']<=release['released_ns']<=markers['release_seen']['monotonic_ns']<=markers['worker_atexit']['monotonic_ns']<=observed
        rows.append(dict(index=i,margin_ms=(r['work_cutoff_ns']-observed)/1e6,supervision_ms=(r['finished_ns']-r['started_ns'])/1e6))
    return dict(repeats=20,status='PASS',observed_exit_margin_ms=distribution([r['margin_ms'] for r in rows]),rows=rows)

def preservation():
    allowed={'src/neuromancer/supervisor.py','tests/test_supervisor.py','tests/supervisor_worker.py','.github/workflows/ci.yml','.github/workflows/v1-qualification.yml','tests/test_calibration.py'};changed={};count=0
    for record in subprocess.check_output(['git','ls-tree','-rz','ce147866186e8502af343157e4e0d45ac446665a']).split(b'\0'):
        if not record:continue
        meta,name=record.split(b'\t',1);name=name.decode();old=meta.split()[2].decode();p=Path(name)
        assert p.exists() or p.is_symlink(),name
        data=os.readlink(p).encode() if p.is_symlink() else p.read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();count+=1
        if old!=actual:changed[name]=dict(before_git_blob=old,after_git_blob=actual,sha256=hashlib.sha256(data).hexdigest())
    assert set(changed)==allowed,changed
    return dict(status='PASS',starting_files=count,unchanged=count-len(changed),authorized_engineering_changes=changed,scientific_source_protocols_and_archives='unchanged')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path('reports/engineering/evidence/m008'));parser.add_argument('--traced',type=Path);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();assert not a.output.exists(),a.output
    if a.traced:r=verify_traced(a.traced)
    else:r=dict(status='PASS',original=verify_repeats(a.root/'original'),traced=verify_traced(a.root/'traced'),corrected=verify_repeats(a.root/'handshake',True),preservation=preservation())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n')
    rows=r.get('rows',r.get('traced',{}).get('rows',[]))
    if rows:
        with a.output.with_suffix('.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    print(json.dumps(dict(status=r['status'],output=str(a.output))))
if __name__=='__main__':main()
