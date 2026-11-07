"""Independent audit of complete but nonqualifying TUNE records; no selection."""
import argparse,csv,hashlib,json,time
from pathlib import Path
import numpy as np
from verify import inspect_public,calibration,policy_replay,close,score
from neuromancer._brian import realization,digest,innovations
from neuromancer.substrate import Config


def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('analysis',type=Path);p.add_argument('output',type=Path);a=p.parse_args();started=time.perf_counter();branches=0;checks={};peaks=[]
    for folder in sorted(a.raw.glob('n*_r*')):
        m=json.loads((folder/'trial.json').read_text());assert m['status']=='complete';n,r=m['network_id'],m['replicate_id'];assert n in range(10) and r==40
        cfg=Config(network_id=n,replicate_id=r);params=realization(cfg)
        assert {k:digest(v) for k,v in params.items()}==m['engine']['metadata']['parameter_hashes'];assert not np.intersect1d(params['recording'],params['stimulation']).size
        pre,raw=inspect_public(folder/'prefix.npz',0,2550);calibration(pre,raw,m['calibration']);cached={};noise=None
        for b in m['branches']:
            condition,name=b['condition'],b['controller'];d,y=inspect_public(folder/f'{condition}_{name}.npz',51000000,1600,pre['rates'][-1])
            policy_replay(d,y,m['calibration'],name);cached[condition,name]=d;branches+=1
            assert b['audit']['violations']==0;close(d['delivered'].sum()*.02,b['audit']['exposure_pA_s'])
            if noise is None:
                noise=b['noise'];assert len(noise)==83
                for block in (51,67):
                    effective,fine=innovations(cfg,block);assert noise[str(block)]==dict(fine=fine,effective=digest(effective))
            else:assert b['noise']==noise
            for window,(x,z) in {'full':(0,32),'stationary':(8,32),'pre':(8,16),'immediate':(16,20),'late':(20,32)}.items():checks[n,r,condition,name,window]=score(y,m['calibration']['target_hz'],x,z)
        for name in ('ZERO','FIXED','MAX','PI10_5','PI20_10','PI30_15'):
            for field in ('counts','rates','sector','delivered','intent'):close(cached['STATIC',name][field][:800],cached['LOSS',name][field][:800])
            close(cached['STATIC',name]['decisions'][:17],cached['LOSS',name]['decisions'][:17])
        for field in ('counts','rates','sector','delivered','intent'):close(cached['STATIC','ZERO'][field],cached['LOSS','ZERO'][field])
        peaks.append(m['peak_rss_bytes'])
    rows=list(csv.DictReader((a.analysis/'metrics.csv').open()));assert len(rows)==len(checks)==600
    for r in rows:
        key=(int(r['network']),int(r['replicate']),r['condition'],r['controller'],r['window'])
        close(checks[key],[float(r[k]) for k in ('mae_hz','bias_hz','rmse_hz','rate_hz')])
    h=json.loads(Path('reports/evidence/m005a/preservation.json').read_text())['historical_sha256']
    for f,d in h.items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==d
    prov=json.loads((a.raw/'provenance.json').read_text());summary=json.loads((a.raw/'summary.json').read_text())
    clock=json.loads(Path('reports/evidence/m005a/acquisition_clock_evidence.json').read_text())
    for name,item in clock.items():assert hashlib.sha256((a.raw/name).read_bytes()).hexdigest()==item['sha256']
    epoch_elapsed=clock['summary.json']['mtime_epoch_s']-clock['provenance.json']['mtime_epoch_s']
    assert epoch_elapsed>3600 and summary['wall_ns']/1e9<3600
    assert not Path('runs/m005a-confirm-01').exists()
    result=dict(status='PASS_TECHNICAL_AUDIT_ONLY',qualification='PARTIAL_RESOURCE_CAP; no confirmation or PIselection',trials=10,branches=branches,
        observation_bins=217500,metric_rows=len(rows),historical_unchanged=len(h),simulated_seconds=4350,
        internal_elapsed_s=summary['wall_ns']/1e9,file_timestamp_elapsed_s=epoch_elapsed,wall_limit_s=3600,
        maximum_worker_peak_rss_bytes=max(peaks),source_revision=prov['head'],wall_s=time.perf_counter()-started)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':main()
