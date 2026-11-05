"""Verify closed-loop causality and archived SDK recordings independently."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import cl
import numpy as np

BASE='69be977c06ff9cef32c90ed01e013103fe273e76'


def read(path):
    return json.loads(path.read_text())


def latency(values):
    return dict(n=len(values),**{f'p{q}_ms':float(np.percentile(values,q)/1e6)
                                 for q in (50,95,99)},max_ms=max(values)/1e6)


def check_case(root,name):
    directory=root/name
    rows=read(directory/'ticks.json')
    callback=[json.loads(line) for line in (directory/'source.jsonl').read_text().splitlines()]
    opened,closed=callback[0],callback[-1]
    assert opened['kind']=='open' and opened['source']=='m016-pulse-v1'
    assert closed==dict(kind='close',pending=0,collisions=0)
    start=rows[0]['start']
    stop=rows[-1]['stop']
    assert len(rows)==16 and stop-start==8000
    committed=[]
    observed=[]
    submissions={}
    submit_time=[]
    observed_latency=[]
    integral=0.
    proposed_error=None
    for index,row in enumerate(rows):
        assert row['index']==index and row['start']==start+index*500 and row['stop']==row['start']+500
        assert row['valid'] and not row['late'] and not row['missing']
        assert row['available']==row['stop']
        spikes=[tuple(event) for event in row['spikes']]
        assert all(row['start']<=frame<row['stop'] and channel==8 for frame,channel in spikes)
        assert row['counts']==[len(spikes)]+[0]*19
        observed.extend(spikes)
        for receipt in row['receipts']:
            request,decision,began=submissions.pop(receipt['request_id'])
            frame=receipt['committed_frame']
            assert receipt['clock']==request['clock'] and receipt['electrode']==decision['electrode']
            assert request['observation_stop']<=frame<request['expires_frame']
            assert frame-decision['submitted_frame']==2
            committed.append((frame,receipt['electrode']))
            observed_latency.append(row['tick_began_ns']-began)
            if name=='PI':
                integral=max(-2.,min(2.,integral+proposed_error))
                proposed_error=None
        decision=row['decision']
        if name=='PI' and index<15:
            error=2-row['counts'][0]
            proposal=error+.2*integral>.5
            assert proposal==bool(decision)
            if proposal:
                proposed_error=error
            else:
                integral=max(-2.,min(2.,integral+error))
        if name=='PI':
            assert row['pi_integral']==integral
        if decision and decision['accepted']:
            request=row['request']
            assert request['observation_stop']==row['stop']
            submissions[decision['request_id']]=(request,decision,row['submit_started_ns'])
            submit_time.append(row['submit_ns'])
    assert not submissions and proposed_error is None
    commits=callback[1:-1]
    assert [(event['frame'],event['electrode']) for event in commits]==committed
    assert all(event['kind']=='commit' and event['intended']==event['frame']
               and event['durations_us']==[160,160] and event['currents_uA']==[-1.,1.]
               for event in commits)
    baseline={(frame,8) for frame in range(start,stop) if frame%500==opened['phase']}
    offsets=(100+opened['extra_delay_frames'],150+opened['extra_delay_frames'],
             200+opened['extra_delay_frames'])
    expected={(frame+delay,8) for frame,electrode in committed for delay in offsets
              if opened['enabled'] and electrode==4 and start<=frame+delay<stop}
    assert observed==sorted(baseline|expected)
    path,=directory.glob('*.h5')
    with cl.RecordingView(str(path)) as recording:
        assert recording.attributes['application']['m016_source']=='m016-pulse-v1'
        assert recording.attributes['frames_per_second']==25000
        assert recording.attributes['uV_per_sample_unit']==.195
        assert recording.samples.shape==(8000,64) and recording.samples.dtype==np.int16
        assert not np.any(recording.samples[:])
        origin=recording.attributes['start_timestamp']
        recorded_spikes=[(int(s['timestamp'])+origin,int(s['channel'])) for s in recording.spikes]
        recorded_stims=[(int(s['timestamp'])+origin,int(s['channel'])) for s in recording.stims]
        assert recorded_spikes==observed and recorded_stims==committed
    result=dict(requests=sum(row['request'] is not None for row in rows),commits=len(committed),
        spike_count=len(observed),additional_spikes=len(expected-baseline),missing_bins=0,
        absolute_tracking_error=float(np.mean([abs(2-row['counts'][0]) for row in rows])),
        frame_range=[start,stop],recording_bytes=path.stat().st_size)
    return result,rows,committed,expected-baseline,submit_time,observed_latency


def verify_preservation():
    count=0
    for row in subprocess.check_output(['git','ls-tree','-rz',BASE]).split(b'\0'):
        if not row:continue
        metadata,name=row.split(b'\t',1)
        path=Path(name.decode())
        contents=os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(contents)).encode()+b'\0'+contents).hexdigest()
        assert blob==metadata.split()[2].decode(),path
        count+=1
    return count


def verify(root):
    cases=('C0','C1','C2','C4','C5','C6','PI','FROZEN','C1_REPEAT')
    results,rows,commits,events,submission_times,observation_times={},{},{},{},[],[]
    for case in cases:
        result,ticks,stims,extra,submit,observed=check_case(root,case)
        results[case],rows[case],commits[case],events[case]=result,ticks,stims,extra
        submission_times.extend(submit)
        observation_times.extend(observed)
    for name in ('C0','C2','C4','C6','FROZEN'):
        assert results[name]['additional_spikes']==0
    for name in ('C1','C1_REPEAT','C2','C4','C5'):
        assert results[name]['commits']==4
    assert results['C1']['additional_spikes']==12 and results['C5']['additional_spikes']==12
    assert all(frame+delay>=frame-frame%500+500 for frame,_ in commits['C5']
               for delay in (800,850,900))
    assert results['C6']['requests']==5 and results['C6']['commits']==0
    rejections=[row['decision']['reason'] for row in rows['C6'] if row['decision']]
    assert rejections==['Unsupported stimulation destination']*4+['Late or mismatched request']
    for name in ('C0','FROZEN'):
        assert results[name]['requests']==0
    assert results['PI']['commits']>0 and results['PI']['additional_spikes']==3*results['PI']['commits']
    start,stop=results['C1']['frame_range']
    relative_receipts=lambda name: [(frame-results[name]['frame_range'][0],electrode)
                                   for frame,electrode in commits[name]]
    assert relative_receipts('C1')==relative_receipts('C1_REPEAT')
    assert [x['counts'] for x in rows['C1']]==[x['counts'] for x in rows['C1_REPEAT']]
    shifts=[start+(frame-start+500)%(stop-start) for frame,_ in commits['C1']]
    shuffled_hits=sum((frame+offset,8) in events['C1'] for frame in shifts for offset in (100,150,200))
    assert shuffled_hits==0
    results['C3']=dict(shifted_frames=shifts,nominal_response_hits=shuffled_hits,unshifted_hits=12)
    rejections_ns=[row['submit_ns'] for row in rows['C6'] if row['decision']]
    cadence=[]
    cadence_jitter=[]
    for group in rows.values():
        intervals=np.diff([row['tick_began_ns'] for row in group])
        cadence.extend(intervals)
        cadence_jitter.extend(np.abs(intervals-np.median(intervals)))
    evidence=read(root.with_name(root.name+'_descendants.json'))
    assert not evidence['timed_out'] and not evidence['forced_cleanup_pids'] and not evidence['remaining']
    supervisor=read(root/'returned.json')
    assert supervisor['status']=='COMPLETED' and supervisor['cleanup_verified']
    assert supervisor['finished_ns']<supervisor['deadline_ns']
    return dict(cases=results,all_paired_receipts=True,reproducible_relative_c1=True,
        application_processing=latency([row['application_ns'] for group in rows.values() for row in group]),
        submit_call=latency(submission_times),rejection_processing=latency(rejections_ns),
        submit_to_observed_commit=latency(observation_times),
        inter_tick_wall=latency(cadence),inter_tick_median_deviation=latency(cadence_jitter),
        sdk_frame_commit_jitter_frames=0,
        response_ms=[4.,6.,8.],delayed_response_ms=[32.,34.,36.],
        measured_supervised_s=(supervisor['finished_ns']-supervisor['started_ns'])/1e9,
        sampled_peak_tree_rss_bytes=evidence['sampled_peak_tree_rss_bytes'],
        cpu_s_parent_sum=sum(read(root/name/'summary.json')['cpu_s'] for name in cases),
        recording_bytes=sum(results[name]['recording_bytes'] for name in cases),
        preserved_base_paths=verify_preservation())


if __name__=='__main__':
    root=Path(sys.argv[1])
    result=verify(root)
    root.with_name(root.name+'_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
