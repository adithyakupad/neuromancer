"""Deterministic descriptive figures; no parameters or targets selected here."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main(output):
    output=Path(output);result=json.loads((output/'comparison.json').read_text())
    trials=json.loads((output/'trial_provenance.json').read_text())
    with np.load(output/'calibration_data.npz',allow_pickle=False) as archive:data={k:archive[k] for k in archive.files}
    assert len(trials)==50 and result['completed_branches']==400
    assert data['raw_rate_hz'].shape==(10,5,2,4,300)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'svg.hashsalt':'neuromancer-m0023'})
    files=[]
    def save(fig,name):
        fig.tight_layout()
        for extension in ('png','svg'):
            path=output/f'{name}.{extension}'
            fig.savefig(path,dpi=140,bbox_inches='tight',metadata={'Date':None} if extension=='svg' else {'Software':'NEUROMANCER M002.3'})
            files.append(path)
        plt.close(fig)
    fig,axes=plt.subplots(2,5,figsize=(15,6),sharex=True,sharey=True)
    for n,ax in enumerate(axes.flat):
        for t in trials:
            if t['network_id']!=n:continue
            cal=t['calibration'];ax.plot((0,30,60,90,120),cal['h_hz'],'o-',alpha=.55,lw=1,label=f"noise {t['replicate_id']}")
        ax.axhline(0,color='grey',lw=.5);ax.set_title(f'Network {n}');ax.set_xlabel('C02 q (pA/channel)');ax.set_ylabel('Preceding-zero response (Hz)')
    axes.flat[-1].legend(fontsize=7);fig.suptitle('Prospective calibration: five independent prefixes per network',y=1.02)
    save(fig,'calibration_maps')
    fig,axes=plt.subplots(2,2,figsize=(11,7));x=np.arange(10)
    spans=np.array([n['span']['mean'] for n in result['networks']]);sigma=np.array([n['sigma_1s_rms'] for n in result['networks']])
    axes[0,0].plot(x,spans,'o-',label='Mean target span');axes[0,0].plot(x,2*sigma,'s-',label='2 x standalone 1s SD')
    axes[0,0].axhline(1,color='black',ls='--',label='1 Hz minimum');axes[0,0].set_ylabel('Hz');axes[0,0].legend()
    means=np.array([n['reduced_headroom']['mean'] for n in result['networks']]);lo=np.array([n['reduced_headroom']['lower'] for n in result['networks']]);hi=np.array([n['reduced_headroom']['upper'] for n in result['networks']])
    axes[0,1].errorbar(x,means,yerr=[means-lo,hi-means],fmt='o');axes[0,1].axhline(0,color='black',ls='--');axes[0,1].set_ylabel('Reduced-gain headroom margin (Hz; t95%)')
    for gi,ax in enumerate(axes[1]):
        for ti,label in enumerate(('Low','High')):
            vals=[n['normalized_absolute_error']['mean'][gi][ti] if n['normalized_absolute_error']['mean'] is not None else np.nan for n in result['networks']]
            ax.plot(x,vals,'o-',label=label)
        ax.axhline(.25,color='black',ls='--');ax.set_ylabel(f"Normalized absolute error, g={(1,.6)[gi]}");ax.legend()
    for ax in axes.flat:ax.set_xlabel('Training network');ax.set_xticks(x)
    fig.suptitle('Frozen qualification components; lookup-error gaps mark invalid calibration (networks1,2,6)')
    save(fig,'qualification_components')
    keys=list(result['component_counts']);matrix=np.array([[n['components'][k] for k in keys] for n in result['networks']])
    fig,ax=plt.subplots(figsize=(11,5));ax.imshow(matrix,cmap=matplotlib.colors.ListedColormap(['#bd4d50','#3f946c']),vmin=0,vmax=1,aspect='auto')
    ax.set_xticks(range(len(keys)),keys,rotation=30,ha='right');ax.set_yticks(range(10),range(10));ax.set_ylabel('Training network')
    for n in range(10):
        for k in range(len(keys)):ax.text(k,n,'PASS' if matrix[n,k] else 'FAIL',ha='center',va='center',color='white',fontsize=8)
    ax.set_title(f"Slow qualification: {result['qualified_networks']}/10 jointly; required 8/10")
    save(fig,'qualification_gate')
    fig,axes=plt.subplots(2,2,figsize=(12,7),sharex=True)
    rates=data['raw_rate_hz'];prefix=data['prefix_counts'].reshape(10,5,2550,4,5)[:,:,:,:,:4].sum(axis=(-1,-2))/1.6
    baseline=prefix[:,:,350:750].mean(axis=-1);epochs=rates.reshape(10,5,2,4,6,50).mean(axis=-1)
    for gi in range(2):
        for ai,(name,color) in enumerate(zip(('S','C120','L','H'),('grey','black','#4179b2','#bd5740'))):
            values=(epochs[:,:,gi,ai]-baseline[:,:,None]).mean(axis=1)
            axes[0,gi].errorbar(np.arange(6)+.5,values.mean(axis=0),yerr=values.std(axis=0,ddof=1)/np.sqrt(10),label=name,color=color,marker='o')
        axes[0,gi].set_title(f'g={(1,.6)[gi]} (network mean +/- SEM; descriptive)');axes[0,gi].set_ylabel('1s observed rate - prefix baseline (Hz)');axes[0,gi].legend()
        for ti,name in enumerate(('L','H')):
            errors=[]
            for n in range(10):
                t=[t for t in trials if t['network_id']==n]
                targets=np.array([v['calibration']['targets_hz'][ti] for v in t])
                errors.append((epochs[n,:,gi,ti+2]-targets[:,None]).mean(axis=0))
            values=np.array(errors);axes[1,gi].plot(np.arange(6)+.5,values.mean(axis=0),'o-',label=name)
        axes[1,gi].axhline(0,color='grey');axes[1,gi].set_ylabel('Actual rate - prospective target (Hz)');axes[1,gi].legend()
        for ax in axes[:,gi]:ax.set_xlabel('Seconds after common checkpoint')
    fig.suptitle('All50 trials; L/H include zero-current fallbacks for three invalid calibrations')
    save(fig,'confirmation_timecourses')
    fig,axes=plt.subplots(2,5,figsize=(15,6),sharex=True)
    seconds=(np.arange(300)+1)*.02
    for n,ax in enumerate(axes.flat):
        for gi,(gain,color) in enumerate(zip((1.,.6),('#4179b2','#bd5740'))):
            trace=data['filtered_sector_rates_hz'][n,:,gi,3].mean(axis=(0,2))-baseline[n].mean()
            ax.plot(seconds,trace,color=color,label=f'g={gain}')
        high=np.mean([t['calibration']['targets_hz'][1]-t['calibration']['baseline_hz'] for t in trials if t['network_id']==n])
        ax.axhline(high,color='black',ls='--',label='Prospective H')
        ax.set_title(f'Network {n}' + (' (1 fallback)' if result['networks'][n]['calibration_failures'] else ''));ax.set_xlabel('Seconds after checkpoint');ax.set_ylabel('Filtered H hold - baseline (Hz)')
    axes.flat[-1].legend(fontsize=7)
    fig.suptitle('Secondary100ms causal-filter diagnostics: means of five noise replicates',y=1.02)
    save(fig,'secondary_100ms')
    record=dict(source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (output/'figure_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))


if __name__=='__main__':main(*sys.argv[1:])
