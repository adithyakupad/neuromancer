"""Render fixed diagnostic comparisons; no action selection or model changes."""
from pathlib import Path
import json
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt


def main(output):
    output=Path(output)
    summary=json.loads((output/'comparison.json').read_text())
    names=summary['action_names'][1:]
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.hashsalt':'neuromancer-m0021'})
    def save(fig,name):
        fig.savefig(output/f'{name}.svg',metadata={'Date':None})
        fig.savefig(output/f'{name}.png',dpi=160)
        plt.close(fig)
    means=np.array(summary['selection']['fixed_primary']['mean'])[:,1:]
    fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
    image=ax.imshow(means,aspect='auto',cmap='viridis',vmin=0,vmax=max(4,float(means.max())))
    ax.set(xticks=range(7),xticklabels=names,yticks=range(10),ylabel='Training network',
           title='g = 0.6: paired observed E response, five-noise mean')
    for n in range(10):
        for a in range(7):ax.text(a,n,f'{means[n,a]:.2f}',ha='center',va='center',color='white',fontsize=9)
    fig.colorbar(image,ax=ax,label='Stimulation − sham (Hz); authority threshold 4 Hz')
    save(fig,'network_authority')
    fixed=summary['aggregate_fixed_population_response']
    mean,lo,hi=[np.array(fixed[key]) for key in ['mean','lower','upper']]
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for g,label in enumerate(['g = 0.6','g = 1.0']):
        for pop,color,offset,pop_label in [(0,'C0',-.10,'Recorded unstimulated E (80)'),
                                        (1,'C1',.10,'All fixed unstimulated E (600)')]:
            y=mean[g,1:,pop]
            axes[g].errorbar(np.arange(7)+offset,y,
                yerr=[y-lo[g,1:,pop],hi[g,1:,pop]-y],fmt='o',capsize=3,color=color,label=pop_label)
        axes[g].axhline(4,color='black',ls='--',label='4 Hz threshold')
        axes[g].set(xticks=range(7),xticklabels=names,ylabel='Paired firing-rate response (Hz)',title=label)
    axes[0].legend(fontsize=8)
    save(fig,'population_response')
    current=summary['current_delta'];group=summary['current_groups'].index('observed_E')
    values=np.array(current['mean'])[0,1:,group]
    lower=np.array(current['lower'])[0,1:,group]
    upper=np.array(current['upper'])[0,1:,group]
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    for index,(label,color,offset) in enumerate([('Excitatory','C0',-.18),('Inhibitory','C1',.18)]):
        y=values[:,index]
        ax.errorbar(np.arange(7)+offset,y,yerr=[y-lower[:,index],upper[:,index]-y],
                    fmt='o',capsize=3,color=color,label=label)
    ax.plot(range(7),values.sum(axis=-1),'s-',color='black',label='Total recurrent (mean)')
    ax.axhline(0,color='grey',linewidth=.8)
    ax.set(xticks=range(7),xticklabels=names,ylabel='Paired mean current change (pA)',
           title='Observed E current decomposition, g = 0.6 (not an inhibitory ablation)')
    ax.legend(fontsize=8);save(fig,'recurrent_currents')
    with np.load(output/'authority_data.npz',allow_pickle=False) as data:
        schedules=data['delivered_current_pA'][0,0,0]
        post=data['post_ramp_observed_response_hz'].mean(axis=(0,1))[0,1:]
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for a,label in [(1,'D'),(2,'C (every pair)')]:
        axes[0].step(np.arange(7)*.02,schedules[a,:7].sum(axis=-1),where='post',label=label)
    axes[0].set(xlabel='Time after intervention onset (s)',ylabel='Total current (pA)',title='Different ramps, same 240 pA plateau')
    axes[0].legend()
    axes[1].plot(range(7),mean[0,1:,0],'o-',label='Full 5 s window')
    axes[1].plot(range(7),post,'s--',label='Common 4.94 s post-ramp window')
    axes[1].axhline(4,color='black',ls=':')
    axes[1].set(xticks=range(7),xticklabels=names,ylabel='Mean paired observed E response (Hz)',title='Ramp sensitivity; primary gate unchanged')
    axes[1].legend(fontsize=8);save(fig,'ramp_sensitivity')


if __name__=='__main__':main(sys.argv[1])
