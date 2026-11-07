"""Frozen M002.1 analysis. Run: python this_file.py RAW_DIR NEW_OUTPUT_DIR.
Only training-network outcomes and the preregistered response measure select actions.
"""
from itertools import product
import json
from pathlib import Path
import sys
import time
import numpy as np
from neuromancer.authority_diagnosis import NAMES,GAINS,TARGETS,action_audit

T_CRITICAL={5:2.7764451052,3:4.3026527299}


def t_summary(values):
    values=np.asarray(values,dtype=float)
    n=values.shape[-1]
    mean=values.mean(axis=-1)
    sd=values.std(axis=-1,ddof=1)
    width=T_CRITICAL[n]*sd/np.sqrt(n)
    return dict(mean=mean.tolist(),sd=sd.tolist(),lower=(mean-width).tolist(),upper=(mean+width).tolist(),
                replicates=n,ci='pointwise 95% Student-t')


def hierarchical_ci(values):
    """Resample network and then replicate; keep all metric columns paired."""
    values=np.asarray(values,dtype=float)
    if values.shape[0]!=10 or values.shape[1] not in (3,5):
        raise ValueError('Expected ten networks and three or five noise replicates')
    n_noise=values.shape[1]
    columns=values.shape[2:]
    flat=values.reshape(10,n_noise,-1)
    generator=np.random.default_rng(20261021)
    means=[]
    for _ in range(100):
        network=generator.integers(0,10,(100,10))
        noise=generator.integers(0,n_noise,(100,10,n_noise))
        draw=flat[network[:,:,None],noise,:]
        means.append(draw.mean(axis=(1,2)))
    samples=np.concatenate(means).reshape((10000,)+columns)
    return dict(mean=values.mean(axis=(0,1)).tolist(),
                lower=np.quantile(samples,.025,axis=0).tolist(),
                upper=np.quantile(samples,.975,axis=0).tolist(),
                ci='pointwise hierarchical percentile bootstrap',resamples=10000,seed=20261021,noise_replicates=n_noise)


def global_choice(response):
    """Response shape network,replicate,action; sham is action zero."""
    calibration=response[:,:2,1:].mean(axis=1)
    count=(calibration>=4).sum(axis=0)
    means=calibration.mean(axis=0)
    choice=max(range(7),key=lambda j:(count[j],means[j],-j))+1
    return choice


def selection_analysis(response):
    primary=response[:,:,0,:]
    selected=global_choice(primary)
    fixed=t_summary(np.moveaxis(primary,1,-1))
    fixed['network_pass_counts']=(primary.mean(axis=1)>=4).sum(axis=0).tolist()
    fixed['lower_ci_pass_counts']=(np.asarray(fixed['lower'])>=4).sum(axis=0).tolist()
    evaluated=primary[:,2:,selected]
    global_result=t_summary(evaluated)
    global_result.update(action=NAMES[selected],action_index=selected,
        calibration_rep_ids=[0,1],evaluation_rep_ids=[2,3,4],
        network_pass_count=int((evaluated.mean(axis=1)>=4).sum()),
        lower_ci_pass_count=int((np.asarray(global_result['lower'])>=4).sum()),
        aggregate=hierarchical_ci(evaluated[:,:,None]),
        secondary=t_summary(response[:,2:,1,selected]))
    oracle=np.argmax(primary.mean(axis=1)[:,1:],axis=1)+1
    oracle_value=primary.mean(axis=1)[np.arange(10),oracle]
    split=np.argmax(primary[:,:2,1:].mean(axis=1),axis=1)+1
    split_value=primary[:,2:,:][np.arange(10),:,split]
    assert split_value.shape==(10,3)
    return dict(fixed_primary=fixed,global_strategy=global_result,
        oracle=dict(actions=[NAMES[j] for j in oracle],network_mean_hz=oracle_value.tolist(),
            network_pass_count=int((oracle_value>=4).sum()),
            inference='Hindsight maximum over five-replicate means; selected-action CIs are not confirmatory.'),
        split_network_diagnostic=dict(actions=[NAMES[j] for j in split],
            evaluation=t_summary(split_value),
            network_pass_count=int((split_value.mean(axis=1)>=4).sum()),
            inference='Evaluator-only network-specific calibration choice, not an implemented identification/controller method.'))


def main(raw,output):
    began=time.perf_counter_ns()
    raw=Path(raw);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    complete=json.loads((raw/'summary.json').read_text())
    if complete['status']!='complete' or len(complete['trials'])!=50:
        raise ValueError('Preregistered cohort incomplete; do not silently analyze a subset')
    arrays={}
    provenance=[];ledger=[];trace_sum=None
    for network,replicate in product(range(10),range(5)):
        folder=raw/f'network_{network}_replicate_{replicate}'
        trial=json.loads((folder/'trial.json').read_text())
        if trial['status']!='complete':raise ValueError('Failed trial')
        with np.load(folder/'numerical.npz',allow_pickle=False) as data:
            for key in ['spike_counts','observed_counts','sector_rates_hz','filtered_sector_rates_hz',
                        'delivered_current_pA','stimulation','recording']:
                if key not in arrays:arrays[key]=np.empty((10,5)+data[key].shape,dtype=data[key].dtype)
                arrays[key][network,replicate]=data[key]
            means=data['group_current_trace_pA'].mean(axis=2)
            if 'group_current_mean_pA' not in arrays:
                arrays['group_current_mean_pA']=np.empty((10,5)+means.shape)
            arrays['group_current_mean_pA'][network,replicate]=means
            if trace_sum is None:trace_sum=np.zeros_like(data['group_current_trace_pA'])
            trace_sum+=data['group_current_trace_pA']
        ledger.extend(dict(network_id=network,replicate_id=replicate,**r) for r in trial['receipt_ledger'])
        provenance.append(trial)
    groups=provenance[0]['group_names']
    counts=arrays['spike_counts']
    rates=np.empty((10,5,2,8,7))
    # First five are fixed populations; last two use action-specific memberships.
    population_names=['observed_E','fixed_unstim_E','all_E','all_I','hidden_fixed_unstim_E',
                      'direct_active_E','action_unstim_E']
    for n,r in product(range(10),range(5)):
        recording=arrays['recording'][n,r].reshape(4,5,5)
        observed=recording[:,:4,:].ravel()
        stimulated=arrays['stimulation'][n,r]
        fixed=np.setdiff1d(np.arange(800),stimulated.ravel())
        hidden=np.setdiff1d(fixed,observed)
        members=[observed,fixed,np.arange(800),np.arange(800,1000),hidden]
        for g,a in product(range(2),range(8)):
            for j,m in enumerate(members):rates[n,r,g,a,j]=counts[n,r,g,a,m].mean()/5
            active=stimulated[TARGETS[a]>0].ravel()
            rates[n,r,g,a,5]=counts[n,r,g,a,active].mean()/5 if len(active) else np.nan
            inactive=np.setdiff1d(np.arange(800),active)
            rates[n,r,g,a,6]=counts[n,r,g,a,inactive].mean()/5
    response=rates.copy()
    response[:,:,:,:,:5]-=rates[:,:,:,0:1,:5]
    # Compare action-defined groups with the identical cells in paired sham.
    for n,r,g,a in product(range(10),range(5),range(2),range(8)):
        active=arrays['stimulation'][n,r][TARGETS[a]>0].ravel()
        inactive=np.setdiff1d(np.arange(800),active)
        response[n,r,g,a,5]-=counts[n,r,g,0,active].mean()/5 if len(active) else np.nan
        response[n,r,g,a,6]-=counts[n,r,g,0,inactive].mean()/5
    observed=response[:,:,:,:,0]
    np.testing.assert_allclose(rates[:,:,:,:,0],arrays['sector_rates_hz'].mean(axis=(-1,-2)),rtol=0,atol=1e-12)
    np.testing.assert_array_equal(counts[:,:,0,0],counts[:,:,1,0])
    selection=selection_analysis(observed)
    aggregate=hierarchical_ci(response[:,:,:,:,:5])
    differences=hierarchical_ci(observed-observed[:,:,:,1:2])
    post=arrays['sector_rates_hz'][:,:,:,:,3:,:].mean(axis=(-1,-2))
    post=post-post[:,:,:,0:1].copy()
    current=arrays['group_current_mean_pA']
    current_delta=current-current[:,:,:,0:1,:,:]
    sectors=arrays['sector_rates_hz'].mean(axis=-2)
    sector_delta=sectors-sectors[:,:,:,0:1,:]
    row_records=[]
    for n,r,g,a in product(range(10),range(5),range(2),range(8)):
        row=dict(network_id=n,replicate_id=r,gain=GAINS[g],action=NAMES[a],
            absolute_rate_hz={name:float(rates[n,r,g,a,j]) if np.isfinite(rates[n,r,g,a,j]) else None
                              for j,name in enumerate(population_names)},
            paired_response_hz={name:float(response[n,r,g,a,j]) if np.isfinite(response[n,r,g,a,j]) else None
                               for j,name in enumerate(population_names)},
            observed_sector_response_hz=sector_delta[n,r,g,a].tolist(),
            observed_post_ramp_response_hz=float(post[n,r,g,a]),
            current_delta_pA={label:dict(excitatory=float(current_delta[n,r,g,a,j,0]),
                inhibitory=float(current_delta[n,r,g,a,j,1]),
                total_recurrent=float(current_delta[n,r,g,a,j].sum())) for j,label in enumerate(groups)})
        row_records.append(row)
    summary=dict(action_names=NAMES,gains=GAINS,population_names=population_names,
        selection=selection,aggregate_fixed_population_response=aggregate,
        network_fixed_population_summary=t_summary(np.moveaxis(response[:,:,:,:,:5],1,-1)),
        aggregate_action_specific_population_response=hierarchical_ci(response[:,:,:,1:,5:]),
        network_action_specific_population_summary=t_summary(np.moveaxis(response[:,:,:,1:,5:],1,-1)),
        concentrated_minus_distributed=differences,
        post_ramp_response=hierarchical_ci(post),
        current_groups=groups,current_delta=hierarchical_ci(current_delta),
        sector_response=hierarchical_ci(sector_delta),
        secondary_fixed=t_summary(np.moveaxis(observed[:,:,1,:],1,-1)),
        constraint_violations=sum(x['constraint_violations'] for x in ledger),
        completed_branches=len(ledger),noise_replicates=5,networks=10,
        analysis_wall_ns=time.perf_counter_ns()-began,
        raw_execution_wall_ns=complete['wall_ns'],
        primary_gate='PASS' if (max(selection['fixed_primary']['network_pass_counts'][1:])>=8
                         or selection['global_strategy']['network_pass_count']>=8) else 'FAIL')
    np.savez_compressed(output/'authority_data.npz',**arrays,
        group_current_trace_mean_pA=trace_sum/50,
        rate_hz=rates,response_hz=response,post_ramp_observed_response_hz=post)
    (output/'comparison.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    (output/'outcomes.json').write_text(json.dumps(row_records,indent=2,allow_nan=False)+'\n')
    (output/'delivered_actions.json').write_text(json.dumps(ledger,indent=2,allow_nan=False)+'\n')
    (output/'trial_provenance.json').write_text(json.dumps(provenance,indent=2,allow_nan=False)+'\n')
    print(json.dumps(selection,indent=2))


if __name__=='__main__':main(sys.argv[1],sys.argv[2])
