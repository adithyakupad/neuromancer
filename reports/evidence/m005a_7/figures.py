"""Fixed deterministic extended-horizon plots; no gate selection."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from neuromancer.supervisor import Deadline
p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);a=p.parse_args();Deadline.from_environment().check()
rows=list(csv.DictReader((a.analysis/'traces.csv').open()));moving=list(csv.DictReader((a.analysis/'moving8.csv').open()));gates=list(csv.DictReader((a.analysis/'network_qualification.csv').open()));summary=json.loads((a.analysis/'summary.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','svg.hashsalt':'m005a7','font.size':9})
def export(fig,name):fig.savefig(a.analysis/f'{name}.png',dpi=140);fig.savefig(a.analysis/f'{name}.svg',metadata={'Date':None});plt.close(fig)
fig,axes=plt.subplots(5,2,figsize=(12,13),layout='constrained')
for n,ax in enumerate(axes.flat):
 for name,color in [('PI10_5','#176b9a'),('FIXED','#cd7c25'),('MAX','#9071a8')]:
  v=[r for r in rows if int(r['network'])==n and r['condition']=='LOSS' and r['controller']==name];y=[np.mean([float(r['error_hz']) for r in v if int(r['second'])==s]) for s in range(64)];ax.plot(np.arange(64)+.5,y,color=color,label=name,lw=.8)
 ax.axvline(16,color='black',ls=':',lw=.8);ax.axhline(0,color='black',lw=.6);ax.axhspan(-.2,.2,color='#d7e8dc',alpha=.5);ax.axvspan(48,64,color='#aaa',alpha=.12);ax.set(title=f'Development network {n}',xlabel='Virtual control time (s)',ylabel='Raw1s rate − target (Hz)')
axes.flat[0].legend(fontsize=7);fig.suptitle('Fresh noise45/46 means; fixed extended window chosen prospectively');export(fig,'loss_timecourses')
fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
for ax,cond in zip(axes,('STATIC','LOSS')):
 for name,color in [('PI10_5','#176b9a'),('FIXED','#cd7c25')]:
  model=summary['models'][cond+'_'+name]['late'];ax.plot(range(10),model['bias_hz']['network_values'],'o-',label=name,color=color)
 ax.axhline(.2,color='black',ls='--');ax.axhline(-.2,color='black',ls='--');ax.axhline(0,color='black',lw=.6);ax.set(title=cond+' late signed bias48–64s',xlabel='Network',ylabel='Hz');ax.legend()
export(fig,'network_bias')
fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
for cond,style in [('STATIC','--'),('LOSS','-')]:
 for key,label in [('q_pA','Desired q'),('integral_pA','Integral')]:
  v=[r for r in rows if r['condition']==cond and r['controller']=='PI10_5'];y=[np.mean([float(r[key]) for r in v if int(r['second'])==s]) for s in range(64)];axes[0].plot(range(64),y,ls=style,label=cond+' '+label)
axes[0].axvline(16,color='black',ls=':');axes[0].set(xlabel='Virtual control time (s)',ylabel='pA per active channel',title='Same policy continues through32s');axes[0].legend(fontsize=7)
for name,color in [('PI10_5','#176b9a'),('FIXED','#cd7c25')]:
 v=[r for r in moving if r['condition']=='LOSS' and r['controller']==name];y=[np.mean([float(r['bias_hz']) for r in v if int(r['end_second'])==s]) for s in range(8,65)];axes[1].plot(range(8,65),y,label=name,color=color)
axes[1].axhline(-.2,color='black',ls='--');axes[1].axhline(.2,color='black',ls='--');axes[1].axvspan(48,64,color='#aaa',alpha=.15);axes[1].set(xlabel='Completed window endpoint (s)',ylabel='Trailing8s signed bias (Hz)',title='Descriptive moving window, not selected endpoint');axes[1].legend();export(fig,'current_moving_bias')
Deadline.from_environment().check()
