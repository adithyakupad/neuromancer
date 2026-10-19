"""M003 analytical/software fixtures, never reported as neural research results."""
import inspect
import numpy as np
import pytest
from neuromancer.identify import fit,features,qualification,Predictor,FIT,GRID,window_errors
from neuromancer.identification_experiment import schedules,audit,bank
from neuromancer.substrate import Config


def linear_data():
    rng=np.random.default_rng(811);u=rng.uniform(0,60,(3350,4));y=np.zeros_like(u)
    for k in range(1,len(y)):y[k]=2+.7*y[k-1]+.01*u[k]+rng.normal(0,.0001,4)
    return y,u


def test_known_linear_recovery_serialization_and_dimensions():
    y,u=linear_data();model=fit(y,u,'ARX',1,1e-8)
    assert model.diagnostics['valid'] and model.coef.shape==(21,4)
    np.testing.assert_allclose((model.coef[1:5]/model.scale[:4,None]).T,.7*np.eye(4),atol=.001)
    np.testing.assert_allclose((model.coef[5:9]/model.scale[4:8,None]).T,.01*np.eye(4),atol=.0001)
    assert model.diagnostics['rank']==21
    assert fit(y,u,'AR',4,.001).coef.shape==(17,4)
    assert fit(y,u,'ARX',4,.001).coef.shape==(33,4)
    restored=Predictor.load(model.record())
    np.testing.assert_array_equal(restored.forecast(y[:3000],u[:3000],u[3000:3050]),model.forecast(y[:3000],u[:3000],u[3000:3050]))


def test_feature_timing_and_common_origin_no_input_contrast():
    y=np.arange(200,dtype=float).reshape(50,4);u=y+1000
    x=features(y,u,np.array([10]),4,True)[0]
    np.testing.assert_array_equal(x,np.r_[y[9],y[8],y[7],y[6],u[10],u[9],u[8],u[7]])
    y,u=linear_data();plan=np.zeros((50,4));active=np.full((50,4),60.)
    for family in ('AR','CONSTANT'):
        model=fit(y,u,family,1,.001)
        np.testing.assert_array_equal(model.forecast(y[:3000],u[:3000],plan),model.forecast(y[:3000],u[:3000],active))
    model=fit(y,u,'ARX',1,.001)
    assert np.abs(model.forecast(y[:3000],u[:3000],plan)-model.forecast(y[:3000],u[:3000],active)).mean()>.1


def test_fit_scaling_and_shuffling_never_cross_evaluation_boundary():
    y,u=linear_data();old_y=y.copy();old_u=u.copy()
    models=[fit(y,u,f,1,.001) for f in ('AR','ARX','SHUFFLED')]
    y[2350:]=999;u[2350:]=-999
    for family,model in zip(('AR','ARX','SHUFFLED'),models):
        changed=fit(y,u,family,1,.001)
        assert changed.record()==model.record()
    np.testing.assert_array_equal(old_u[:2350],u[:2350]);assert not np.array_equal(models[1].coef,models[2].coef)
    source=inspect.getsource(inspect.getmodule(fit))
    assert '_brian' not in source and 'efficacy' not in source and 'connectivity' not in source
    assert tuple(inspect.signature(Predictor.forecast).parameters)==('self','y_history','u_history','plan')
    assert np.all(old_y[FIT].mean(axis=0)==models[0].output_mean)


def test_predictions_do_not_use_future_observations_or_out_of_horizon_actions():
    y,u=linear_data();model=fit(y,u,'ARX',1,.001);k=3000
    expected=model.forecast(y[:k],u[:k],u[k:k+10])
    y[k:]=900;u[k+10:]=-900
    np.testing.assert_array_equal(model.forecast(y[:k],u[:k],u[k:k+10]),expected)
    with pytest.raises(ValueError):model.forecast(y[:0],u[:0],np.zeros((1,4)))
    with pytest.raises(ValueError):model.forecast(y[:k],u[:k],np.full((1,4),np.nan))


def test_input_design_constraints_rank_seeds_and_guard_exposure():
    for n in range(10):
        for rep in (18,19,20):
            desired,prefix,targets,plans=schedules(Config(network_id=n,replicate_id=rep))
            assert prefix.shape==(3350,4) and plans.shape==(6,100,4)
            for rows in (prefix,*plans):assert audit(rows)['violations']==0
            assert all(audit(rows)['exposure_pA_s']==pytest.approx(120) for rows in plans[1:5])
            np.testing.assert_array_equal(prefix[-1],np.zeros(4))
            for first in (750,2350,2750):
                for tick in range(first+5,first+(1600 if first==750 else 400),25):assert not prefix[tick-1].any()
            k=np.arange(750,2350);x=np.concatenate([prefix[k-lag] for lag in range(4)],axis=1)
            z=(x-x.mean(axis=0))/np.maximum(x.std(axis=0),1)
            assert np.linalg.matrix_rank(z)==16 and np.linalg.cond(z)<1e6
    np.testing.assert_array_equal(bank().sum(axis=0),np.full(4,540))
    a=schedules(Config(network_id=0,replicate_id=18))[1];b=schedules(Config(network_id=0,replicate_id=19))[1]
    assert not np.array_equal(a,b)


def test_reject_numerically_unidentified_model_and_guard_absolute_gate():
    model=fit(np.ones((3350,4)),np.zeros((3350,4)),'ARX',1,.001)
    assert not model.diagnostics['valid']
    with pytest.raises(ValueError):model.forecast(np.ones((4,4)),np.zeros((4,4)),np.zeros((1,4)))
    mse=np.tile([1.,1.,.5,1.],(10,1));assert qualification(mse)['scientific_gate']=='PASS'
    tiny=np.tile([.01,.01,.009,.01],(10,1));assert qualification(tiny)['scientific_gate']=='FAIL'
    mse[:,3]=.49;assert qualification(mse)['scientific_gate']=='FAIL'
    with pytest.raises(ValueError):qualification(np.full((10,4),np.nan))
    assert len(GRID)==8


def test_filter_initialization_warmup_is_identical_for_all_candidates():
    y,u=linear_data();y[:749]=np.nan
    for family in ('AR','ARX','SHUFFLED'):
        for p in (1,4):assert fit(y,u,family,p,.001).diagnostics['valid']
    assert FIT.start==753 and FIT.stop-FIT.start==1597
