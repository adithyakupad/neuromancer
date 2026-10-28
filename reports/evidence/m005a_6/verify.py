"""Independent scalar/loop reconstruction; does not import diagnostic producer."""
import csv,json,math
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline
r=Path(__file__).resolve().parent;raw=Path('reports/evidence/m005a_5/confirmation');Deadline.from_environment().check()
def rows(name):return list(csv.DictReader((r/name).open()))
def close(a,b):np.testing.assert_allclose(float(a),float(b),rtol=1e-11,atol=2e-11)
W={'pre':(8,16),'immediate':(16,20),'late':(20,32),'final':(28,32)}
time=rows('timecourses.csv');win=rows('windows.csv');tr=rows('trial_diagnosis.csv');net=rows('network_diagnosis.csv');eff=rows('matched_effects.csv')
assert (len(time),len(win),len(tr),len(net),len(eff))==(5120,640,20,10,2560)
time_index={(int(x['network']),int(x['replicate']),x['condition'],x['controller'],int(x['second'])):x for x in time};window_index={(int(x['network']),int(x['replicate']),x['condition'],x['controller'],x['window']):x for x in win}
old=list(csv.DictReader(open('reports/evidence/m005a_5/confirmation_analysis/metrics.csv')));all_stats={};branches=0
for folder in raw.glob('n*_r*'):
 m=json.loads((folder/'trial.json').read_text());n,k=m['network_id'],m['replicate_id'];target=m['calibration']['target_hz'];cal=m['calibration'];base=np.load(folder/'prefix.npz')['counts'];bs=[sum(int(base[t,ch]) for t in range(350,750) for ch in range(5*j,5*j+4))/160 for j in range(4)];cached={}
 for b in m['branches']:
  c,name=b['condition'],b['controller'];d=dict(np.load(folder/f'{c}_{name}.npz'));u=d['delivered'];de=d['decisions'];sector=np.zeros((32,4))
  for sec in range(32):
   for j in range(4):sector[sec,j]=sum(int(d['counts'][t,ch]) for t in range(sec*50,(sec+1)*50) for ch in range(j*5,j*5+4))/20
  y=sector.sum(1)/4;cached[c,name]=(y,d);branches+=1
  for sec in range(32):
   v=time_index[n,k,c,name,sec];close(v['rate_hz'],y[sec]);close(v['signed_error_hz'],y[sec]-target);close(v['available_us'],52000000+sec*1000000)
   close(v['target_hz'],target)
   if sec:close(v['controller_previous_error_hz'],target-y[sec-1])
   close(v['desired_q_pA'],de[sec,1]);close(v['integral_pA'],de[sec,2]);close(v['blocked'],de[sec,4]);close(v['clipped'],de[sec,5])
   for j in range(4):close(v[f'sector{j}_hz'],sector[sec,j]);close(v[f'sector{j}_above_baseline_hz'],sector[sec,j]-bs[j]);close(v[f'u{j}_pA'],sum(u[t,j] for t in range(sec*50,(sec+1)*50))/50)
   close(v['total_pA'],sum(float(v[f'u{j}_pA']) for j in range(4)))
  for w,(a,z) in W.items():
   v=window_index[n,k,c,name,w];error=[float(y[t])-target for t in range(a,z)];close(v['bias_hz'],sum(error)/(z-a));close(v['mae_hz'],sum(abs(e) for e in error)/(z-a));close(v['rate_hz'],sum(y[a:z])/(z-a));close(v['target_hz'],target)
   sub=u[a*50:z*50];close(v['total_mean_pA'],sub.sum()/(50*(z-a)));close(v['exposure_pA_s'],.02*sub.sum());close(v['dose_min_pA'],min(sub[:,0]));close(v['dose_max_pA'],max(sub[:,0]));close(v['dose_zero_fraction'],sum(x==0 for x in sub[:,0])/len(sub));close(v['dose_max_fraction'],sum(x==120 for x in sub[:,0])/len(sub));close(v['budget_fraction'],sum(sum(x)==240 for x in sub)/len(sub));close(v['antiwindup_count'],sum(de[a:z,4]));close(v['decision_clip_count'],sum(de[a:z,5]));close(v['integral_mean_pA'],sum(de[a:z,2])/(z-a))
   for j in range(4):close(v[f'sector{j}_hz'],sum(sector[a:z,j])/(z-a));close(v[f'sector{j}_above_baseline_hz'],sum(sector[a:z,j])/(z-a)-bs[j]);close(v[f'u{j}_pA'],sub[:,j].sum()/len(sub))
   if w!='final':
    prior=next(o for o in old if (int(o['network']),int(o['replicate']),o['condition'],o['controller'],o['window'])==(n,k,c,name,w));close(v['bias_hz'],prior['bias_hz']);close(v['mae_hz'],prior['mae_hz'])
  if name=='PI10_5':
   history=np.vstack((de,d['terminal']));I=0.;clamps=blocked=clipped=0
   for sec in range(32):
    error=target-y[sec];candidate=I+5*error;clamps+=abs(candidate)>120;trial=min(120,max(-120,candidate));proposed=cal['feedforward_pA']+10*error+trial;block=(proposed>120 and error>0) or (proposed<0 and error<0)
    if not block:I=trial
    qraw=cal['feedforward_pA']+10*error+I;q=min(120,max(0,qraw));nxt=history[sec+1];close(nxt[1],q);close(nxt[2],I);close(nxt[3],error);close(nxt[4],block);close(nxt[5],qraw!=q);blocked+=block;clipped+=(qraw!=q)
   if c=='LOSS':pi_counters=(clamps,blocked,clipped)
 # Every matched contrast reconstructed independently.
 for name in ('ZERO','FIXED','MAX','PI10_5'):
  yl,dl=cached['LOSS',name];ys,ds=cached['STATIC',name];np.testing.assert_array_equal(dl['counts'][:800],ds['counts'][:800]);np.testing.assert_array_equal(dl['delivered'][:800],ds['delivered'][:800])
  er=[v for v in eff if int(v['network'])==n and int(v['replicate'])==k and v['controller']==name];assert len(er)==32
  for v in er:
   sec=int(v['second']);close(v['loss_minus_static_hz'],yl[sec]-ys[sec]);close(v['loss_minus_zero_hz'],yl[sec]-cached['LOSS','ZERO'][0][sec]);close(v['static_minus_zero_hz'],ys[sec]-cached['STATIC','ZERO'][0][sec])
 t=next(v for v in tr if (int(v['network']),int(v['replicate']))==(n,k));y,d=cached['LOSS','PI10_5'];de=d['decisions'];term=d['terminal'];margin=float(np.mean(cached['LOSS','MAX'][0][20:]-target));zero=float(np.mean(cached['LOSS','ZERO'][0][20:]-target))
 close(t['max_target_margin_hz'],margin);close(t['zero_target_margin_hz'],zero);assert (t['bracket']=='True')==(zero<0<margin)
 for w in W:close(t[f'pi_{w}_bias_hz'],np.mean(y[slice(*W[w])]-target))
 for idx in (16,17,20,31):close(t[f'q{idx}_pA'],de[idx,1]);close(t[f'I{idx}_pA'],de[idx,2])
 close(t['pi_dose_bound_ticks'],sum((q==0 or q==120) for q in d['delivered'][:,0]))
 for label,source in [('target_hz','target_hz'),('baseline_hz','baseline_hz'),('noise_hz','noise_hz'),('slope_hz_per_pA','slope_hz_per_pA'),('qff_pA','feedforward_pA')]:close(t[label],cal[source])
 close(t['q32_unused_pA'],term[1]);close(t['I32_pA'],term[2]);close(t['gain_scaled_reference_pA'],cal['feedforward_pA']/.6);close(t['pi_q_peak_pA'],max(d['delivered'][:,0]));close(t['integral_post_delta_pA'],term[2]-de[16,2]);close(t['post_error_integral_pA'],5*sum(target-y[16:]));close(t['late_error_integral_pA'],5*sum(target-y[20:]));close(t['late_integral_delta_pA'],term[2]-de[20,2]);close(t['integral_clamp_attempts'],pi_counters[0]);close(t['blocked_including_terminal'],pi_counters[1]);close(t['clipped_including_terminal'],pi_counters[2])
 all_stats[n,k]=t
assert branches==160
# All network columns that are simple repeat means and all classifications.
original=list(csv.DictReader(open('reports/evidence/m005a_5/confirmation_analysis/network_qualification.csv')))
for v in net:
 n=int(v['network']);ts=[all_stats[n,k] for k in (41,42)]
 for key in tr[0]:
  if key not in ('network','replicate','bracket','max_target_margin_hz'):close(v[key],np.mean([float(t[key]) for t in ts]))
 bracket=all(t['bracket']=='True' for t in ts);failed=next(o for o in original if int(o['network'])==n and o['condition']=='LOSS')['qualified']=='False';assert v['classification']==('A' if failed and bracket else 'C' if failed else 'PASS_NO_FAILURE')
 close(v['min_max_target_margin_hz'],min(float(t['max_target_margin_hz']) for t in ts));close(v['mean_max_target_margin_hz'],np.mean([float(t['max_target_margin_hz']) for t in ts]))
 for cond in ('STATIC','LOSS'):
  for name in ('ZERO','FIXED','MAX','PI10_5'):
   for w in W:
    for key in ('bias_hz','mae_hz','total_mean_pA','integral_mean_pA'):close(v[f'{cond}_{name}_{w}_{key}'],np.mean([float(window_index[n,k,cond,name,w][key]) for k in (41,42)]))
 close(v['pi_loss_mae_benefit_hz'],float(v['LOSS_FIXED_late_mae_hz'])-float(v['LOSS_PI10_5_late_mae_hz']));close(v['pi_bias_improvement_final_vs_immediate_hz'],float(v['pi_final_bias_hz'])-float(v['pi_immediate_bias_hz']))
s=json.loads((r/'summary.json').read_text())
for key,stat in s['stats'].items():
 vals=np.array([float(next(v for v in net if int(v['network'])==n)[key]) for n in range(10)]);g=np.random.Generator(np.random.PCG64(20261025));q=np.quantile(vals[g.integers(0,10,(10000,10))].mean(1),[.025,.975]);np.testing.assert_allclose(stat['ci95'],q,atol=2e-12);close(stat['mean'],vals.mean())
for key,v in s['classifications'].items():
 count=sum(x['classification']==key for x in net);assert v['count']==count;close(v['fraction'],count/10);z=1.95996398454;p=count/10;den=1+z*z/10;cen=(p+z*z/20)/den;half=z*math.sqrt(p*(1-p)/10+z*z/400)/den;np.testing.assert_allclose(v['wilson95'],[max(0,cen-half),min(1,cen+half)],atol=1e-12)
for key,v in s['correlations'].items():
 x=np.array([float(z[key]) for z in net]);y=np.array([float(z['pi_late_bias_hz']) for z in net])
 def pearson(a,b):
  a=a-a.mean();b=b-b.mean();return float(np.dot(a,b)/np.sqrt(np.dot(a,a)*np.dot(b,b)))
 def ranks(a):
  order=sorted(set(a));mapping={value:np.mean([i for i,b in enumerate(sorted(a)) if b==value]) for value in order};return np.array([mapping[b] for b in a])
 close(v['pearson'],pearson(x,y));close(v['spearman'],pearson(ranks(x),ranks(y)))
assert s['failed_networks']==[int(v['network']) for v in net if v['loss_failed']=='True']
close(s['A_conditional_failed'],sum(v['classification']=='A' for v in net)/sum(v['loss_failed']=='True' for v in net))
for output,key in [('pi_bound_ticks','pi_dose_bound_ticks'),('clipped','clipped_including_terminal'),('blocked','blocked_including_terminal'),('integral_clamp_attempts','integral_clamp_attempts')]:close(s[output],sum(float(v[key]) for v in tr))
# Independent existing excitation reference, itself reconstructed in M005A.5.
a=json.loads((r/'excitation.json').read_text());b=json.load(open('reports/evidence/m005a_5/confirmation_analysis/excitation.json'));assert len(a)==len(b)==320
for v in a:
 prior=next(o for o in b if all(o[k]==v[k] for k in ('network','replicate','condition','controller','window')));assert v['rank']==prior['rank'];np.testing.assert_allclose(v['singular_values'],prior['singular_values'],atol=1e-11,rtol=1e-10);close(v['positive_condition'],prior['positive_condition'])
(r/'verification.json').write_text(json.dumps(dict(status='PASS',windows=640,one_second_rows=5120,matched_contrasts=2560,trials=20,branches=160,networks=10,excitation_designs=320,updates_reconstructed=1280,method='Independent spike-count loops, scalar PI recurrence, network aggregation/bootstrap and immutable excitation reference; no producer import'),indent=2)+'\n');Deadline.from_environment().check()
