"""Deterministic descriptive control figures from frozen score tables."""
import argparse,csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import numpy as np


def main():
    p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('raw',type=Path);a=p.parse_args()
    s=json.loads((a.analysis/'summary.json').read_text());pi=s['selected']
    rows=list(csv.DictReader((a.analysis/'traces.csv').open()))
    colors={'ZERO':'#666666','FIXED':'#d68420',pi:'#146ba4','MAX':'#a56ba8'}
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.hashsalt':'m005a-control','font.size':9})
    def export(fig,name):
        fig.savefig(a.analysis/f'{name}.png',dpi=140);fig.savefig(a.analysis/f'{name}.svg',metadata={'Date':None});plt.close(fig)
    fig,axes=plt.subplots(5,2,figsize=(12,13),layout='constrained')
    for n,ax in enumerate(axes.flat):
        for name in ('ZERO','FIXED',pi,'MAX'):
            v=[r for r in rows if int(r['network'])==n and r['condition']=='LOSS' and r['controller']==name]
            y=np.array([np.mean([float(r['rate_hz'])-(float(r['target_hz'])-1) for r in v if int(r['second'])==k]) for k in range(32)])
            ax.plot(np.arange(32)+.5,y,label=name,color=colors[name],linewidth=1)
        ax.axhline(1,color='black',ls='--',lw=.8);ax.axvline(16,color='black',ls=':',lw=.8)
        ax.set(title=f'Development network {n}',xlabel='Time after control start (s)',ylabel='Rate − calibration baseline (Hz)')
    axes.flat[0].legend(fontsize=7,ncol=2);fig.suptitle('Hidden efficacy loss: means across two fresh noise replicates; 1 s recorded rates')
    export(fig,'loss_timecourses')
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for ax,cond in zip(axes,('STATIC','LOSS')):
        for name in ('ZERO','FIXED',pi,'MAX'):
            y=s['models'][name][cond]['network_mae_hz'];ax.plot(range(10),y,'o-',color=colors[name],label=name)
        ax.axhline(.35,color='black',ls='--',lw=.8,label='Frozen .35 Hz criterion')
        ax.set(title=f'{cond}: '+('late 12 s' if cond=='LOSS' else 'last 24 s'),xlabel='Network',ylabel='Mean absolute 1 s rate error (Hz)')
    axes[0].legend(fontsize=7);export(fig,'network_error')
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for name in ('ZERO','FIXED',pi,'MAX'):
        v=[r for r in rows if r['condition']=='LOSS' and r['controller']==name]
        y=[np.mean([float(r['q_pA']) for r in v if int(r['second'])==k]) for k in range(32)]
        axes[0].plot(np.arange(32),y,label=name,color=colors[name])
    axes[0].axvline(16,color='black',ls=':');axes[0].set(xlabel='Control time (s)',ylabel='Held desired C02 current (pA/channel)',title='No extra probing; feedback changes dose');axes[0].legend(fontsize=7)
    metrics=list(csv.DictReader((a.analysis/'metrics.csv').open()))
    names=['ZERO','FIXED',pi,'MAX'];cal=[];online=[]
    for name in names:
        v=[r for r in metrics if r['controller']==name and r['condition']=='LOSS' and r['window']=='late']
        cal.append(np.mean([float(r['calibration_exposure_pA_s'])*50/1000 for r in v]));online.append(np.mean([float(r['online_exposure_pA_s'])*50/1000 for r in v]))
    axes[1].bar(names,cal,label='51 s calibration',color='#b6c9d9');axes[1].bar(names,online,bottom=cal,label='32 s online',color='#146ba4')
    axes[1].set(ylabel='Aggregate model current charge (nC)',title='Full exposure per independent policy');axes[1].legend(fontsize=7)
    export(fig,'actions_and_costs')


if __name__=='__main__':main()
