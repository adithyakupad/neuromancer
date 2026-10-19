"""Descriptive report tables from frozen analysis; never changes qualification."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from analyze import ci,network_bootstrap,save,csv_write


def main(output):
    output=Path(output);trials=json.loads((output/'trial_provenance.json').read_text())
    assert len(trials)==50
    with np.load(output/'calibration_data.npz',allow_pickle=False) as archive:
        rates=archive['raw_rate_hz'];prefix=archive['prefix_counts']
    late=rates[:,:,:,:,50:].mean(axis=-1);response=late-late[:,:,:,0,None]
    maps=[];lookups=[]
    for n in range(10):
        selected=[t for t in trials if t['network_id']==n];assert len(selected)==5
        maps.append(ci([t['calibration']['h_hz'] for t in selected]))
        lookups.append(ci([t['calibration']['lookup_pA'] or [np.nan,np.nan] for t in selected]))
    allbranches=[b for t in trials for b in t['receipt_ledger']];assert len(allbranches)==400
    init=np.array([t['engine']['initialization_ns']/1e6 for t in trials])
    worker=np.array([t['total_wall_ns']/1e9 for t in trials])
    targets=np.array([[t['calibration']['targets_hz'] for t in trials if t['network_id']==n] for n in range(10)])
    spans=np.array([[t['calibration']['span_hz'] for t in trials if t['network_id']==n] for n in range(10)])
    error=late[:,:,:,2:]-targets[:,:,None,:]
    normalized=np.divide(np.abs(error),spans[:,:,None,None],out=np.full_like(error,np.nan),where=spans[:,:,None,None]>0)
    sham_error=np.abs(late[:,:,:,0,None]-targets[:,:,None,:])/spans[:,:,None,None]
    maximum_error=np.abs(late[:,:,:,1,None]-targets[:,:,None,:])/spans[:,:,None,None]
    rows=[]
    for n in range(10):
        selected=[t for t in trials if t['network_id']==n]
        for r,t in enumerate(selected):
            for gi,gain in enumerate((1.,.6)):
                for ti,target in enumerate(('L','H')):
                    rows.append(dict(network_id=n,replicate_id=t['replicate_id'],gain=gain,target=target,
                        calibration_valid=t['calibration']['valid'],safe_fallback=not t['calibration']['valid'],
                        target_hz=targets[n,r,ti],actual_late_hz=late[n,r,gi,ti+2],signed_error_hz=error[n,r,gi,ti],
                        normalized_actual_error=normalized[n,r,gi,ti]))
    assert len(rows)==200
    csv_write(output/'all_realization_errors.csv',rows)
    result=dict(paired_late_response_hz=network_bootstrap(response.mean(axis=1)),
        network_paired_late_response_hz=[ci(response[n]) for n in range(10)],
        calibration_h_hz=maps,lookup_pA=lookups,
        fallback_inclusive_normalized_error=[ci(normalized[n]) for n in range(10)],
        fallback_inclusive_aggregate_normalized_error=network_bootstrap(normalized.mean(axis=1)),
        sham_normalized_error=network_bootstrap(sham_error.mean(axis=1)),
        maximum_reference_normalized_error=network_bootstrap(maximum_error.mean(axis=1)),
        calibration_prefix_nominal_exposure_pA_s=2400,
        confirmation_exposure_pA_s=sum(b['total_exposure_pA_s'] for b in allbranches),
        confirmation_effective_exposure_pA_s=sum(b['effective_exposure_pA_s'] for b in allbranches),
        confirmation_model_charge_pC=sum(b['aggregate_injected_charge_pC'] for b in allbranches),
        prefix_worker_wall_s=sum(t['prefix_wall_ns'] for t in trials)/1e9,
        confirmation_worker_wall_s=sum(b['simulation_call_ns'] for b in allbranches)/1e9,
        initialization_ms=dict(minimum=init.min(),median=np.median(init),maximum=init.max()),
        trial_worker_wall_s=dict(minimum=worker.min(),median=np.median(worker),maximum=worker.max()),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    save(output/'report_statistics.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main(*sys.argv[1:])
