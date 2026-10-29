"""Preservation, source, cohort, clock and numerical-evidence reconciliation."""
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
from neuromancer.clocks import clock_domain
from neuromancer.supervisor import Deadline,atomic_json
R=Path('reports/evidence/v1_finish');B=R/'m005b'
def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=Deadline.from_environment();baseline=read(R/'preservation.json')['historical_sha256'];changed=[p for p,h in baseline.items() if not Path(p).exists() or digest(p)!=h];assert not changed
 acquisition=read(B/'primary_launch.json')['source_revision'];scientific=['src/neuromancer/'+p for p in ('_brian.py','substrate.py','observation.py','predictive.py','predictive_planner.py','control.py','calibration.py','tick_execution.py','m005b_study.py','research_codec.py','m005b_analysis.py','clocks.py','supervisor.py')]+['docs/research/011_M005B_CONTROL_PROTOCOL.md']
 hashes={}
 for p in scientific:
  frozen=subprocess.check_output(['git','show',acquisition+':'+p]);assert hashlib.sha256(frozen).hexdigest()==digest(p);hashes[p]=digest(p)
 decision=read(B/'analysis_primary/summary.json');assert (B/'validation').exists()==decision['scientific_pass'] or (not (B/'validation').exists() and decision['scientific_pass'])
 from neuromancer._brian import realization,innovations
 from neuromancer.substrate import Config
 def array_hash(value):
  x=np.ascontiguousarray(value);return hashlib.sha256(str(x.dtype).encode()+str(x.shape).encode()+x.tobytes()).hexdigest()
 phases={};totalbranches=0;seed_checks=[];parameter_hashes={}
 for phase in ('primary','faults','validation'):
  root=B/phase
  if not root.exists():continue
  meta=read(root/'provenance.json');actual={(int(f.name.split('_')[0][1:]),int(f.name.split('_')[1][1:])) for f in root.glob('n*_r*') if f.is_dir()};assert actual==set(map(tuple,meta['jobs'])) and not any(n>=100 for n,r in actual);branches=0
  for n,r in meta['jobs']:
   t=read(root/f'n{n}_r{r}'/'trial.json');assert t['status']=='complete'
   config=Config(**t['engine']['config']);params=realization(config);hashes_now={key:array_hash(value) for key,value in params.items()};assert hashes_now==t['engine']['metadata']['parameter_hashes'];assert not np.any(params['pre']==params['post']);assert len(set(params['stimulation'].ravel()))==200 and len(set(params['recording'].ravel()))==100 and not set(params['stimulation'].ravel())&set(params['recording'].ravel())
   if n in parameter_hashes:assert parameter_hashes[n]==hashes_now
   parameter_hashes[n]=hashes_now;noise,fine=innovations(config,67);sample=dict(fine=fine,effective=array_hash(noise));assert sample==t['branches'][0]['noise']['67'];seed_checks.append(dict(phase=phase,network=n,replicate=r,parameter_hashes=hashes_now,noise_block=67,noise_hashes=sample));del noise,params
   expected=8 if phase=='faults' else 13;assert len(t['branches'])==expected and len({x['name'] for x in t['branches']})==expected;branches+=expected
   if phase!='faults':
    for kind in ('PI10_5','FIXED-MPC','RLS-MPC','BIAS-MPC','FIXED','ZERO'):
     one=np.load(root/f'n{n}_r{r}'/('STATIC_'+kind+'.npz'));two=np.load(root/f'n{n}_r{r}'/('LOSS_'+kind+'.npz'))
     for key in ('counts','delivered','requested','time_us','valid','coverage_us','frames','pre_prediction','state_hashes'):
      assert np.array_equal(one[key][:800],two[key][:800],equal_nan=True),(phase,n,r,kind,key,'pre-loss mismatch')
     if kind in ('FIXED','FIXED-MPC','ZERO'):assert np.array_equal(one['delivered'],two['delivered']),(phase,n,r,kind,'frozen-action mismatch')
     if kind=='ZERO':
      for key in ('counts','event_time_us','event_channel','event_offset','sector','rates'):assert np.array_equal(one[key],two[key],equal_nan=True),(phase,n,r,key,'zero-input gain had neural effect')
   d.check()
  close=read(B/(phase+'_closure.json'));assert close['status']=='COMPLETE' and close['finished_ns']<close['deadline']['end_ns'] and close['deadline']['clock_id']==clock_domain();samples=[json.loads(x) for x in (B/(phase+'_resource.jsonl')).read_text().splitlines()];ns=np.array([x['ns'] for x in samples],dtype=np.int64);gaps=np.diff(ns)/1e9
  phases[phase]=dict(trials=len(actual),branches=branches,wall_s=close['elapsed_s'],peak_live_aggregate_rss_bytes=max(x['aggregate_rss_bytes'] for x in samples),peak_worker_rss_bytes=max([max(x['rss_bytes'].values(),default=0) for x in samples]+[x['completed_peak_rss_bytes'] for x in samples]),maximum_allocated_bytes=max(x['mission_allocated_bytes'] for x in samples),maximum_combined_allocated_bytes=max(x['combined_allocated_bytes'] for x in samples),poll_cadence_s=dict(nominal=1.,p50=float(np.median(gaps)),p95=float(np.quantile(gaps,.95)),maximum=float(gaps.max()),over2s=int((gaps>2).sum())),native_clock_domain=close['deadline']['clock_id']);totalbranches+=branches;d.check()
 assert read(B/'primary_launch.json')['deadline']==read(B/'faults_launch.json')['deadline'];allhashes={str(p):digest(p) for p in B.rglob('*') if p.is_file() and p.name not in ('final_integrity.json',) and not any('supervision' in part for part in p.relative_to(B).parts) and not p.name.startswith('final_qualification')};d.check();atomic_json(B/'final_integrity.json',dict(status='PASS',historical_files_unchanged=len(baseline),historical_changed=changed,acquisition_source=acquisition,scientific_source_hashes=hashes,phases=phases,complete_branches=totalbranches,seed_regeneration_checks=seed_checks,pre_loss_equality_all_primary_arms=True,zero_input_gain_negative_control_exact=True,frozen_reference_actions_gain_blind=True,locked_networks_opened=False,no_scientific_retuning=True,hash_scope='Immutable numerical/configuration/analysis artifacts present at this audit; live supervision and final_qualification lifecycle files excluded, preserved by final Git commit.',data_sha256=allhashes));d.check()
if __name__=='__main__':main()
