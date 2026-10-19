"""Analytical M003.1 fixtures; not neural scientific results."""
import inspect
import numpy as np
import pytest
from neuromancer.necessity import fit,forecast,forecast_inputs,design,gate,select
from neuromancer.necessity_experiment import schedules
from neuromancer.substrate import Config
from neuromancer.identification_experiment import audit


def data():
    rng=np.random.default_rng(552);u=rng.uniform(0,40,(3350,4));y=3+.02*u
    return y,u


def test_static_coefficients_and_input_only_api():
    y,u=data();m=fit(y,u,'STATIC',1,1e-9)
    np.testing.assert_allclose(np.array(m['coef'])[1:]/np.array(m['scale'])[:,None],.02*np.eye(4),atol=1e-8)
    np.testing.assert_allclose(forecast_inputs(m,u[:3000],u[3000:3010]),y[3000:3010],atol=1e-8)
    assert tuple(inspect.signature(forecast_inputs).parameters)==('record','u_history','plan')
    assert m['diagnostics']['parameters']==20


def test_fir_recovery_delayed_impulse_and_independent_convolution():
    y,u=data();y=3+.005*u+.03*np.roll(u,3,axis=0)
    m=fit(y,u,'FIR',10,1e-9);beta=np.array(m['coef'])[1:]/np.array(m['scale'])[:,None]
    np.testing.assert_allclose(beta[12:16],.03*np.eye(4),atol=1e-7)
    plan=np.zeros((15,4));plan[0,0]=10
    predicted=forecast_inputs(m,np.zeros((50,4)),plan);zero=forecast_inputs(m,np.zeros((50,4)),np.zeros_like(plan))
    expected=np.zeros_like(predicted);expected[0,0]=.05;expected[3,0]=.3
    np.testing.assert_allclose(predicted-zero,expected,atol=1e-7)
    assert m['diagnostics']['parameters']==164


def test_fitting_and_forecast_data_separation_and_shuffling():
    y,u=data();m=fit(y,u,'FIR',10,.001);before=m.copy();y[2350:]=999;u[2350:]=-999
    assert fit(y,u,'FIR',10,.001)==before
    plan=np.zeros((100,4));a=forecast(m,np.zeros((100,4)),u[:2200],plan);b=forecast(m,np.full((100,4),999),u[:2200],plan)
    np.testing.assert_array_equal(a,b)
    x=design(y,u,'STATIC_SHUFFLED',1);np.testing.assert_array_equal(x,np.roll(u[800:2350],500,axis=0))
    with pytest.raises(ValueError):forecast_inputs(m,u[:2],plan)
    with pytest.raises(ValueError):forecast_inputs(m,u[:2200],np.full_like(plan,np.nan))


def test_linear_arx_contrast_does_not_use_origin_observation_state():
    y,u=data()
    for k in range(1,len(y)):y[k]=1+.6*y[k-1]+.015*u[k]
    m=fit(y,u,'ARX',1,.0001);plan=np.full((100,4),30.);zero=np.zeros_like(plan)
    first=forecast(m,y[:3000],u[:3000],plan)-forecast(m,y[:3000],u[:3000],zero)
    replaced=np.tile(m['output_mean'],(len(y[:3000]),1))
    second=forecast(m,replaced,u[:3000],plan)-forecast(m,replaced,u[:3000],zero)
    np.testing.assert_allclose(first,second,rtol=0,atol=1e-12)
    weights=np.array(m['coef'])[1:]/np.array(m['scale'])[:,None];effect=np.zeros((100,4))
    for k in range(100):
        if k:effect[k]+=effect[k-1]@weights[:4]
        for lag in range(4):
            if k>=lag:effect[k]+=plan[k-lag]@weights[4+4*lag:8+4*lag]
    np.testing.assert_allclose(first,effect,rtol=0,atol=1e-12)


def test_registered_plans_exposure_and_input_rank():
    for n in range(10):
        for rep in (22,23,24):
            _,u,_,plans=schedules(Config(network_id=n,replicate_id=rep))
            for rows in (u,*plans):assert audit(rows)['violations']==0
            assert all(audit(rows)['exposure_pA_s']==pytest.approx(24) for rows in plans[1:5])
            x=design(np.zeros_like(u),u,'FIR',50);z=(x-x.mean(axis=0))/np.maximum(x.std(axis=0),1)
            assert np.linalg.matrix_rank(z)==200 and np.linalg.cond(z)<1e6
            assert not np.array_equal(plans[1],plans[2]) and not np.array_equal(plans[3],plans[4])


def test_network_gate_and_selection():
    assert gate(np.ones(10),np.full(10,.5))['scientific_gate']=='PASS'
    assert gate(np.full(10,.1),np.full(10,.095))['scientific_gate']=='FAIL'
    assert gate(np.ones(10),np.ones(10))['scientific_gate']=='FAIL'
    assert select([dict(loss=.1,features=4,lambda_value=.01,**{'lambda':.01}),dict(loss=.1,features=40,**{'lambda':.1})])['features']==4
    with pytest.raises(ValueError):select([dict(loss=None)])


def test_independent_ridge_and_forecast_equations():
    import importlib.util
    spec=importlib.util.spec_from_file_location('necessity_audit','reports/evidence/m003_1/verify.py')
    audit_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit_module)
    y,u=data();rng=np.random.default_rng(775);y+=rng.normal(0,.1,y.shape)
    for family,size in [('STATIC',1),('FIR',10),('FIR',50),('ARX',1),('ARX',4),('AR',4),('FIR_SHUFFLED',10)]:
        m=fit(y,u,family,size,.001);assert m['diagnostics']['valid'];audit_module.coefficient(m,y,u,{})
        np.testing.assert_allclose(forecast(m,y[:3000],u[:3000],u[3000:3010]),audit_module.predict(m,y[:3000],u[:3000],u[3000:3010]),atol=1e-9,rtol=0)
        expected=forecast(m,y[:3000],u[:3000],u[3000:3010]);changed=y.copy();changed[3000:]=999
        np.testing.assert_array_equal(expected,forecast(m,changed[:3000],u[:3000],u[3000:3010]))
