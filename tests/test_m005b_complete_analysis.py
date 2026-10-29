"""Analytical whole-cohort fixture; no neural acquisition or reserved outcome."""
import importlib.util,json,os
from pathlib import Path
import numpy as np
from neuromancer.m005b_analysis import analyze

def test_full_cohort_gates_independently_reconstructed(tmp_path,monkeypatch):
 from neuromancer.supervisor import Deadline
 d=Deadline.after(90);monkeypatch.setenv('NEUROMANCER_DEADLINE_NS',str(d.end_ns));monkeypatch.setenv('NEUROMANCER_DEADLINE_CLOCK',d.clock_id)
 root=tmp_path/'raw';root.mkdir();jobs=[(n,r) for n in range(10) for r in (47,48)];(root/'provenance.json').write_text(json.dumps(dict(phase='primary',jobs=jobs)))
 q=np.zeros(2550)
 for j,dose in enumerate((30,60,90,120)):q[950+400*j:1150+400*j]=dose
 prefixcounts=np.zeros((2550,20),int);prefixcounts[:,0]=16+(q/30).astype(int);prefixu=np.c_[q,np.zeros(2550),q,np.zeros(2550)];c=dict(baseline_hz=10.,noise_hz=0.,slope_hz_per_pA=1/48,feedforward_pA=48.,target_hz=11.,valid=True)
 record=dict(coef=np.zeros((41,4)).tolist(),scale=np.ones(40).tolist(),mean=np.zeros(40).tolist(),output_mean=np.ones(4).tolist());base=tmp_path/'template';base.mkdir();np.savez_compressed(base/'prefix.npz',counts=prefixcounts,delivered=prefixu);np.savez_compressed(base/'initial.npz',history=np.zeros((9,4)));(base/'initial.json').write_text(json.dumps(dict(calibration=c,record=record)))
 branches=[]
 for reg in ('STATIC','LOSS'):
  for kind in ('PI10_5','FIXED-MPC','RLS-MPC','BIAS-MPC','FIXED','ZERO',*(['MAX'] if reg=='LOSS' else [])):
   name=reg+'_'+kind;counts=np.zeros((3200,20),int);counts[:,0]=17 if kind!='MAX' else 20;u=np.tile([48.,0,48.,0],(3200,1));np.savez_compressed(base/(name+'.npz'),counts=counts,delivered=u,frames=np.zeros((3200,8)),pre_prediction=np.zeros((3200,4)),dense_theta=np.zeros((64,41,4)),presented=np.ones(3200,bool));branches.append(dict(name=name,controller=kind,condition=reg,fault=None,safe_bins=0,violations=0,model_failure=None,plans=0))
 for n,r in jobs:
  folder=root/f'n{n}_r{r}';folder.mkdir()
  for p in base.iterdir():os.link(p,folder/p.name)
  (folder/'trial.json').write_text(json.dumps(dict(status='complete',network=n,replicate=r,branches=branches)))
 analysis=tmp_path/'analysis';analyze(root,analysis);s=json.loads((analysis/'summary.json').read_text());assert not s['scientific_pass'] and not s['H1a']['pass_gate'] and not s['H1b']['pass_gate']
 p=Path(__file__).resolve().parents[1]/'reports/evidence/v1_finish/verify_metrics.py';spec=importlib.util.spec_from_file_location('independent_stats',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.verify(root,analysis,tmp_path/'verified.json');assert json.loads((tmp_path/'verified.json').read_text())['status']=='PASS'
