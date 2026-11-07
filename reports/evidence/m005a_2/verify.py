"""Independent evidence checks; does not import the supervisor or run workers."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

root=Path(__file__).resolve().parent
records=[]
allowed={'COMPLETED','DEADLINE_EXCEEDED','WORKER_FAILURE','CLEANUP_FAILURE','SUPERVISOR_FAILURE'}
for path in sorted((root/'final_release_trials').glob('*/returned.json')):
    r=json.loads(path.read_text())
    assert r['status'] in allowed
    assert r['started_ns'] <= r['finished_ns'] <= r['deadline_ns']
    assert r['work_cutoff_ns']==r['deadline_ns']-800000000
    if r['status']=='COMPLETED':
        assert r['finished_ns']<r['work_cutoff_ns'] and r['cleanup_verified']
    for w in r['workers']:
        events=w['events'];times=[e['monotonic_ns'] for e in events]
        assert times==sorted(times)
        assert events[0]['state']=='CREATED'
        if w['terminal']=='COMPLETED':
            assert w['returncode']==0 and w['state']=='REAPED'
        if w['terminal']=='FORCED_TERMINATION':
            states=[e['state'] for e in events]
            assert states.index('STOP_REQUESTED')<states.index('TERMINATING')<states.index('REAPED')
        if w['terminal']=='NOT_STARTED': assert 'pid' not in w
    # Child checkpoint records the same absolute deadline, including descendants.
    for f in path.parent.rglob('pid.json'):
        info=json.loads(f.read_text())
        assert info['deadline_ns']==r['deadline_ns']
        assert info['started_ns'] < r['deadline_ns']
    records.append(dict(case=path.parent.name,status=r['status'],cause=r['cause'],
                        elapsed_s=(r['finished_ns']-r['started_ns'])/1e9,
                        hard_deadline_margin_s=(r['deadline_ns']-r['finished_ns'])/1e9,
                        cleanup_verified=r['cleanup_verified'],
                        workers=[dict(pid=w.get('pid'),terminal=w['terminal'],returncode=w.get('returncode'),
                                      states=[e['state'] for e in w['events']]) for w in r['workers']]))
assert len(records)==16,len(records) #13 cases + progress failure + queued multiworker + cleanup failure
# Independently inspect all worker and descendant PIDs after the tests.
table=subprocess.check_output(['ps','-axo','pid=,ppid=,pgid=,stat='],text=True)
states={int(line.split()[0]):line.split()[3] for line in table.splitlines()}
pids={json.loads(f.read_text())['pid'] for f in (root/'final_release_trials').rglob('pid.json')}
(root/'process_table.txt').write_text('pid ppid pgid stat (owned fixture PIDs only; absence means gone)\n'+'\n'.join(line for line in table.splitlines() if int(line.split()[0]) in pids)+'\n')
live=[pid for pid in pids if pid in states and not states[pid].startswith('Z')]
assert not live,live
old=json.loads((root.parent/'m005a_1'/'audit.json').read_text())
manifest=json.loads((root.parent/'m005a_1'/'verification_manifest.json').read_text())
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest['files'].items())
prior=subprocess.check_output(['git','ls-tree','-r','--name-only','6077ba50fc05a140fa6bdfc21fe2f6e6a859e7d0'],text=True).splitlines()
previous_hash={**old['historical_hashes'], **manifest['files']}
self_path='reports/evidence/m005a_1/verification_manifest.json'
previous_hash[self_path]=hashlib.sha256(subprocess.check_output(['git','show','6077ba50fc05a140fa6bdfc21fe2f6e6a859e7d0:'+self_path])).hexdigest()
assert set(previous_hash)==set(prior)
changed=[p for p,h in previous_hash.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
assert changed==['src/neuromancer/control_experiment.py'],changed
out=dict(starting_revision='6077ba50fc05a140fa6bdfc21fe2f6e6a859e7d0',
         cases=records, independent_worker_pids=len(pids),live_worker_pids=live,
         zombie_pids=[p for p in pids if p in states and states[p].startswith('Z')],
         prior_tracked_count=len(prior),changed_historical_paths=changed,
         m005a_1_manifest_verified=len(manifest['files']),
         platform=platform.platform(),python=sys.version,
         monotonic_clock=vars(time.get_clock_info('monotonic')),
         source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                       [Path('src/neuromancer/supervisor.py'),Path('src/neuromancer/control_experiment.py'),
                        Path('tests/test_supervisor.py'),Path('tests/supervisor_worker.py')]})
(root/'verification.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'cases':len(records),'live_workers':live,'historical_changes':changed}))
