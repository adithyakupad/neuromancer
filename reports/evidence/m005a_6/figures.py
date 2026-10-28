"""Deterministic descriptive figures; never changes scientific gates."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from neuromancer.supervisor import Deadline
r=Path(__file__).resolve().parent;Deadline.from_environment().check();t=list(csv.DictReader((r/'timecourses.csv').open()));n=list(csv.DictReader((r/'network_diagnosis.csv').open()))
plt.rcParams.update({'font.family':'DejaVu Sans','svg.hashsalt':'m005a6','font.size':9})
colors={'PI10_5':'#176b9a','FIXED':'#cc7d23','ZERO':'#777777','MAX':'#9274a7'}
def export(fig,name):fig.savefig(r/f'{name}.png',dpi=140);fig.savefig(r/f'{name}.svg',metadata={'Date':None});plt.close(fig)
def trace(name,cond,key):
 return np.array([[np.mean([float(v[key]) for v in t if int(v['network'])==net and int(v['second'])==sec and v['controller']==name and v['condition']==cond]) for sec in range(32)] for net in range(10)])
fig,ax=plt.subplots(1,2,figsize=(12,4),layout='constrained')
for name in colors:
 a=trace(name,'LOSS','signed_error_hz');ax[0].plot(np.arange(32)+.5,a.mean(0),label=name,color=colors[name])
ax[0].axvline(16,color='black',ls=':');ax[0].axhline(0,color='black',lw=.6);ax[0].axhline(-.2,color='black',ls='--',lw=.6);ax[0].set(xlabel='Virtual control time (s)',ylabel='Observed rate − target (Hz)',title='Loss trajectories: network mean of paired repeats');ax[0].legend()
for key,label in [('pi_pre_bias_hz','Pre 8–16 s'),('pi_immediate_bias_hz','Immediate 16–20 s'),('pi_late_bias_hz','Frozen late 20–32 s'),('pi_final_bias_hz','Final 28–32 s')]:ax[1].plot([int(x['network']) for x in n],[float(x[key]) for x in n],'o-',label=label)
ax[1].axhline(-.2,color='black',ls='--');ax[1].axhline(.2,color='black',ls='--');ax[1].set(xlabel='Development network',ylabel='Signed PI bias (Hz)',title='Finite-horizon bias; final window is descriptive');ax[1].legend(fontsize=7);export(fig,'bias_dynamics')
fig,ax=plt.subplots(1,2,figsize=(12,4),layout='constrained')
for cond,ls in [('LOSS','-'),('STATIC','--')]:
 for key,label in [('desired_q_pA','Desired current'),('integral_pA','Integral')]:
  a=trace('PI10_5',cond,key);ax[0].plot(range(32),a.mean(0),ls=ls,label=cond+' '+label)
ax[0].axvline(16,color='black',ls=':');ax[0].set(xlabel='Virtual control time (s)',ylabel='pA per active channel',title='Recorded decisions; not an optimized controller');ax[0].legend(fontsize=7)
for x in n:
 net=int(x['network']);ax[1].plot([net,net],[float(x['pi_q_peak_pA']),120],color='#bbb');ax[1].plot(net,float(x['pi_q_peak_pA']),'o',color='#176b9a');ax[1].plot(net,120,'_',color='black')
ax[1].set(xlabel='Network',ylabel='pA per active channel',title='Mean replicate peak PI dose versus 120 pA bound');export(fig,'current_integral')
fig,ax=plt.subplots(1,2,figsize=(12,4),layout='constrained')
tr=list(csv.DictReader((r/'trial_diagnosis.csv').open()))
for net in range(10):
 a=[float(v['max_target_margin_hz']) for v in tr if int(v['network'])==net];ax[0].plot([net,net],a,'o-',color='#9274a7')
ax[0].axhline(0,color='black',ls='--');ax[0].set(xlabel='Network',ylabel='MAX observed rate − actual target (Hz)',title='Both original noise repeats; reduced efficacy, 20–32 s')
for sector in range(4):
 loss=trace('PI10_5','LOSS',f'sector{sector}_hz');static=trace('PI10_5','STATIC',f'sector{sector}_hz');ax[1].plot(np.arange(32)+.5,(loss-static).mean(0),label=f'Sector {sector}')
ax[1].axvline(16,color='black',ls=':');ax[1].axhline(0,color='black',lw=.5);ax[1].set(xlabel='Virtual control time (s)',ylabel='Matched LOSS − STATIC rate (Hz)',title='Recorded E sectors; feedback mediation included');ax[1].legend();export(fig,'authority_sectors')
Deadline.from_environment().check()
