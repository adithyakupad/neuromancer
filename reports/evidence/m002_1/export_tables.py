"""Flat numerical tables for all networks/replicates; no selection or inference changes."""
import csv
import json
from pathlib import Path
import sys
import numpy as np
from analyze import t_summary


def write_csv(path,rows):
    with path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main(output):
    output=Path(output)
    summary=json.loads((output/'comparison.json').read_text())
    outcomes=json.loads((output/'outcomes.json').read_text())
    ledger=json.loads((output/'delivered_actions.json').read_text())
    audit={(r['network_id'],r['replicate_id'],r['gain'],r['action']):r for r in ledger}
    trial_rows=[]
    for record in outcomes:
        identity={k:record[k] for k in ['network_id','replicate_id','gain','action']}
        row=dict(identity)
        for name,value in record['absolute_rate_hz'].items():row[name+'_absolute_hz']=value
        for name,value in record['paired_response_hz'].items():row[name+'_response_hz']=value
        delivery=audit[tuple(identity.values())]
        for key in ['total_exposure_pA_s','aggregate_injected_charge_pC','effective_drive_exposure_pA_s','constraint_violations']:
            row[key]=delivery[key]
        trial_rows.append(row)
    assert len(trial_rows)==800
    assert all(row['constraint_violations']==0 for row in trial_rows)
    write_csv(output/'all_trials.csv',trial_rows)
    names=summary['action_names'];populations=summary['population_names']
    with np.load(output/'authority_data.npz',allow_pickle=False) as data:
        response=data['response_hz'];current=data['group_current_mean_pA']
        counts=data['spike_counts'];recording=data['recording'];stimulation=data['stimulation']
        current=current-current[:,:,:,0:1,:,:].copy()
    rows=[]
    for n in range(10):
        for g,gain in enumerate(summary['gains']):
            for a,action in enumerate(names):
                row=dict(network_id=n,gain=gain,action=action,noise_replicates=5)
                for j,population in enumerate(populations):
                    values=response[n,:,g,a,j]
                    stats=t_summary(values) if np.all(np.isfinite(values)) else {}
                    for key in ['mean','sd','lower','upper']:row[population+'_'+key+'_hz']=stats.get(key)
                row['authority_mean_ge4']=bool(response[n,:,g,a,0].mean()>=4)
                group=summary['current_groups'].index('observed_E')
                for j,label in [(0,'exc'),(1,'inh'),(None,'total_recurrent')]:
                    values=current[n,:,g,a,group,:]
                    values=values.sum(axis=-1) if j is None else values[:,j]
                    stats=t_summary(values)
                    for key in ['mean','sd','lower','upper']:row[label+'_'+key+'_pA']=stats[key]
                rows.append(row)
    assert len(rows)==160
    assert all(row['noise_replicates']==5 for row in rows)
    write_csv(output/'network_intervention_summary.csv',rows)
    sector_rows=[]
    for item in outcomes:
        n,r=item['network_id'],item['replicate_id']
        g=0 if item['gain']==.6 else 1;a=names.index(item['action'])
        for sector in range(4):
            row={key:item[key] for key in ['network_id','replicate_id','gain','action']}
            row['sector']=sector
            full=np.arange(sector*200,(sector+1)*200)
            members={'observed_E':recording[n,r].reshape(4,5,5)[sector,:4].ravel(),
                'fixed_unstim_E':np.setdiff1d(full,stimulation[n,r].ravel()),
                'all_E':full,'all_I':np.arange(800+sector*50,850+sector*50)}
            for label,ids in members.items():
                row[label+'_absolute_hz']=float(counts[n,r,g,a,ids].mean()/5)
                row[label+'_response_hz']=float((counts[n,r,g,a,ids]-counts[n,r,g,0,ids]).mean()/5)
            assert abs(row['observed_E_response_hz']-item['observed_sector_response_hz'][sector])<1e-12
            sector_rows.append(row)
    assert len(sector_rows)==3200
    write_csv(output/'sector_trials.csv',sector_rows)


if __name__=='__main__':main(sys.argv[1])
