"""M002.2 adds finite-bank evidence without changing the neural model."""
import numpy as np
import pytest
from neuromancer.reachability import intervention_bank,audit_actions,EXPECTED_EXPOSURE


def test_bank_constraints_and_exact_charge_matches():
    desired,actual=intervention_bank()
    assert actual.shape==desired.shape==(12,300,4)
    for a,rows in enumerate(actual):
        check=audit_actions(rows)
        assert check['constraint_violations']==0
        assert check['total_exposure_pA_s']==pytest.approx(EXPECTED_EXPOSURE[a])
    for dynamic,constant in [(9,3),(10,8),(11,1)]:
        assert actual[dynamic].sum()==pytest.approx(actual[constant].sum())
    np.testing.assert_array_equal(actual[11,8],[0]*4)
    np.testing.assert_array_equal(actual[9,26],[0]*4)
    assert np.allclose(actual[10,3:].sum(axis=-1),240)
    bad=actual[4].copy();bad[0]=60
    assert audit_actions(bad)['constraint_violations']>0
    with pytest.raises(ValueError):audit_actions(np.full((300,4),np.nan))


def analysis_module():
    import importlib.util
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'reports/evidence/m002_2/analyze.py'
    spec=importlib.util.spec_from_file_location('m0022_analysis',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_analysis_noise_hierarchy_and_nontrivial_target_floor():
    a=analysis_module()
    values=np.ones((10,3,2))
    interval=a.hierarchy(values)
    assert interval['mean']==interval['lower']==interval['upper']==[1,1]
    late=np.zeros((10,3,2,12));late[:,:,:,8]=3
    result=a.objective_gate(late,{'filtered100ms':np.ones((10,3)),
                                'epoch1s':np.full((10,3),.2)},np.full((10,3),13.))
    assert result['scales']['filtered100ms']['pass_count']==0
    assert result['scales']['epoch1s']['pass_count']==10
    assert result['selected_scale']=='epoch1s'
    late[:,:,:,8]=1
    result=a.objective_gate(late,{'filtered100ms':np.zeros((10,3)),
                                'epoch1s':np.zeros((10,3))},np.full((10,3),13.))
    assert result['recommendation']=='HOLD'
    assert result['scales']['epoch1s']['component_counts']['minimum_span']==0


def test_readout_holds_out_noise_and_time_metrics_are_causal_bins():
    a=analysis_module()
    raw=np.zeros((10,3,2,12,300));baseline=np.zeros((10,3))
    raw[:,:,:,8]=4
    readout=a.condition_readout(raw,baseline)
    assert np.array(readout['mean'])[:,0].tolist()==[1,1]
    assert readout['calibration_replicate']==5 and readout['evaluation_replicates']==[6,7]
    np.testing.assert_array_equal(np.array(readout['threshold_hz'])[:,:,0],2)
    raw[:,1:,:,8]=100
    changed=a.condition_readout(raw,baseline)
    np.testing.assert_array_equal(changed['threshold_hz'],readout['threshold_hz'])
    assert a.first_run([False,True,True,True])==1
    assert a.first_run([True,True]) is None
    late=np.zeros((10,3,2,12));late[:,:,:,4]=2;late[:,:,:,8]=2
    delta=np.zeros_like(raw);delta[:,:,:,4,4:]=2;delta[:,:,:,8,4:]=2
    records=a.temporal_metrics(delta,late)
    assert records[0]['time_s']==pytest.approx(.1)
    assert records[2]['time_s'] is None


def test_complete_analysis_synthetic_zero_fixture(tmp_path):
    """Software-only data, never published as simulated neural evidence."""
    import json
    from neuromancer.authority_diagnosis import evaluator_groups
    from neuromancer._brian import realization
    from neuromancer import Config
    a=analysis_module();raw=tmp_path/'raw';raw.mkdir()
    _,bank=intervention_bank();groups=evaluator_groups(realization(Config()))
    for n in range(10):
        for rep in (5,6,7):
            folder=raw/f'network_{n}_replicate_{rep}';folder.mkdir()
            parameters=realization(Config(network_id=n))
            np.savez_compressed(folder/'numerical.npz',
                observed_counts=np.zeros((2,12,300,20),dtype=np.int32),
                group_counts=np.zeros((2,12,300,24),dtype=np.int32),
                neuron_counts=np.zeros((2,12,1000),dtype=np.int32),
                filtered_sector_rates_hz=np.zeros((2,12,300,4)),
                baseline_counts=np.zeros((400,20),dtype=np.int32),
                stimulation=parameters['stimulation'],recording=parameters['recording'],
                delivered_current_pA=np.tile(bank,(2,1,1,1)))
            trial=dict(status='complete',network_id=n,replicate_id=rep,
                group_names=list(groups),group_sizes=[len(v) for v in groups.values()],
                receipt_ledger=[dict(constraint_violations=0) for _ in range(24)])
            (folder/'trial.json').write_text(json.dumps(trial))
    (raw/'summary.json').write_text(json.dumps(dict(status='complete',trials=[0]*30,wall_ns=0)))
    output=tmp_path/'analysis';a.main(raw,output)
    result=json.loads((output/'comparison.json').read_text())
    assert result['completed_branches']==720 and result['objective_gate']['recommendation']=='HOLD'
    assert result['objective_gate']['selected_scale'] is None
    assert len((output/'all_trials.csv').read_text().splitlines())==721
    assert len((output/'network_summary.csv').read_text().splitlines())==241
