"""Bind unchanged numerical gates to full execution/lineage/fallback requirements."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root
raw=root/'confirmation';analysis=root/'confirmation_analysis'
summary=json.loads((analysis/'summary.json').read_text())
resource=json.loads((root/'resource_verification.json').read_text());assert resource['status']=='PASS'
verification=json.loads((root/'confirmation_verification.json').read_text());assert verification['status']=='PASS'
replay=json.loads((root/'replay_fixture/verification.json').read_text());assert replay['status']=='PASS'
causal=json.loads((root/'causality_verification.json').read_text());assert causal['status']=='PASS'
repeat=json.loads((root/'repeat_verification.json').read_text());assert repeat['status']=='PASS'
tests=ET.parse(root/'final_tests.xml').getroot()
suites=list(tests.iter('testsuite'));test_count=sum(int(s.attrib['tests']) for s in suites)
assert test_count==125 and all(int(s.attrib.get('failures',0))==0 and int(s.attrib.get('errors',0))==0 for s in suites)
selected=json.loads((root/'selection_freeze.json').read_text())
launch=json.loads((root/'acquisition_launch.json').read_text())
assert subprocess.check_output(['git','show',launch['head']+':reports/evidence/m005a_3/tuning_analysis/selection.json'])==(root/'tuning_analysis/selection.json').read_bytes()
assert launch['selection_sha256']==selected['selection_sha256']
meta=json.loads((raw/'provenance.json').read_text());assert meta['head']==launch['head']
assert meta['protocol_sha256']==selected['original_protocol_sha256']
for folder in raw.glob('n*_r*'):
    trial=json.loads((folder/'trial.json').read_text());n=trial['network_id']
    old=json.loads((Path('reports/evidence/m005a/results/tune')/f'n{n}_r40/trial.json').read_text())
    assert trial['engine']['metadata']['parameter_hashes']==old['engine']['metadata']['parameter_hashes']
rows=list(csv.DictReader((analysis/'metrics.csv').open()))
base=[r for r in rows if r['window']=='full']
assert len(base)==160
fallbacks=sum(int(r['fallback_decisions']) for r in base)
# Full scientific acceptance additionally requires no base-case fallback,
# as explicitly frozen in protocol009, beyond >=8/10 per-regime components.
stationary=bool(summary['stationary_pass'] and fallbacks==0)
recovery=bool(summary['recovery_pass'] and fallbacks==0)
replicate=[]
for r in (41,42):
    for n in range(10):
        for condition,window in [('STATIC','stationary'),('LOSS','late')]:
            def get(name,key,win=window):
                matches=[v for v in rows if int(v['network'])==n and int(v['replicate'])==r and v['condition']==condition and v['window']==win and v['controller']==name]
                assert len(matches)==1
                return float(matches[0][key])
            replicate.append(dict(network=n,replicate=r,condition=condition,
                                  pi_mae_hz=get(summary['selected'],'mae_hz'),pi_bias_hz=get(summary['selected'],'bias_hz'),
                                  fixed_mae_hz=get('FIXED','mae_hz'),zero_mae_hz=get('ZERO','mae_hz'),
                                  authority_hz=get('MAX','rate_hz','late')-get('ZERO','rate_hz','late'),
                                  target_hz=get('ZERO','target_hz'),baseline_hz=get('ZERO','baseline_hz'),noise_hz=get('ZERO','noise_hz')))
with (root/'per_replicate_errors.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=list(replicate[0]));writer.writeheader();writer.writerows(replicate)
result=dict(execution='PASS',scientific='PASS' if stationary and recovery else 'FAIL',
    stationary='PASS' if stationary else 'FAIL',recovery='PASS' if recovery else 'FAIL',
    m005b='READY' if stationary and recovery else 'HOLD',
    selected_controller=summary['selected'],selection_revision=launch['head'],
    completed_trials=20,completed_branches=160,base_fallback_decisions=fallbacks,tests_passed=test_count,
    final_verification_supervisor_completion_required=True,
    old_m005a_execution='PARTIAL_RESOURCE_FAILURE_UNCHANGED',
    parameter_hashes_match_historical_networks=True,
    model_source_hashes=meta['source_hashes'])
(root/'decision.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
