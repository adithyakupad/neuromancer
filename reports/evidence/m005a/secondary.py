"""Descriptive costs, timing, recovery and excitation; no gate changes."""
import argparse,json,csv
from pathlib import Path
import numpy as np


def stats(x):
    return dict(min=float(np.min(x)),median=float(np.median(x)),p95=float(np.quantile(x,.95)),max=float(np.max(x)))


def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('analysis',type=Path);a=p.parse_args()
    s=json.loads((a.analysis/'summary.json').read_text());selected=s['selected'];entries=[];times={};init=[];rss=[];walls=[];cal=[];reversals=[]
    for folder in sorted(a.raw.glob('n*_r*')):
        m=json.loads((folder/'trial.json').read_text());c=m['calibration'];init.append(m['engine']['initialization_ns']/1e9);rss.append(m['peak_rss_bytes']);walls.append(m['wall_ns']/1e9)
        cal.append(dict(network=m['network_id'],replicate=m['replicate_id'],**c));reversals.append(int((np.diff(c['h_hz'])<0).sum()))
        for b in m['branches']:
            name=b['controller'];d=dict(np.load(folder/f"{b['condition']}_{name}.npz"));t=d['timings_ns']
            times.setdefault(name,[]).extend((t[:,:2].sum(axis=1)/1e6).tolist())
            if name!=selected:continue
            raw=d['counts'].reshape(1600,4,5)[:,:,:4].sum(axis=(1,2)).reshape(32,50).sum(axis=1)/80.
            e=raw-c['target_hz'];hits=[k for k in range(16,30) if (abs(e[k:k+3])<=.35).all()]
            first=(hits[0]+1-16) if hits else None;confirmed=(first+2) if first is not None else None
            u=d['delivered'];entries.append(dict(network=m['network_id'],replicate=m['replicate_id'],condition=b['condition'],
                first_recovery_endpoint_s=first,causal_recovery_confirmation_s=confirmed,miss=first is None,
                online_charge_pC=float(u.sum()*.02*50),total_charge_pC=float((u.sum()*.02+m['prefix_audit']['exposure_pA_s'])*50),
                q_mean_pA=float(u[:,0].mean()),saturation_fraction=float(d['decisions'][:,5].mean()),
                integral_blocked_fraction=float(d['decisions'][:,4].mean()),fallback_decisions=int(d['decisions'][:,6].sum()),
                filtered_mae_hz=float(abs(d['rates'].mean(axis=1)[1000:]-c['target_hz']).mean())))
    designs=json.loads((a.analysis/'excitation.json').read_text());excitation={}
    for name in s['models']:
        rows=[r for r in designs if r['controller']==name and r['condition']=='LOSS' and r['window']=='last16']
        excitation[name]=dict(ranks=[r['rank'] for r in rows],q_sd_pA=stats([r['per_channel_sd_pA'][0] for r in rows]),positive_condition=stats([r['positive_condition'] for r in rows]),changed_ticks=stats([r['changed_ticks'] for r in rows]))
    report=dict(calibrations=cal,adjacent_reversals=sum(reversals),invalid_calibrations=sum(not r['valid'] for r in cal),
                policy_outcomes=entries,planning_plus_aggregation_ms={k:stats(v) for k,v in times.items()},
                initialization_s=stats(init),trial_wall_s=stats(walls),worker_peak_rss_bytes=stats(rss),excitation=excitation,
                interpretation='descriptive; no held-out-network claim; saturation/conditioning not persistent-excitation proof')
    (a.analysis/'secondary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
