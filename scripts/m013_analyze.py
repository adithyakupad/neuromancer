"""Independent scoring from saved held-out predictions; no neural acquisition."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.stats import t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(sys.argv[1]);rows=json.loads((root/'results.json').read_text())
verified=[]
for row in rows:
    archive=np.load(root/f"{row['network']}_{row['condition']}.npz")
    labels=archive['y_test'];predicted=archive['prediction_test']>=.5
    accuracy=float(np.mean([np.mean(predicted[labels==value]==value) for value in [0,1]]))
    assert accuracy==row['accuracy']
    ledger=json.loads((root/f"{row['network']}_{row['condition']}.json").read_text())
    assert len(ledger['learning'])==32
    previous=np.zeros(4);exposure=0
    for index,record in enumerate(ledger['receipts']):
        current=np.array(record['delivered']);requested=np.array(record['requested'])
        assert record['start_us']==index*20000 and record['stop_us']==(index+1)*20000
        assert np.array_equal(current,requested)
        assert current.min()>=0 and current.max()<=120 and current.sum()<=240
        assert np.abs(current-previous).max()<=30
        previous=current;exposure+=current.sum()*.02
    weights=archive['final_weights'];assert np.all(np.isfinite(weights)) and weights.min()>=0 and weights.max()<=30
    if row['condition']=='C0':assert np.array_equal(archive['initial_weights'],weights)
    row['exposure_pA_s']=exposure
    row['probe_design_condition']=float(np.linalg.cond(np.column_stack((np.ones(len(archive['x_probe'])),(archive['x_probe']-archive['mean'])/archive['scale']))))
    counts=np.array([x['counts'] for x in ledger['receipts']])
    row['recorded_E_rate_Hz']=float(counts.reshape(-1,4,5)[:,:,:4].sum()/(len(counts)*.02*80))
    row['recorded_I_rate_Hz']=float(counts.reshape(-1,4,5)[:,:,4].sum()/(len(counts)*.02*20))
    row['confusion']=[[int(np.sum((labels==a)&(predicted==b))) for b in [0,1]] for a in [0,1]]
    verified.append(row)
for network in [13000,13001]:
    frozen=np.load(root/f'{network}_C0.npz')
    for condition in range(1,5):
        current=np.load(root/f'{network}_C{condition}.npz')
        np.testing.assert_array_equal(frozen['initial_weights'],current['initial_weights'])
        for split in ['train','probe','validation','test','delay20','delay100']:
            np.testing.assert_array_equal(frozen['symbols_'+split],current['symbols_'+split])
    assert len(set(r['exposure_pA_s'] for r in verified if r['network']==network))==1
paired=np.array([next(r['accuracy'] for r in verified if r['network']==n and r['condition']=='C1')-
                 next(r['accuracy'] for r in verified if r['network']==n and r['condition']=='C0') for n in [13000,13001]])*100
mean=float(paired.mean());margin=float(t.ppf(.975,1)*paired.std(ddof=1)/np.sqrt(2))
summary=dict(pilot=True,confirmatory=False,network_count=2,rows=verified,effect_pp=mean,
             paired_effects_pp=paired.tolist(),descriptive_t95_pp=[mean-margin,mean+margin],
             scientific_decision='INCONCLUSIVE PILOT; confirmation NOT RUN',
             arithmetic_thresholds_met=bool(mean>=5 and mean-margin>0))
(root/'independent_analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axes=plt.subplots(2,3,figsize=(12,7))
for condition in range(5):
    group=[r for r in rows if r['condition']==f'C{condition}']
    axes[0,0].plot([13000,13001],[r['accuracy'] for r in group],marker='o',label=f'C{condition}')
    for r in group:
        a=np.load(root/f"{r['network']}_{r['condition']}.npz")
        axes[0,1].hist(a['final_weights']-a['initial_weights'],bins=30,histtype='step',alpha=.6)
        axes[1,0].plot([20,40,100],[r['delay20'],r['accuracy'],r['delay100']],marker='.',alpha=.5)
axes[0,0].legend();axes[0,0].set(title='Held-out balanced accuracy (pilot)',xlabel='Network',ylim=(0,1))
axes[0,1].set(title='E/E weight changes',xlabel='pA')
axes[0,2].bar([13000,13001],paired);axes[0,2].set(title='Paired C1−C0',ylabel='percentage points')
axes[1,0].set(title='Delay sensitivity',xlabel='Delay ms',ylim=(0,1))
confusion=np.sum([r['confusion'] for r in rows if r['condition']=='C1'],axis=0)
axes[1,1].imshow(confusion);axes[1,1].set(title='C1 test confusion (pooled descriptive)',xlabel='Predicted',ylabel='Actual')
for r in rows:
    ledger=json.loads((root/f"{r['network']}_{r['condition']}.json").read_text())
    correct=np.array([x['correct'] for x in ledger['learning']],float)
    axes[1,2].plot(np.arange(4,33),np.convolve(correct,np.ones(4)/4,mode='valid'),alpha=.4)
axes[1,2].set(title='Training decoder accuracy, 4-trial windows',xlabel='Training trial',ylim=(0,1))
fig.tight_layout();fig.savefig(root/'pilot_diagnostics.png',dpi=150);plt.close(fig)
print(json.dumps({k:v for k,v in summary.items() if k!='rows'}))
