from dataclasses import fields
import numpy as np
import pytest
from neuromancer.reservoir import symbols,commands_for_trial,features,reset_trial,set_recurrence,representation_diagnostics
from neuromancer.substrate import Config


def test_task_balance_independence_energy_constraints():
    for delay in [20,40,80,160]:
        values=symbols(14000,0,0,16)
        unique,counts=np.unique(values,axis=0,return_counts=True)
        np.testing.assert_array_equal(counts,[4]*4)
        energies=[]
        for cue,distractor in unique:
            commands=commands_for_trial(cue,distractor,delay,'test')
            inputs=np.array([x.current_pA for x in commands])
            assert all(type(v) is float for x in commands for v in x.current_pA)
            assert np.max(np.abs(np.diff(np.vstack((np.zeros(4),inputs)),axis=0)))<=30
            assert inputs.min()>=0 and inputs.max()<=120 and inputs.sum(axis=1).max()<=240
            np.testing.assert_array_equal(inputs[-2:],np.zeros((2,4)))
            energies.append(inputs.sum()*.02)
        np.testing.assert_array_equal(energies,[4.8]*4)


def test_recurrence_ablation_and_reset_replay():
    from neuromancer._brian import BrianEngine
    engine=BrianEngine(Config(network_id=14000,replicate_id=140000,root_seed=20261105,trial_id='test'))
    commands=commands_for_trial(0,1,20,'test')
    weights=[np.array(s.weight[:]) for s in engine.synapses]
    try:
        reset_trial(engine,140000,False)
        assert not any(s.active for s in engine.synapses)
        actual=engine.run_commands(commands)
        reset_trial(engine,140000,False)
        replay=engine.run_commands(commands)
        for left,right in zip(actual,replay):
            for field in fields(left.observation):
                np.testing.assert_array_equal(getattr(left.observation,field.name),getattr(right.observation,field.name))
        for index,synapse in enumerate(engine.synapses):
            np.testing.assert_array_equal(synapse.weight[:],weights[index])
        set_recurrence(engine,True)
        assert all(s.active for s in engine.synapses)
        final,history=features(actual,commands[-1].start_us+20000)
        assert final.shape==(20,) and history.shape==(80,)
        with pytest.raises(ValueError):features(actual,20000)
    finally:engine.close()


def test_representation_zero_dimension():
    assert representation_diagnostics(np.zeros((8,20)))['effective_dimension']==0


def test_readout_label_isolation_and_history_baselines():
    from neuromancer.reservoir import score_readout
    from neuromancer.functional_learning import balanced_accuracy
    inputs=symbols(14000,0,1,16)
    labels=inputs[:,0]
    _,prediction=score_readout(inputs,inputs,inputs,labels,labels)
    assert balanced_accuracy(labels,prediction)==1
    _,zero_prediction=score_readout(np.zeros((16,4)),np.zeros((16,4)),np.zeros((16,4)),labels,labels)
    assert balanced_accuracy(labels,zero_prediction)==.5
    mutated_test_labels=1-labels
    _,unchanged=score_readout(inputs,inputs,inputs,labels,labels)
    np.testing.assert_array_equal(prediction,unchanged)
    assert balanced_accuracy(mutated_test_labels,prediction)==0
