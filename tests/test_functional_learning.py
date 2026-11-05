import numpy as np
from neuromancer.functional_learning import balanced_symbols,schedule,probe_fit,probe_predict,balanced_accuracy


def test_balancing_energy_and_slew():
    symbols = balanced_symbols(16,np.random.default_rng(1))
    assert len(np.unique(symbols,axis=0))==4
    exposures=[]
    for a,b in symbols:
        commands,_=schedule(a,b,40,0,'task')
        assert all(type(value) is float for command in commands for value in command.current_pA)
        inputs=np.array([x.current_pA for x in commands])
        assert np.max(np.abs(np.diff(np.vstack((np.zeros(4),inputs)),axis=0)))<=30
        assert inputs.max()<=120 and inputs.sum(axis=1).max()<=240
        exposures.append(inputs.sum()*.02)
    assert len(set(exposures))==1


def test_readout_no_test_label_argument_and_nonlinear_control():
    symbols=balanced_symbols(16,np.random.default_rng(2))
    nonlinear=np.column_stack((symbols,symbols[:,0]*symbols[:,1]))
    target=np.bitwise_xor(symbols[:,0],symbols[:,1])
    fit=probe_fit(nonlinear,target,nonlinear,target)
    assert balanced_accuracy(target,probe_predict(nonlinear,fit))==1
    before=probe_predict(nonlinear,fit)
    mutated_test_labels=1-target
    np.testing.assert_array_equal(before,probe_predict(nonlinear,fit))
    assert balanced_accuracy(mutated_test_labels,before)==0
