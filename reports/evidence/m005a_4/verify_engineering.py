"""Read saved engineering evidence independently; never advances neural dynamics."""
from pathlib import Path
import collections, hashlib, json, os, xml.etree.ElementTree as ET
root=Path('reports/evidence/m005a_4')
for f in root.rglob('*'):
    if f.is_symlink():f.unlink() # pytest aliases, not evidence copies
xml=ET.parse(root/'verified_tests.xml')
suites=list(xml.getroot().iter('testsuite'))
assert sum(int(s.attrib.get('failures',0))+int(s.attrib.get('errors',0)) for s in suites)==0
assert sum(int(s.attrib['tests']) for s in suites)==104
records=[]
for f in sorted((root/'verified_trials').rglob('returned.json')):
    d=json.loads(f.read_text());assert d['deadline_clock_id'].startswith('darwin.mach_continuous_time.ns.v1@')
    assert d['status']!='COMPLETED' or (d['cleanup_verified'] and d['finished_ns']<=d['deadline_ns'])
    if d['post_deadline_cleanup']:
        assert d['status']!='COMPLETED'
        if d['cleanup_clock_id']==d['deadline_clock_id']:
            assert d['cleanup_deadline_ns']>d['deadline_ns']
            if d['finished_ns'] is not None:assert d['finished_ns']<=d['cleanup_deadline_ns']
    for w in d['workers']:
        if not w.get('pid'):continue
        assert w['parent_reaped']
        try:os.killpg(w['pgid'],0)
        except ProcessLookupError:pass
        else:raise AssertionError(('live owned group',f,w['pgid']))
    records.append(dict(path=str(f),status=d['status'],cleanup_verified=d['cleanup_verified'],post_deadline_cleanup=d['post_deadline_cleanup']))
assert len(records)==20
preserved=json.loads((root/'preservation.json').read_text())['historical_sha256']
assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in preserved.items())
audit=json.loads((root/'confirmation_verification.json').read_text())
assert audit['complete_trials']==3 and audit['complete_branches']==24
assert all(t['classification']=='REUSABLE' for t in audit['trial_classifications'])
result=dict(status='PASS',engineering_tests=104,neural_tests_executed=0,real_process_records=records,status_counts=dict(collections.Counter(r['status'] for r in records)),preserved_historical_files=len(preserved),physical_sleep_test='NOT_RUN',scientific_acquisition='NONE')
(root/'engineering_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='real_process_records'},indent=2))
