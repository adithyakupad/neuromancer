"""Independent M014 artifact scoring and constraint/provenance reconciliation."""
import json
from pathlib import Path
import sys
import numpy as np
from scipy.stats import t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(sys.argv[1])
results=json.loads((root/'results.json').read_text())
assert len(results)==16
assert {(r["network"],r["condition"],r["delay_ms"]) for r in results} == {(n,c,d) for n in [14000,14001] for c in ["C0","C1"] for d in [20,40,80,160]}
primary=[]
verified_files=0
for entry in results:
    prefix=f"{entry['network']}_{entry['condition']}_D{entry['delay_ms']}"
    for model in entry['models']:
        archive=np.load(root/f"{prefix}_{model['model']}.npz")
        truth=archive['test_labels']
        prediction=archive['predictions']>=.5
        score=np.mean([np.mean(prediction[truth==label]==label) for label in [0,1]])
        assert score==model['accuracy']
        design=np.column_stack((np.ones(len(archive['test'])),
                                 (archive['test']-archive['mean'])/archive['scale']))
        np.testing.assert_allclose(design@archive['coefficients'],archive['predictions'],rtol=0,atol=0)
        # Scaling must use fit observations only, including constant-feature handling.
        np.testing.assert_array_equal(archive['fit'].mean(axis=0),archive['mean'])
        verified_files+=1
    exposures=[]
    for split,size in [('fit',16),('validation',8),('test',16)]:
        archive=np.load(root/f'{prefix}_{split}_features.npz')
        unique,counts=np.unique(archive['symbols'],axis=0,return_counts=True)
        np.testing.assert_array_equal(counts,[size//4]*4)
        records=json.loads((root/f'{prefix}_{split}_records.json').read_text())
        assert len(records)==size
        for record in records:
            currents=np.array(record['delivered'])
            np.testing.assert_array_equal(currents,record['requested'])
            assert currents.min()>=0 and currents.max()<=120 and currents.sum(axis=1).max()<=240
            assert np.abs(np.diff(np.vstack((np.zeros(4),currents)),axis=0)).max()<=30
            np.testing.assert_array_equal(record['start_us'],np.arange(len(currents))*20000)
            np.testing.assert_array_equal(record['available_us'],(np.arange(len(currents))+1)*20000)
            np.testing.assert_array_equal(currents[-2:],np.zeros((2,4)))
            exposures.append(float(currents.sum()*.02))
        counts=np.array([record['counts'] for record in records])
        independently_final=counts[:,-2:,:].sum(axis=1)/(.04*5)
        np.testing.assert_array_equal(independently_final,archive['final'])
        independent_history=(counts[:,-4:,:]/(.02*5)).reshape(size,80)
        np.testing.assert_array_equal(independent_history,archive['history'])
        np.testing.assert_array_equal(counts[:,2:4,:].sum(axis=1)/(.04*5),archive['cue_end'])
        second_end=8+entry['delay_ms']//20
        np.testing.assert_array_equal(counts[:,second_end-2:second_end,:].sum(axis=1)/(.04*5),archive['distractor_end'])
    assert set(exposures)=={4.8}
    if entry['condition']=='C0':
        other_prefix=prefix.replace('_C0_','_C1_')
        for split in ['fit','validation','test']:
            recurrent=json.loads((root/f'{prefix}_{split}_records.json').read_text())
            disconnected=json.loads((root/f'{other_prefix}_{split}_records.json').read_text())
            for left,right in zip(recurrent,disconnected,strict=True):
                assert left['noise_id']==right['noise_id']
                assert left['noise_hashes']==right['noise_hashes']
                assert left['delivered']==right['delivered']
        other=next(x for x in results if x['network']==entry['network'] and x['condition']=='C1' and x['delay_ms']==entry['delay_ms'])
        assert entry['provenance']['metadata']['parameter_hashes']==other['provenance']['metadata']['parameter_hashes']
    if entry['delay_ms']==80:
        primary.append(dict(network=entry['network'],condition=entry['condition'],
                            accuracy=next(m['accuracy'] for m in entry['models'] if m['model']=='final')))
lag_archives_verified = 0
for network in [14000,14001]:
    recurrent_inputs = np.load(root/f'{network}_C0_binary_stream.npz')['inputs']
    for condition in ['C0','C1']:
        stream = np.load(root/f'{network}_{condition}_binary_stream.npz')
        np.testing.assert_array_equal(stream['inputs'], recurrent_inputs)
        for lag in [1,2,4,8]:
            archive = np.load(root/f'{network}_{condition}_lag{lag}.npz')
            target = stream['inputs'][np.arange(16,256)-lag]
            np.testing.assert_array_equal(archive['test_labels'],target[176:])
            np.testing.assert_array_equal(archive['test'],stream['features'][192:256])
            design = np.column_stack((np.ones(64),(archive['test']-archive['mean'])/archive['scale']))
            np.testing.assert_array_equal(design@archive['coefficients'],archive['predictions'])
            lag_archives_verified += 1
paired=np.array([next(x['accuracy'] for x in primary if x['network']==n and x['condition']=='C0')-
                 next(x['accuracy'] for x in primary if x['network']==n and x['condition']=='C1') for n in [14000,14001]])*100
mean=float(paired.mean())
margin=float(t.ppf(.975,1)*paired.std(ddof=1)/np.sqrt(2))
summary=dict(primary=primary,effect_pp=mean,network_effects_pp=paired.tolist(),
    descriptive_t95_pp=[mean-margin,mean+margin],prediction_archives_verified=verified_files,lag_archives_verified=lag_archives_verified,
    gate=bool(mean>=5 and mean-margin>0),scientific_decision='INCONCLUSIVE PILOT; confirmation NOT RUN')
(root/'independent_analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axes=plt.subplots(2,3,figsize=(12,7))
for network in [14000,14001]:
    for condition in ['C0','C1']:
        values=sorted([x for x in results if x['network']==network and x['condition']==condition],key=lambda x:x['delay_ms'])
        for model,axis in [('final',axes[0,0]),('history',axes[0,1])]:
            axis.plot([x['delay_ms'] for x in values],
                      [next(m['accuracy'] for m in x['models'] if m['model']==model) for x in values],
                      marker='o',label=f'{network} {condition}')
        at80=next(x for x in values if x['delay_ms']==80)
        axes[0,2].plot([0,1,2],[next(m['accuracy'] for m in at80['models'] if m['model']==name)
                                  for name in ['cue_end','distractor_end','final']],marker='o',label=f'{network} {condition}')
        axes[1,0].scatter(at80['representation']['effective_dimension'],
                         next(m['accuracy'] for m in at80['models'] if m['model']=='final'))
        axes[1,1].plot(np.arange(20),at80['activity_mean_hz'],label=f'{network} {condition}')
        lags=json.loads((root/f'{network}_{condition}_lag_results.json').read_text())
        axes[1,2].plot([1,2,4,8],[x['accuracy'] for x in lags],marker='o',label=f'{network} {condition}')
for axis in [axes[0,0],axes[0,1],axes[0,2],axes[1,2]]:
    axis.axhline(.5,color='gray',ls=':');axis.set_ylim(0,1)
axes[0,0].set(title='Primary final-window representation',xlabel='Delay ms',ylabel='Balanced accuracy')
axes[0,1].set(title='Secondary 80ms history',xlabel='Delay ms')
axes[0,2].set(title='Cue decodability by task time',xticks=[0,1,2],xticklabels=['Cue','Distractor','Final'])
axes[1,0].set(title='Dimension versus recall',xlabel='Effective dimension',ylabel='Accuracy')
axes[1,1].set(title='Recorded activity, D80',xlabel='Recording channel',ylabel='Mean Hz')
axes[1,2].set(title='Binary lag decoding (not classical MC)',xlabel='Lag bins')
axes[0,0].legend(fontsize=7)
fig.tight_layout();fig.savefig(root/'reservoir_diagnostics.png',dpi=150);plt.close(fig)
print(json.dumps(summary))
