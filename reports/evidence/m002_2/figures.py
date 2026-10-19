"""Deterministic M002.2 figures, fixed comparisons only."""
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt


def main(output):
    output=Path(output);s=json.loads((output/'comparison.json').read_text())
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.hashsalt':'neuromancer-m0022'})
    def save(fig,name):
        fig.savefig(output/f'{name}.png',dpi=160)
        fig.savefig(output/f'{name}.svg',metadata={'Date':None});plt.close(fig)
    late=s['summaries']['late_static']
    mean,lo,hi=[np.array(late[k]) for k in ('mean','lower','upper')]
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for g,gain in enumerate(s['gains']):
        for ids,x,label,color in [(np.array([0,1,2,3,4]),[0,24,60,120,240],'Distributed','C0'),
                                  (np.array([0,5,6,7,8]),[0,60,120,180,240],'Channels 0 + 2','C1')]:
            y=mean[g,ids]
            axes[g].errorbar(x,y,yerr=[y-lo[g,ids],hi[g,ids]-y],fmt='o-',capsize=3,label=label,color=color)
        axes[g].axhline(4,color='black',ls=':',label='Failed V0.1 +4 Hz')
        axes[g].set(xlabel='Plateau total current (pA)',ylabel='Paired late response (Hz)',title=f'g = {gain}')
    axes[0].legend(fontsize=8);save(fig,'static_dose_response')
    whole=s['summaries']['whole'];wm,wl,wh=[np.array(whole[k]) for k in ('mean','lower','upper')]
    fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
    for g,gain in enumerate(s['gains']):
        for x,(a,b,label) in enumerate([(9,3,'Periodic / D30'),(10,8,'Alternate / C120'),(11,1,'Pulse / D6')]):
            for offset,j,color in [(-.12,a,'C2'),(.12,b,'C0')]:
                axes[g].errorbar(x+offset,wm[g,j],yerr=[[wm[g,j]-wl[g,j]],[wh[g,j]-wm[g,j]]],
                                 fmt='o',color=color,capsize=3,label='Dynamic' if x==0 and offset<0 else ('Charge-matched constant' if x==0 else None))
        axes[g].set(xticks=range(3),xticklabels=['Periodic / D30','Alternate / C120','Pulse / D6'],
            ylabel='Paired whole-window response (Hz)',title=f'Equal charge comparisons, g = {gain}')
    axes[0].legend(fontsize=8);save(fig,'dynamic_charge_comparison')
    cyc=s['summaries']['dynamic_cycle_filtered'];cm,cl,ch=[np.array(cyc[k]) for k in ('mean','lower','upper')]
    with np.load(output/'reachability_data.npz',allow_pickle=False) as data:
        actions=data['delivered_current_pA'][0,0,0]
        timecourse=data['filtered_response_hz'].mean(axis=(0,1))
    fig,axes=plt.subplots(2,3,figsize=(13,6),layout='constrained')
    for j,a in enumerate((9,10,11)):
        axes[0,j].step(np.arange(50)*.02,actions[a,:50].sum(axis=-1),where='post',label='Total')
        if a==10:
            axes[0,j].step(np.arange(50)*.02,actions[a,:50,0],where='post',label='Channel 0')
            axes[0,j].step(np.arange(50)*.02,actions[a,:50,1],where='post',label='Channel 1');axes[0,j].legend(fontsize=8)
        axes[0,j].set(title=s['action_names'][a]+' (first delivered cycle)',ylabel='Delivered pA',xlabel='Cycle time (s)')
        for g,gain in enumerate(s['gains']):
            t=(np.arange(50)+1)*.02
            axes[1,j].plot(t,cm[g,j],label=f'g={gain}');axes[1,j].fill_between(t,cl[g,j],ch[g,j],alpha=.18)
        axes[1,j].axhline(0,color='grey',lw=.7)
        axes[1,j].set(xlabel='Completed-bin cycle time (s)',ylabel='Paired filtered response (Hz)',title='Response: mean over cycles 1–5')
    axes[1,0].legend(fontsize=8);save(fig,'dynamic_cycles')
    gate=s['objective_gate'];span=np.array(gate['span_hz']);high=np.array(gate['high_hz']);reduced=np.array(gate['reduced_response_lower95_hz'])
    fig,axes=plt.subplots(1,3,figsize=(13,4),layout='constrained')
    for j,label in enumerate(('filtered100ms','epoch1s')):
        sigma=np.array(gate['scales'][label]['sigma_hz'])
        axes[j].plot(range(10),span,'o-',label='Candidate high-low span')
        axes[j].plot(range(10),2*sigma,'s--',label='2 × standalone noise SD')
        axes[j].axhline(1,color='black',ls=':',label='1 Hz minimum')
        axes[j].set(xlabel='Training network',ylabel='Hz',title=f'{label}: {gate["scales"][label]["pass_count"]}/10 all gates')
    axes[2].plot(range(10),high,'o-',label='Candidate high excursion')
    axes[2].plot(range(10),reduced,'s--',label='Reduced response lower 95% CI')
    axes[2].set(xlabel='Training network',ylabel='Hz above baseline',title='Headroom / precision gate')
    failed=high>reduced
    axes[2].plot(np.flatnonzero(failed),high[failed],'rx',ms=8,label='Headroom gate fails')
    for ax in axes:ax.set_xticks(range(10))
    axes[0].legend(fontsize=7);axes[2].legend(fontsize=7);save(fig,'objective_feasibility')
    readout=s['condition_readout'];rm,rl,rh=[np.array(readout[k]) for k in ('mean','lower','upper')]
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for g,gain in enumerate(s['gains']):
        axes[0].errorbar(np.arange(3)+(g-.5)*.12,rm[g],yerr=[rm[g]-rl[g],rh[g]-rm[g]],fmt='o',capsize=3,label=f'g={gain}')
        axes[1].plot((np.arange(50)+1)*.02,timecourse[g,8,:50],label=f'C120 g={gain}')
        axes[1].plot((np.arange(50)+1)*.02,timecourse[g,4,:50],ls='--',label=f'D60 g={gain}')
    axes[0].axhline(.5,color='grey',ls=':');axes[0].set(ylim=(0,1.05),xticks=range(3),
        xticklabels=['Sham / C120','D30 / D60','D60 / C120'],ylabel='Held-out-noise balanced accuracy',title='One-second scalar readout')
    axes[1].set(xlabel='Completed-bin time since onset (s)',ylabel='Mean paired filtered response (Hz)',title='Step response: neural + bin + filter timing')
    axes[0].legend(fontsize=8);axes[1].legend(fontsize=8);save(fig,'readout_and_step_response')
    assert len(list(output.glob('*.png')))>=5


if __name__=='__main__':main(sys.argv[1])
