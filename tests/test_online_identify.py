import numpy as np
import pytest
from neuromancer.online_identify import initialize, features, standardized, ridge, OnlineFIR, ResidualCUSUM
from neuromancer.online_experiment import actions, branch_audit
from neuromancer.substrate import Config


def fixture():
    rng=np.random.default_rng(45);u=rng.uniform(0,30,(2000,4));x=features(u,np.arange(9,2000));y=np.ones((2000,4))*12
    y[9:]+=x[:,:4]*.01+rng.normal(0,.1,(1991,4));rec,z,t,p=initialize(y,u)
    return u,y,rec,z,t,p


def test_original_fir_scaling_and_lags():
    u,y,r,z,t,p=fixture();k=np.arange(790,1950);x=features(u,k)
    np.testing.assert_array_equal(x[0,:4],u[790]);np.testing.assert_array_equal(x[0,-4:],u[781])
    a=np.diag(np.r_[0.,np.full(40,np.sqrt(len(z)*.1))]);coef=np.linalg.lstsq(np.vstack([z,a]),np.vstack([t,np.zeros((41,4))]),rcond=None)[0]
    np.testing.assert_allclose(coef,r['coef'],atol=1e-11)
    np.testing.assert_array_equal(r['mean'],x.mean(axis=0));np.testing.assert_array_equal(r['scale'],np.maximum(x.std(axis=0),1))


def test_rls_weighted_batch_equivalence():
    u,y,r,z,t,p=fixture();m=OnlineFIR(r,z,t,p,'RLS995');a=np.linalg.inv(p);h=z.T@t
    for i in range(50):
        x=features(u,np.array([1950+i]))[0];zz=standardized(r,x[None])[0];v=y[1950+i]-r['output_mean']
        m.update(x,y[1950+i],39_020_000+i*20000,39_020_000+i*20000)
        a=.995*a+np.outer(zz,zz);h=.995*h+np.outer(zz,v)
    np.testing.assert_allclose(m.theta,np.linalg.solve(a,h),atol=1e-9)
    np.testing.assert_allclose(m.p,np.linalg.inv(a),atol=1e-9)


def test_window_sample_budget_and_ordering():
    u,y,r,z,t,p=fixture();m=OnlineFIR(r,z,t,p,'SW250')
    before=m.forecast(features(u,np.arange(1950,2000)),39_000_000)
    for i in range(50):m.update(features(u,np.array([1950+i]))[0],y[1950+i],39_020_000+i*20000,39_020_000+i*20000)
    expected,_=ridge(np.array(m.z[-250:]),np.array(m.target[-250:]))
    np.testing.assert_allclose(m.theta,expected);assert m.updates==50 and m.refits==1
    assert before.shape==(50,4)
    with pytest.raises(ValueError):m.forecast(features(u,np.arange(1950,2000)),39_000_000)


def test_delay_missing_invalid_and_numerical_failure():
    u,y,r,z,t,p=fixture();m=OnlineFIR(r,z,t,p,'RLS999');old=m.theta.copy();x=features(u,np.array([1950]))[0]
    m.update(x,y[1950],39_020_000,39_040_000);m.update(x,y[1950],39_040_000,39_040_000,False)
    m.update(np.full(40,np.nan),y[1950],39_060_000,39_060_000)
    assert m.skips==3 and m.updates==0;np.testing.assert_array_equal(m.theta,old)
    with pytest.raises(ValueError):m.update(x,y[1950],39_060_000,39_060_000)
    m.p=-np.eye(41)*100;m.update(x,y[1950],39_080_000,39_080_000)
    assert m.failed and m.failures;np.testing.assert_array_equal(m.theta,old)
    with pytest.raises(ValueError):m.forecast(np.full((1,40),np.nan),39_080_000)


def test_detector_causality_information_and_refractory():
    d=ResidualCUSUM(.1,.25,3);assert not d.update(99,0,40_000_000)['alarm']
    assert d.update(1,120,41_000_000)['alarm']
    for s in range(42,46):assert not d.update(1,120,s*1_000_000)['alarm']
    assert d.update(1,120,46_000_000)['alarm']
    with pytest.raises(ValueError):d.update(1,120,46_000_000)


def test_future_observation_and_input_mutation():
    u,y,r,z,t,p=fixture();a=OnlineFIR(r,z,t,p,'RLS999');b=OnlineFIR(r,z,t,p,'RLS999')
    changed=y.copy();changed[1975:]=99
    for i in range(25):
        x=features(u,np.array([1950+i]))[0]
        np.testing.assert_array_equal(a.forecast(x[None],a.time_us),b.forecast(x[None],b.time_us))
        for m,obs in ((a,y),(b,changed)):m.update(x,obs[1950+i],39_020_000+i*20000,39_020_000+i*20000)
    altered=u.copy();altered[1975:]=100
    np.testing.assert_array_equal(features(u,np.arange(1950,1975)),features(altered,np.arange(1950,1975)))


def test_schedules_and_sham_from_nonzero_prior():
    for n in range(10):
        _,u=actions(Config(network_id=n,replicate_id=32));assert u.shape==(3950,4)
        assert branch_audit(u,np.zeros(4))['violations']==0
        for k in (2700,3200,3700):
            prev=u[k-1];sham=np.maximum(prev[None]-30*np.arange(1,51)[:,None],0)
            assert branch_audit(sham,prev)['violations']==0
    _,weak=actions(Config(),True);assert not weak.any()


def test_unexcited_initialization_and_finite_serialization():
    import json
    rng=np.random.default_rng(47);u=np.zeros((2000,4));y=12+rng.normal(0,.1,(2000,4))
    rec,z,t,p=initialize(y,u);json.dumps(rec,allow_nan=False)
    assert rec['diagnostics']['rank']==1
    np.testing.assert_allclose(np.array(rec['coef'])[1:],0,atol=1e-12)
    m=OnlineFIR(rec,z,t,p,'RLS995');assert np.isfinite(m.forecast(np.zeros((50,40)),39_000_000)).all()


def test_detector_event_boundary_is_strictly_post_change():
    import importlib.util,sys
    from pathlib import Path
    directory=Path(__file__).parents[1]/'reports/evidence/m004';sys.path.insert(0,str(directory))
    try:
        spec=importlib.util.spec_from_file_location('m004_selection_test',directory/'select_models.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        alarms=np.zeros(40);alarms[19]=1
        assert module.detection(alarms)['miss']
        alarms[20]=1;event=module.detection(alarms)
        assert event['delay_s']==1 and event['timely'] and event['pre_alarms']==1
    finally:sys.path.remove(str(directory))
