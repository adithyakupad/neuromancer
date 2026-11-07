"""Deterministic M003.1 descriptive figures; no model/gate selection."""
import argparse
import json
from pathlib import Path
import hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

NAMES=('S','SHORT','LONG','NEAR','FAR','R')
MODELS=('STATIC','FIR','ARX','AR','STATIC_SHUFFLED','FIR_SHUFFLED','ARX_SHUFFLED')
COLORS=('#997337','#4278a3','#ce653d','gray','#c4a775','#85acca','#dfaa93')


def main(output):
    output=Path(output);r=json.load(open(output/'comparison.json'));summary=r['network_summary'];files=[]
    with np.load(output/'data.npz',allow_pickle=False) as a:d={k:a[k] for k in a.files}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'svg.hashsalt':'neuromancer-m003-1'})
    def save(fig,name):
        fig.tight_layout()
        for ext in ('png','svg'):
            p=output/f'{name}.{ext}';fig.savefig(p,dpi=140,bbox_inches='tight',metadata={'Date':None} if ext=='svg' else {'Software':'NEUROMANCER M003.1'});files.append(p)
        plt.close(fig)
    nets=r['networks'];matrix=np.array([n['evoked_mse'] for n in nets])[:,:,2]
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for i in (0,1,2,3,6):axes[0].plot(range(10),matrix[:,i],'o-',label=MODELS[i],color=COLORS[i])
    axes[0].set(xlabel='Development network',ylabel='Reserved 1s mean effect MSE (Hz²)');axes[0].legend(fontsize=8)
    primary=r['absolute'];axes[1].errorbar([0],[primary['mean']],yerr=[[primary['mean']-primary['lower']],[primary['upper']-primary['mean']]],fmt='o',capsize=5)
    axes[1].axhline(0,color='black');axes[1].axhline(.04,color='gray',ls='--',label='Frozen meaningful gain floor');axes[1].legend(fontsize=8)
    axes[1].set_xticks([0],[r['primary_competitor']+' minus ARX']);axes[1].set_ylabel('Paired network-bootstrap 95% improvement (Hz²)')
    fig.suptitle('M003.1 primary superiority gate: '+r['scientific_gate']);save(fig,'primary_comparison')
    include=np.where(d['identities'][:,1]!=25)[0];truth=d['rates'][include]-d['rates'][include,0,None];pred=d['forecast'][include]-d['forecast'][include,:,0,None]
    fig,axes=plt.subplots(4,5,figsize=(15,10),sharex=True)
    t=(np.arange(100)+1)*.02
    for c in range(4):
        for a,name in enumerate(NAMES[1:],1):
            ax=axes[c,a-1];ax.plot(t,truth[:,a,:,c].mean(axis=0),color='black',label='Paired actual')
            for i in (0,1,2):ax.plot(t,pred[:,i,a,:,c].mean(axis=0),color=COLORS[i],label=MODELS[i])
            if c==0:ax.set_title(name)
            if a==1:ax.set_ylabel(f'Sector {c} effect (Hz)')
            if c==3:ax.set_xlabel('Seconds after common origin')
    axes[0,0].legend(fontsize=7);fig.suptitle('Fresh reserved patterns: same origin and no future observations',y=1.01);save(fig,'held_out_effects')
    fig,axes=plt.subplots(1,3,figsize=(13,4));h=np.array([20,200,1000,2000])
    for i in (0,1,2):
        axes[0].plot(h,np.array(summary['evoked_mse']['mean'])[i],'-o',label=MODELS[i],color=COLORS[i])
        axes[1].plot(h,np.array(summary['absolute_mse']['mean'])[i],'-o',label=MODELS[i],color=COLORS[i])
    axes[0].set(xscale='log',xlabel='Mean forecast horizon (ms)',ylabel='Paired effect MSE (Hz²)');axes[0].legend()
    axes[1].set(xscale='log',xlabel='Mean forecast horizon (ms)',ylabel='Absolute rate MSE (Hz²)')
    axes[2].bar(range(7),summary['ordinary_mse']['mean'],color=COLORS);axes[2].set_xticks(range(7),MODELS,rotation=75,fontsize=7);axes[2].set_ylabel('Conditional next-step MSE (Hz²)')
    fig.suptitle('Distinct prediction tasks; secondary horizons do not rescue primary gate');save(fig,'tasks_and_horizons')
    fig,axes=plt.subplots(1,3,figsize=(14,4));coverage=np.array(summary['coverage']['mean'])
    axes[0].imshow(coverage,aspect='auto',vmin=0,vmax=1,cmap='viridis');axes[0].set_xticks(range(4),['20ms','200ms','1s','2s']);axes[0].set_yticks(range(7),MODELS);axes[0].set_title('Empirical absolute-output coverage')
    for i in range(7):
        for j in range(4):axes[0].text(j,i,f'{coverage[i,j]:.2f}',ha='center',va='center',color='white',fontsize=7)
    axes[1].bar(range(7),summary['residual_lag1_acf']['mean'],color=COLORS);axes[1].set_xticks(range(7),MODELS,rotation=75,fontsize=7);axes[1].set_ylabel('Within-branch residual lag1 correlation')
    means=np.array(summary['dynamic_contrast_mse']['mean'])
    for i in (0,1,2):axes[2].plot(range(4),means[i,[1,2,1,2],[0,0,1,1]],'o-',label=MODELS[i],color=COLORS[i])
    axes[2].set_xticks(range(4),['Short−Long .2s','Short−Long 1s','Near−Far .2s','Near−Far 1s'],rotation=40);axes[2].set_ylabel('Equal-charge timing contrast MSE (Hz²)');axes[2].legend()
    save(fig,'calibration_and_dynamic_contrasts')
    null=r['null_controls'];fig,axes=plt.subplots(1,2,figsize=(10,3))
    for i in (0,1,2):axes[0].plot([n['network_id'] for n in null],[n['false_response_rms'][i] for n in null],'o-',label=MODELS[i],color=COLORS[i])
    axes[0].axhline(.2,color='gray',ls='--');axes[0].set(xlabel='Null network, fresh noise25',ylabel='Predicted effect RMS (Hz)',title='Actual null effect exactly zero');axes[0].legend()
    axes[1].bar([0],[r['maximum_origin_history_effect_difference']]);axes[1].set_yscale('symlog',linthresh=1e-14);axes[1].set(ylabel='Max contrast difference (Hz)',title='ARX observation-history replacement');axes[1].set_xticks([0],['All trials/plans'])
    save(fig,'null_and_history_ablation')
    record=dict(source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (output/'figure_manifest.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
