"""Independent M015 checks and figures from saved observations only."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import os

import numpy as np
from scipy.linalg import solve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = '9cde9c24d0e2db4c76d70741b4427c1d77962453'
NETWORKS = (15000,15001)
CONDITIONS = ('C0','C1','C2')


def load(path):
    return json.loads(path.read_text())


def accuracy(labels,scores):
    return float(sum(np.mean((scores[labels==label]>=.5)==label) for label in (0,1))/2)


def reconstruct_probe(matrices,labels,artifact,metrics):
    fit,validation,test = matrices
    mean=fit.mean(axis=0)
    scale=fit.std(axis=0)
    scale[scale==0]=1
    design,validation_design,test_design = [
        np.column_stack((np.ones(len(matrix)),(matrix-mean)/scale)) for matrix in matrices]
    coefficients=[]
    validation_scores=[]
    for alpha in (.1,1.,10.):
        beta=solve(design.T@design+alpha*np.eye(design.shape[1]),
                   design.T@labels[0],assume_a='pos')
        coefficients.append(beta)
        validation_scores.append(accuracy(labels[1],validation_design@beta))
    index=int(np.argmax(validation_scores))
    assert metrics['alpha_index']==index and metrics['validation_scores']==validation_scores
    np.testing.assert_allclose(artifact['coefficients'],coefficients[index],rtol=0,atol=1e-12)
    scores=test_design@coefficients[index]
    np.testing.assert_allclose(scores,artifact['predictions'],rtol=0,atol=1e-12)
    assert accuracy(labels[2],scores)==metrics['accuracy']
    for name,matrix in zip(('fit','validation','test'),(fit,validation,test),strict=True):
        np.testing.assert_array_equal(artifact[name],matrix)


def trial_counts(raw, *, sham=False):
    counts=np.asarray(raw['counts'])
    currents=np.asarray(raw['delivered'])
    np.testing.assert_array_equal(currents,raw['requested'])
    assert np.max(currents)<=120 and np.min(currents)>=0 and currents.sum(axis=1).max()<=240
    assert np.abs(np.diff(np.vstack((np.zeros(4),currents)),axis=0)).max()<=30
    assert np.isclose(currents.sum()*.02,0 if sham else 2.4)
    np.testing.assert_array_equal(raw['start_us'],np.arange(4)*20000)
    np.testing.assert_array_equal(raw['available_us'],np.arange(1,5)*20000)
    assert counts.shape==(4,20) and np.all(counts>=0)
    return counts


def verify_access(output):
    stage=output/'access'
    summary=load(stage/'summary.json')
    verified=0
    for network in NETWORKS:
        for condition in CONDITIONS:
            prefix=f'{network}_{condition}_D80'
            matrices=[]
            labels=[]
            for split,size in [('fit',16),('validation',8),('test',16)]:
                data=load(stage/f'{prefix}_{split}_raw.json')
                pairs=np.asarray(data['symbols'])
                np.testing.assert_array_equal(np.unique(pairs,axis=0,return_counts=True)[1],[size//4]*4)
                reference=load(stage/f'{network}_C0_D80_{split}_raw.json')
                assert reference['symbols']==data['symbols']
                sham=[]
                features=[]
                for trial,paired in zip(data['trials'],reference['trials'],strict=True):
                    assert trial['noise_hashes']==paired['noise_hashes']
                    assert trial['noise_id']==paired['noise_id']
                    assert trial['delivered']==paired['delivered']
                    counts=trial_counts(trial)
                    features.append(counts[-2:].sum(axis=0)/.2)
                    verified+=1
                    if split=='test':
                        assert trial['sham']['noise_hashes']==trial['noise_hashes']
                        sham_counts=trial_counts(trial['sham'],sham=True)
                        sham.append(sham_counts[-2:].sum(axis=0)/.2)
                        verified+=1
                        if condition=='C1':
                            np.testing.assert_array_equal(counts,sham_counts)
                matrices.append(np.asarray(features))
                labels.append(pairs[:,0])
            metrics=summary['networks'][str(network)][condition]['80']['cue']
            reconstruct_probe(matrices,labels,np.load(stage/f'{prefix}_cue.npz'),metrics)
            np.testing.assert_allclose(metrics['rate_hz'],matrices[-1].mean(),rtol=0,atol=1e-12)
            difference=matrices[-1]-np.asarray(sham)
            measured=[np.sqrt(np.mean(difference[labels[-1]==value].mean(axis=0)**2))
                      for value in (0,1)]
            np.testing.assert_allclose(measured,metrics['evoked_rms_hz'],rtol=0,atol=1e-12)
        graph={c:np.load(stage/f'{network}_{c}_graph.npz') for c in CONDITIONS}
        original,dag=graph['C0'],graph['C2']
        assert not len(graph['C1']['edges'])
        assert set(map(tuple,dag['edges'])).issubset(set(map(tuple,original['edges'])))
        for membership in ('stimulation','recording'):
            np.testing.assert_array_equal(original[membership],dag[membership])
        assert not set(dag['stimulation'].ravel())&set(dag['recording'].ravel())
        # Independent graph traversal. Topological processing exhausts all nodes only in a DAG.
        neighbors=[[] for _ in range(1000)]
        indegree=np.zeros(1000,dtype=int)
        for pre,post in dag['edges'][:,:2].astype(int):
            neighbors[pre].append(post)
            indegree[post]+=1
        ready=list(np.flatnonzero(indegree==0))
        visited=0
        while ready:
            cell=ready.pop()
            visited+=1
            for target in neighbors[cell]:
                indegree[target]-=1
                if indegree[target]==0:
                    ready.append(target)
        assert visited==1000
        for sources in dag['stimulation']:
            reached=set(sources)
            frontier=set(sources)
            while frontier:
                frontier={target for source in frontier for target in neighbors[source]}-reached
                reached.update(frontier)
            assert set(dag['recording'].ravel()).issubset(reached)
    assert verified==336
    return summary,verified


def verify_history():
    count=0
    for row in subprocess.check_output(['git','ls-tree','-rz',BASE]).split(b'\0'):
        if not row:
            continue
        metadata,name=row.split(b'\t',1)
        path=Path(name.decode())
        contents=os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(contents)).encode()+b'\0'+contents).hexdigest()
        assert blob==metadata.split()[2].decode(),path
        count+=1
    return count


def plot_access(output,summary):
    figure,axes=plt.subplots(1,3,figsize=(12,3.5))
    x=np.arange(2)
    for index,condition in enumerate(CONDITIONS):
        rows=[summary['networks'][str(network)][condition]['80']['cue'] for network in NETWORKS]
        offset=(index-1)*.23
        axes[0].bar(x+offset,[row['accuracy']*100 for row in rows],.23,label=condition)
        axes[1].bar(x+offset,[row['rate_hz'] for row in rows],.23,label=condition)
        axes[2].bar(x+offset,[min(row['evoked_rms_hz']) for row in rows],.23,label=condition)
    axes[0].axhline(68.75,color='black',linestyle=':',label='Cue gate')
    axes[0].set(ylim=(0,100),ylabel='Balanced accuracy (%)',title='Cue-end decoding')
    axes[1].set(ylabel='Mean recorded rate (Hz)',title='Recorded activity')
    axes[2].axhline(1,color='black',linestyle=':')
    axes[2].set(ylabel='Minimum class RMS (Hz)',title='Paired cue minus sham')
    for axis in axes:
        axis.set(xticks=x,xticklabels=NETWORKS,xlabel='Development network')
    axes[0].legend(fontsize=8)
    figure.tight_layout()
    figure.savefig(output/'cue_access.png',dpi=160)
    plt.close(figure)

    figure,axis=plt.subplots(figsize=(10,3))
    labels=['Stimulated E','Unrecorded E','Unrecorded I','Recorded E/I']
    dag=np.load(output/'access'/'15000_C2_graph.npz')
    membership=np.where(np.arange(1000)<800,1,2)
    membership[dag['stimulation'].ravel()]=0
    membership[dag['recording'].ravel()]=3
    pre,post=dag['edges'][:,:2].astype(int).T
    for index,label in enumerate(labels):
        axis.text(index,0,label,ha='center',bbox={'boxstyle':'round','facecolor':'white'},zorder=2)
        for target in range(index+1,4):
            count=np.sum((membership[pre]==index)&(membership[post]==target))
            if count:
                height=.22*(target-index)
                axis.annotate('',xy=(target-.21,.03),xytext=(index+.21,.03),
                              arrowprops=dict(arrowstyle='->',connectionstyle=f'arc3,rad={-height}'))
                axis.text((index+target)/2,height*(target-index)*.56,str(count),ha='center')
    axis.set(xlim=(-.5,3.5),ylim=(-.2,1.5),title='Effective C2 edge counts by layer, network 15000')
    axis.axis('off')
    figure.tight_layout()
    figure.savefig(output/'connectivity.png',dpi=160)
    plt.close(figure)


def verify_cross(output):
    directory=output/'cross'
    summary=load(directory/'summary.json')
    assert len(summary['rows'])==8
    maximum_error=0.
    figure,axes=plt.subplots(2,2,figsize=(10,6),sharex=True)
    for axis,case in zip(axes.ravel(),('deterministic','ou_15500','ou_15501','ou_15502'),strict=True):
        conditions=[]
        for stimulated in (0,1):
            artifact=np.load(directory/f'{case}_{stimulated}.npz')
            counts=[]
            for engine in ('reference','brian'):
                spikes=artifact[f'{engine}_spikes']
                cell_counts=np.stack([np.histogram(spikes[spikes[:,1]==cell,0],
                    bins=np.arange(11)*200)[0] for cell in range(3)],axis=1)
                np.testing.assert_array_equal(cell_counts,artifact[f'{engine}_counts'])
                counts.append(cell_counts)
            np.testing.assert_array_equal(counts[0],counts[1])
            maximum_error=max(maximum_error,float(np.max(np.abs(
                artifact['reference_current']-artifact['brian_current']))))
            conditions.append((artifact['drive'],counts))
        delta=conditions[1][0]-conditions[0][0]
        expected=np.zeros_like(delta)
        expected[400:1000,0]=100.
        np.testing.assert_allclose(delta,expected,rtol=0,atol=1e-12)
        for index,name in enumerate(('Scalar','Brian2')):
            change=conditions[1][1][index]-conditions[0][1][index]
            axis.plot(np.arange(10)*20+10,change.sum(axis=1),
                      marker='o' if index==0 else 'x',linestyle='-' if index==0 else ':',label=name)
        axis.axvspan(40,100,alpha=.09)
        axis.set(title=case,xlabel='Bin midpoint (ms)',ylabel='Evoked spike count')
    assert maximum_error<=1e-8
    assert summary['status']=='QUALIFIED'
    axes[0,0].legend()
    figure.tight_layout()
    figure.savefig(output/'cross_simulator.png',dpi=160)
    plt.close(figure)
    return dict(archives_verified=8,max_current_error_pA=maximum_error)


if __name__=='__main__':
    output=Path(sys.argv[1])
    summary,trials=verify_access(output)
    old_count=verify_history()
    plot_access(output,summary)
    (output/'verification.json').write_text(json.dumps(dict(verified_trajectories=trials,
        preserved_base_paths=old_count,paired_noise=True,independent_dag_check=True,
        independent_readout=True,gate=summary['gate'],cross=verify_cross(output)),indent=2)+'\n')
