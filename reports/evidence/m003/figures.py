"""Deterministic held-out M003 figures; no selection or scientific gates."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MODELS=('CONSTANT','AR','ARX','SHUFFLED')
COLORS=('gray','#4278a3','#ce653d','#589b71')


def main(output,stationary=None):
    output=Path(output);result=json.loads((output/'comparison.json').read_text())
    metrics=json.loads((output/'trial_metrics.json').read_text())
    with np.load(output/'identification_data.npz',allow_pickle=False) as archive:data={k:archive[k] for k in archive.files}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'svg.hashsalt':'neuromancer-m003'})
    files=[]
    def save(fig,name):
        fig.tight_layout()
        for ext in ('png','svg'):
            path=output/f'{name}.{ext}';fig.savefig(path,dpi=140,bbox_inches='tight',metadata={'Date':None} if ext=='svg' else {'Software':'NEUROMANCER M003'});files.append(path)
        plt.close(fig)
    nets=result['networks'];x=np.arange(len(nets));mse=np.array([n['evoked_mse'] for n in nets])[:,:,2]
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for mi,(model,color) in enumerate(zip(MODELS,COLORS)):axes[0].plot(x,mse[:,mi],'o-',label=model,color=color)
    axes[0].set_xticks(x,[n['network_id'] for n in nets]);axes[0].set(xlabel='Network',ylabel='Reserved1s mean evoked-response MSE (Hz²)');axes[0].legend()
    for j,name in enumerate(('AR','SHUFFLED')):
        c=result['comparisons'][name]['absolute'];axes[1].errorbar(j,c['mean'],yerr=[[c['mean']-c['lower']],[c['upper']-c['mean']]],fmt='o',capsize=5,label=name)
    axes[1].axhline(0,color='black');axes[1].axhline(.04,color='gray',ls='--',label='Absolute mean benefit floor')
    axes[1].set_xticks([0,1],['AR minus ARX','SHUFFLED minus ARX']);axes[1].set_ylabel('MSE improvement,network-bootstrap95% (Hz²)');axes[1].legend()
    fig.suptitle(f"Stage {result['stage']}: frozen primary gate {result['scientific_gate']}")
    save(fig,'primary_response_error')
    include=np.where(data['identities'][:,1]!=21)[0];assert len(include)>0
    truth=data['rates'][include]-data['rates'][include,0,None]
    predicted=data['forecast'][include]-data['forecast'][include,:,0,None]
    fig,axes=plt.subplots(4,5,figsize=(15,10),sharex=True)
    for sector in range(4):
        for a,name in enumerate(('P01','P12','P23','P03','R'),1):
            ax=axes[sector,a-1];t=(np.arange(100)+1)*.02
            ax.plot(t,truth[:,a,:,sector].mean(axis=0),color='black',label='Paired actual')
            for mi in (1,2,3):ax.plot(t,predicted[:,mi,a,:,sector].mean(axis=0),color=COLORS[mi],label=MODELS[mi],ls='--' if mi==1 else '-')
            if sector==0:ax.set_title(name)
            if a==1:ax.set_ylabel(f'Sector {sector} effect (Hz)')
            if sector==3:ax.set_xlabel('Seconds from common forecast origin')
    axes[0,-1].legend(fontsize=7)
    fig.suptitle('Reserved paired effects: mean across networks and repeated noise; no future observations used',y=1.02)
    save(fig,'held_out_responses')
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    ordinary=result['ordinary_next_mse'];means=np.array(ordinary['mean']);lo=np.array(ordinary['lower']);hi=np.array(ordinary['upper'])
    axes[0].bar(np.arange(4),means,color=COLORS,yerr=[means-lo,hi-means],capsize=3)
    axes[0].set_xticks(range(4),MODELS,rotation=25);axes[0].set_ylabel('Ordinary next-step MSE (Hz²)')
    coverage=np.array(result['common_coverage']['mean']);im=axes[1].imshow(coverage,vmin=0,vmax=1,cmap='viridis',aspect='auto')
    axes[1].set_xticks(range(3),['20ms','200ms','1s']);axes[1].set_yticks(range(4),MODELS);axes[1].set_title('Common-origin output interval coverage')
    for i in range(4):
        for h in range(3):axes[1].text(h,i,f'{coverage[i,h]:.2f}',ha='center',va='center',color='white')
    nextcoverage=result['next_coverage']['mean'];axes[2].bar(range(4),nextcoverage,color=COLORS);axes[2].axhline(.95,color='black',ls='--')
    axes[2].set_xticks(range(4),MODELS,rotation=25);axes[2].set(ylim=(0,1.05),ylabel='Teacher-forced next-step interval coverage')
    fig.suptitle('Ordinary prediction and empirical intervals are separate from paired-effect qualification')
    save(fig,'ordinary_prediction_and_coverage')
    null=result['null_controls']
    if null:
        fig,ax=plt.subplots(figsize=(7,3));ax.bar([str(v['network_id']) for v in null],[v['ARX_false_response_rms_hz'] for v in null],color=COLORS[2])
        ax.axhline(.2,color='black',ls='--',label='Descriptive false-response warning,not a gate')
        ax.set(xlabel='Prespecified null-control network,noise21',ylabel='Predicted1s evoked RMS (Hz)',title='g=0: actual paired response exactly zero');ax.legend(fontsize=7)
        save(fig,'zero_coupling_control')
    if stationary:
        old=json.loads((Path(stationary)/'trial_metrics.json').read_text());fig,axes=plt.subplots(1,2,figsize=(11,4))
        for m in metrics:
            ref=next(v for v in old if v['network_id']==m['network_id'] and v['replicate_id']==m['replicate_id'])
            axes[0].plot([0,1],[ref['evoked_mse'][2][2],m['evoked_mse'][2][2]],'o-',label=str(m['network_id']))
            axes[1].plot([0,1],[ref['residual_score_observed_minus_predicted'][2],m['residual_score_observed_minus_predicted'][2]],'o-')
        axes[0].set_ylabel('Frozen ARX evoked1s MSE (Hz²)');axes[0].legend(ncol=2,fontsize=7,title='Network')
        axes[1].set_ylabel('Observed minus predicted1s rate (Hz)')
        for ax in axes:ax.set_xticks([0,1],['Stationary g=1','Hidden g=.6'])
        fig.suptitle('Frozen-model OOD stress: paired noise18; no gain input or parameter update')
        save(fig,'efficacy_stress')
    record=dict(source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),files={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in files})
    (output/'figure_manifest.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--stationary');a=p.parse_args();main(a.output,a.stationary)
