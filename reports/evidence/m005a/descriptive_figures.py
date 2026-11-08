import argparse,csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import numpy as np


def main():
    p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);a=p.parse_args();s=json.loads((a.analysis/'descriptive_summary.json').read_text())
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.hashsalt':'m005a-descriptive','font.size':9})
    def save(f,name):
        f.savefig(a.analysis/f'{name}.png',dpi=140);f.savefig(a.analysis/f'{name}.svg',metadata={'Date':None});plt.close(f)
    rows=list(csv.DictReader((a.analysis/'network_models.csv').open()));names=list(s['models'])
    fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
    for ax,condition in zip(axes,('STATIC','LOSS')):
        for name in names:
            ys=[next(float(r['mae_hz']) for r in rows if int(r['network'])==n and r['condition']==condition and r['controller']==name) for n in range(10)]
            ax.plot(range(10),ys,'o-',lw=1,label=name)
        ax.axhline(.35,color='black',ls='--',lw=.8);ax.set(xlabel='Network',ylabel='1 s rate MAE (Hz)',title=condition+' — tuning only; no confirmation')
    axes[0].legend(fontsize=7,ncol=2);save(fig,'tuning_network_errors')
    traces=list(csv.DictReader((a.analysis/'traces.csv').open()));fig,axes=plt.subplots(5,2,figsize=(12,13),layout='constrained')
    for n,ax in enumerate(axes.flat):
        for name in names:
            v=sorted([r for r in traces if int(r['network'])==n and r['condition']=='LOSS' and r['controller']==name],key=lambda r:int(r['second']))
            ax.plot(np.arange(32)+.5,[float(r['rate_hz'])-float(r['target_hz'])+1 for r in v],lw=.8,label=name)
        ax.axhline(1,color='black',ls='--',lw=.8);ax.axvline(16,color='black',ls=':',lw=.8)
        ax.set(title=f'Network{n}, one tuning noise',xlabel='Relative time (s)',ylabel='Rate − calibrated baseline (Hz)')
    axes.flat[0].legend(fontsize=6,ncol=3);fig.suptitle('Descriptive tuning records — not scientific qualification');save(fig,'tuning_loss_rates')
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for name in names:
        v=[r for r in traces if r['condition']=='LOSS' and r['controller']==name]
        axes[0].plot(range(32),[np.mean([float(r['q_pA']) for r in v if int(r['second'])==k]) for k in range(32)],label=name)
    axes[0].axvline(16,color='black',ls=':');axes[0].set(xlabel='Relative time (s)',ylabel='Desired C02 pA/channel',title='Mean desired dose (delivered ramps archived)');axes[0].legend(fontsize=7)
    charge=[s['models'][name]['LOSS']['mean_nominal_charge_pC']/1000 for name in names]
    axes[1].bar(names,charge);axes[1].tick_params(axis='x',rotation=25);axes[1].set(ylabel='Nominal model charge (nC)',title='51 s calibration +32 s online cost');save(fig,'tuning_actions_costs')


if __name__=='__main__':main()
