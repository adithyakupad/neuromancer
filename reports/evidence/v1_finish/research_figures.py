"""Fixed descriptive figures and computational diagnostics, no endpoint selection."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from neuromancer.supervisor import Deadline,atomic_json

KINDS=('PI10_5','FIXED-MPC','RLS-MPC','BIAS-MPC','FIXED','ZERO')
def loadcsv(p):return list(csv.DictReader(Path(p).open()))
def run(root,analysis,out):
 root=Path(root);analysis=Path(analysis);out=Path(out);out.mkdir(exist_ok=False);d=Deadline.from_environment();meta=json.loads((root/'provenance.json').read_text());ts=loadcsv(analysis/'timecourses.csv');metrics=loadcsv(analysis/'trial_metrics.csv');nets=sorted({int(r['network']) for r in ts});colors=dict(zip(KINDS,plt.get_cmap('tab10').colors));plt.rcParams.update({'font.size':9,'figure.dpi':120,'svg.hashsalt':'NEUROMANCER-M005B-V1'})
 def pernet(reg,kind,key,absolute=False):
  return np.array([[np.mean([(abs(float(r[key])) if absolute else float(r[key])) for r in ts if int(r['network'])==n and r['condition']==reg and r['controller']==kind and int(r['second'])==s]) for s in range(64)] for n in nets])
 fig,axes=plt.subplots(2,2,figsize=(11,7))
 for col,reg in enumerate(('STATIC','LOSS')):
  for kind in KINDS:
   v=pernet(reg,kind,'error_hz');axes[0,col].plot(np.arange(64)+.5,v.mean(0),label=kind,color=colors[kind]);axes[1,col].plot(np.arange(16,64)+1,np.cumsum(pernet(reg,kind,'error_hz',True)[:,16:],axis=1).mean(0),label=kind,color=colors[kind])
  axes[0,col].axhline(0,color='black',lw=.7);axes[0,col].axhspan(-.2,.2,color='gray',alpha=.1);axes[0,col].set(title=reg,ylabel='Signed rate error (Hz)',xlabel='Control time (s)');axes[1,col].set(ylabel='Network-mean cumulative |error| (Hz s)',xlabel='Control time (s)')
  if reg=='LOSS':
   for ax in axes[:,col]:ax.axvline(16,color='black',ls='--',lw=.8)
 axes[0,0].legend(ncol=2,fontsize=7);fig.suptitle('M005B development: repeat-average within network, then network mean');fig.tight_layout();fig.savefig(out/'tracking_and_cumulative.png');fig.savefig(out/'tracking_and_cumulative.svg',metadata={'Date':None});plt.close(fig)
 fig,axes=plt.subplots(1,2,figsize=(11,4))
 for kind in KINDS:
  val=[np.mean([float(r['post_iae_hz_s']) for r in metrics if int(r['network'])==n and r['condition']=='LOSS' and r['controller']==kind]) for n in nets];dose=[np.mean([float(r['post_exposure_pA_s']) for r in metrics if int(r['network'])==n and r['condition']=='LOSS' and r['controller']==kind]) for n in nets];axes[0].plot(nets,val,'o-',label=kind,color=colors[kind],lw=.7);axes[1].scatter(dose,val,label=kind,color=colors[kind],s=18)
 axes[0].set(xlabel='Independent network',ylabel='Post-loss IAE (Hz s)');axes[1].set(xlabel='Post-loss current exposure (pA s)',ylabel='Post-loss IAE (Hz s)');axes[0].legend(fontsize=7,ncol=2);fig.tight_layout();fig.savefig(out/'network_and_cost.png');fig.savefig(out/'network_and_cost.svg',metadata={'Date':None});plt.close(fig)
 computational={};failures=[];sectors=[]
 for n,rep in meta['jobs']:
  folder=root/f'n{n}_r{rep}';trial=json.loads((folder/'trial.json').read_text())
  for branch in trial['branches']:
   a=np.load(folder/(branch['name']+'.npz'));key=branch['controller'];item=computational.setdefault(key,dict(command_ns=[],update_ns=[],planner_ns=[],branch_wall_s=[],peak_rss_bytes=[],fallback_bins=0,model_failures=0));item['command_ns'].extend(a['command_ns'].tolist());item['update_ns'].extend(a['update_ns'].tolist());item['branch_wall_s'].append(branch['wall_s']);item['peak_rss_bytes'].append(trial['peak_rss_bytes']);item['fallback_bins']+=branch['safe_bins'];item['model_failures']+=bool(branch['model_failure'])
   for j in range(branch['plans']):item['planner_ns'].append(float(np.load(folder/f'{branch["name"]}_plan_{j:02}.npz')['elapsed_ns']))
   if branch['model_failure']:failures.append(dict(network=n,replicate=rep,branch=branch['name'],failure=branch['model_failure']))
   raw=a['counts'].reshape(64,50,4,5)[:,:,:,:4].sum((1,3))/20;sectors.append(dict(network=n,replicate=rep,condition=branch['condition'],controller=key,post_sector_rates_hz=raw[16:].mean(0).tolist(),late_sector_rates_hz=raw[48:].mean(0).tolist()))
  d.check()
 for kind,item in computational.items():
  for name in ('command_ns','update_ns','planner_ns'):
   x=np.array(item.pop(name),float)/1e6;item[name.replace('_ns','_ms')]=dict(count=len(x),p50=float(np.median(x)),p95=float(np.quantile(x,.95)),p99=float(np.quantile(x,.99)),maximum=float(x.max()),over250ms=int((x>=250).sum())) if len(x) else None
  item['peak_rss_bytes']=max(item['peak_rss_bytes']);item['branch_wall_s']=dict(total=sum(item['branch_wall_s']),minimum=min(item['branch_wall_s']),maximum=max(item['branch_wall_s']))
 atomic_json(out/'computation.json',dict(controllers=computational,failures=failures,hard_real_time_qualified=False));atomic_json(out/'sectors.json',sectors);d.check()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('analysis');p.add_argument('out');a=p.parse_args();run(a.root,a.analysis,a.out)
