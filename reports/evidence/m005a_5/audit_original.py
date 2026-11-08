"""Independent audit of an INTERRUPTED cohort; no cohort gates or success inference."""
import argparse
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import numpy as np


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root;raw=root/'confirmation';began=time.monotonic_ns()
    donor=Path('reports/evidence/m005a');v=load('independent_m005a',donor/'verify.py');analysis=load('frozen_m005a_analysis',donor/'analyze.py')
    terminal=json.loads((raw/'supervision/terminal.json').read_text());meta=json.loads((raw/'provenance.json').read_text())
    assert terminal['status']=='SUPERVISOR_FAILURE' and terminal['error']=='KeyboardInterrupt()' and terminal['cleanup_verified']
    assert not (raw/'summary.json').exists()
    states={s:sum(w['terminal']==s for w in terminal['workers']) for s in ('COMPLETED','FORCED_TERMINATION','NOT_STARTED')}
    assert states==dict(COMPLETED=3,FORCED_TERMINATION=3,NOT_STARTED=14)
    owned=[w['pid'] for w in terminal['workers'] if w.get('pid')]
    for pid in owned:
        try:os.killpg(pid,0)
        except ProcessLookupError:pass
        else:raise AssertionError(f'Owned process group still exists: {pid}')
    table=subprocess.check_output(['ps','-axo','pid=,stat='],text=True);present={int(line.split()[0]) for line in table.splitlines()}
    assert not set(owned)&present
    stop=json.loads((root/'clock_stop.json').read_text());first_stop=min(e['monotonic_ns'] for w in terminal['workers'] for e in w['events'] if e['state']=='STOP_REQUESTED')
    assert terminal['finished_ns']<meta['deadline_monotonic_ns']
    cleanup_s=(terminal['finished_ns']-first_stop)/1e9
    assert cleanup_s<.8
    assert terminal['cause']=='SUPERVISOR_FAILURE'
    from neuromancer._brian import realization,digest,innovations
    from neuromancer.substrate import Config
    rows=[];traces=[];designs=[];observed=[];scores={};noise_manifest=[]
    for folder in sorted(raw.glob('n*_r*')):
        trial_file=folder/'trial.json'
        if not trial_file.exists():
            observed.append(dict(folder=folder.name,status='aborted_in_flight',published_files=[f.name for f in folder.iterdir() if f.is_file()]))
            continue
        m=json.loads(trial_file.read_text());n,r=m['network_id'],m['replicate_id']
        assert (n,r) in ((0,41),(0,42),(1,41)) and m['status']=='complete'
        assert m['peak_rss_bytes']<2*1024**3
        cfg=Config(network_id=n,replicate_id=r);params=realization(cfg)
        assert {k:digest(value) for k,value in params.items()}==m['engine']['metadata']['parameter_hashes']
        old=json.loads((donor/f'results/tune/n{n}_r40/trial.json').read_text())
        assert old['engine']['metadata']['parameter_hashes']==m['engine']['metadata']['parameter_hashes']
        assert not np.intersect1d(params['recording'],params['stimulation']).size
        prefix,baseline=v.inspect_public(folder/'prefix.npz',0,2550);c=m['calibration'];v.calibration(prefix,baseline,c)
        cached={};common=None
        for branch in m['branches']:
            cond,name=branch['condition'],branch['controller'];d,y=v.inspect_public(folder/f'{cond}_{name}.npz',51000000,1600,prefix['rates'][-1]);v.policy_replay(d,y,c,name)
            assert branch['audit']['violations']==0
            v.close(d['delivered'].sum()*.02,branch['audit']['exposure_pA_s'])
            assert len(branch['noise'])==83
            if common is None:
                common=branch['noise']
                for block in (0,50,51,66,67,82):
                    effective,fine=innovations(cfg,block);assert common[str(block)]==dict(fine=fine,effective=digest(effective))
            else:assert common==branch['noise']
            cached[cond,name]=d
            for window,(lo,hi) in {'full':(0,32),'stationary':(8,32),'pre':(8,16),'immediate':(16,20),'late':(20,32)}.items():
                scores[n,r,cond,name,window]=(*v.score(y,c['target_hz'],lo,hi),float(d['delivered'].sum()*.02))
        for name in meta['names']:
            x,z=cached['STATIC',name],cached['LOSS',name]
            for field in ('counts','rates','sector','delivered','decisions','intent'):
                v.close(x[field][:(17 if field=='decisions' else 800)],z[field][:(17 if field=='decisions' else 800)])
        for field in ('counts','rates','sector','delivered','intent'):
            v.close(cached['STATIC','ZERO'][field],cached['LOSS','ZERO'][field])
        rr,tt,dd=analysis.trial_rows(folder);rows+=rr;traces+=tt;designs+=dd
        observed.append(dict(folder=folder.name,status='complete',branches=len(m['branches']),calibration=c,
                             peak_rss_bytes=m['peak_rss_bytes']))
        noise_manifest.append(dict(network=n,replicate=r,root_seed=20261018,parameter_hashes=m['engine']['metadata']['parameter_hashes'],noise_block_hashes=common,checkpoint=m['checkpoint']))
    assert len(scores)==120 and len(rows)==120
    for row in rows:
        key=(row['network'],row['replicate'],row['condition'],row['controller'],row['window']);expected=scores[key]
        v.close(expected[:4],[row[k] for k in ('mae_hz','bias_hz','rmse_hz','rate_hz')]);v.close(expected[4],row['online_exposure_pA_s'])
    analysis.csvout(Path('reports/evidence/m005a_5')/'partial_descriptive_metrics.csv',rows);analysis.csvout(Path('reports/evidence/m005a_5')/'partial_descriptive_traces.csv',traces)
    (Path('reports/evidence/m005a_5')/'partial_excitation.json').write_text(json.dumps(designs,indent=2)+'\n')
    (Path('reports/evidence/m005a_5')/'actual_seed_manifest.json').write_text(json.dumps(dict(status='INCOMPLETE_COHORT',complete_trials=noise_manifest,planned_all_networks=list(range(10)),planned_noise=[41,42],aborted_pairs=[[1,42],[2,41],[2,42]],unstarted_pairs=[[n,r] for n in range(3,10) for r in (41,42)]),indent=2)+'\n')
    preservation=json.loads(Path('reports/evidence/m005a_5/preservation.json').read_text())['historical_sha256']
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in preservation.items())
    freeze=json.loads((root/'selection_freeze.json').read_text());selection=root/'tuning_analysis/selection.json'
    assert hashlib.sha256(selection.read_bytes()).hexdigest()==freeze['selection_sha256']==meta['selection_sha256']
    launch=json.loads((root/'acquisition_launch.json').read_text());assert launch['head']==meta['head']=='604302e9eecc491b8855a6ccbcaf4e195cb2adb2'
    assert subprocess.check_output(['git','show',launch['head']+':reports/evidence/m005a_3/tuning_analysis/selection.json'])==selection.read_bytes()
    original_source={key:hashlib.sha256(subprocess.check_output(['git','show',meta['head']+':src/'+key])).hexdigest() for key in meta['source_hashes']}
    assert original_source==meta['source_hashes']
    immutable=json.loads(Path('reports/evidence/m005a_3/verification_manifest.json').read_text())['inventory']
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in immutable.items())
    classifications=[dict(network_id=n,replicate_id=r,classification='REUSABLE',basis='Complete markers, source Git hashes,27 archive hashes, all spike counts/timing/actions/seeds/120 numerical rows pass; all unfavorable outcomes retained',eligibility='Requires a prospective continuation amendment; original resource stop remains PARTIAL') for n,r in ((0,41),(0,42),(1,41))]
    result=dict(trial_classifications=classifications,technical_verification='PASS_AVAILABLE_RECORDS_ONLY',mission_execution='PARTIAL',scientific='NOT_ESTABLISHED',m005b='HOLD',source_revision=meta['head'],selected_controller='PI10_5',states=states,
        complete_trials=3,complete_prefixes=3,complete_branches=24,completed_simulated_seconds=921,missing_trials=17,missing_branches=136,available_metric_rows=120,
        unflushed_inflight_activity='unknown; no complete prefix/branch published for aborted workers',published_abort_inventory=observed,
        supervisor_cleanup_s=cleanup_s,owned_groups=owned,live_owned_groups=[],original_deadline_exceeded=False,clock_discrepancy_s=json.loads((root/'clock_investigation.json').read_text())['difference_s'],
        historical_files_unchanged=len(preservation),all_full_cohort_scientific_gates='NOT_EVALUABLE; no subset gate or network CI substituted',
        verifier_wall_s=(time.monotonic_ns()-began)/1e9)
    (Path('reports/evidence/m005a_5')/'historical_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('technical_verification','complete_trials','complete_branches','supervisor_cleanup_s','live_owned_groups')}))


if __name__=='__main__':main()
