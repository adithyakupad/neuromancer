"""Synthetic M005B engineering tests; no study acquisition or tuning."""
from dataclasses import replace
import numpy as np
import pytest
from neuromancer.predictive import initialize_raw,Initialization,FIRModel,PredictiveController
from neuromancer.predictive_planner import bank,plan
from neuromancer.control import ControlCalibration,project
from neuromancer.observation import Observation
from neuromancer.substrate import Receipt


def fixture():
    g=np.random.default_rng(20261106);q=g.uniform(0,120,2550)
    for k in range(1,len(q)):q[k]=np.clip(q[k],q[k-1]-30,q[k-1]+30)
    u=np.zeros((2550,4));u[:,::2]=q[:,None];y=np.full((2550,4),8.)
    for lag in range(10):y[9:]+=.0005*(lag+1)*q[9-lag:2550-lag,None]
    rec,z,v,p=initialize_raw(y,u);cal=ControlCalibration(8.,.1,.0275,1/.0275,9.,(0.,.8,1.6,2.4,3.2),True,'synthetic')
    return Initialization(rec,p,np.zeros((9,4)),cal,'synthetic'),z,v,u,y


def observation(t,rate=10.):
    counts=[0]*20
    for sector in range(4):counts[sector*5]=int(round(rate*.4))
    return Observation('synthetic',t,t+20000,t+20000,tuple(counts),(0.,)*20,(20000,)*20,(True,)*20,(),(),(0.,)*4,(0.,)*4,True)


def receipt(c):return Receipt(c.trial_id,c.command_id,c.start_us,c.start_us,c.start_us+20000,c.current_pA,c.current_pA,'delivered','')


def test_initializer_raw_normal_equations_and_no_independent_channel_claim():
    init,z,v,u,y=fixture();a=z.T@z+len(z)*.1*np.diag(np.r_[0.,np.ones(40)])
    np.testing.assert_allclose(init.record['coef'],np.linalg.solve(a,z.T@v),atol=1e-10)
    assert init.record['diagnostics']['rank']==11 and init.record['diagnostics']['reduced_rank']==11
    with pytest.raises(ValueError):initialize_raw(y,np.zeros_like(u))


def test_all625_candidates_exact_projection_and_multistep_raw_equations():
    init,*_=fixture();q0,q1,q=bank(37.3)
    for i in range(625):
        prev=np.array([37.3,0,37.3,0])
        for k in range(100):prev,_=project([q0[i] if k<50 else q1[i],0,q0[i] if k<50 else q1[i],0],prev);np.testing.assert_array_equal(prev,[q[i,k],0,q[i,k],0])
    out=plan(init.record,init.record['coef'],init.history,9.,51_000_000,limit_s=10)
    b=np.array(init.record['coef'])[1:]/np.array(init.record['scale'])[:,None];offset=np.array(init.record['output_mean'])+np.array(init.record['coef'])[0]-np.array(init.record['mean'])@b
    i=out['chosen'];future=np.zeros((109,4));future[9:,::2]=out['bank'][i,:,None];expected=np.tile(offset,(100,1))
    for lag in range(10):expected+=future[9-lag:109-lag]@b[lag*4:lag*4+4]
    np.testing.assert_allclose(out['predictions'][i],expected,atol=1e-11)


def test_rls_and_bias_independent_weighted_batch_and_frozen_coefficients():
    init,z,v,u,y=fixture();models=[FIRModel(init.record,init.information_inverse,k) for k in ('FIXED','RLS','BIAS')];a=np.linalg.inv(init.information_inverse);rhs=z.T@v;ab=len(z);hb=ab*models[2].theta[0].copy();frozen=models[0].theta.copy()
    for k in range(50):
        x=np.concatenate([u[2400+k-lag] for lag in range(10)]);zz=models[1].standardized(x);obs=y[2400+k];vv=obs-init.record['output_mean']
        a=.999*a+np.outer(zz,zz);rhs=.999*rhs+np.outer(zz,vv);ab=.999*ab+1;hb=.999*hb+vv-zz[1:]@frozen[1:]
        for m in models:m.update(x,obs)
    np.testing.assert_allclose(models[1].theta,np.linalg.solve(a,rhs),atol=1e-9);np.testing.assert_allclose(models[1].p,np.linalg.inv(a),atol=1e-9)
    np.testing.assert_allclose(models[2].theta[0],hb/ab,atol=1e-11);np.testing.assert_array_equal(models[0].theta,frozen);np.testing.assert_array_equal(models[2].theta[1:],frozen[1:])


def test_synthetic_gain_loss_adaptation_and_weak_identifiability():
    init,z,v,u,y=fixture();fixed=FIRModel(init.record,init.information_inverse);adaptive=FIRModel(init.record,init.information_inverse,'RLS');g=np.random.default_rng(61);prior=[];post=[]
    for k in range(1000):
        q=g.uniform(0,120,10);x=np.zeros((10,4));x[:,::2]=q[:,None];x=x.ravel();observed=8.+.6*(fixed.predict(x)-8.)
        if k>=900:prior.append(np.mean((fixed.predict(x)-observed)**2));post.append(np.mean((adaptive.predict(x)-observed)**2))
        adaptive.update(x,observed)
    assert np.mean(post)<np.mean(prior) and adaptive.failure is None
    # Constant-zero online design rank1: cannot identify independent kernel directions.
    weak=np.tile(adaptive.standardized(np.zeros(40)),(100,1));assert np.linalg.matrix_rank(weak)==1


def test_controller_timestamp_order_isolation_reset_and_future_data():
    init,*_=fixture();a=PredictiveController(init,'FIXED');b=PredictiveController(init,'RLS');old=a.model.theta.copy()
    ca=a.command(51_000_000);cb=b.command(51_000_000);assert ca==cb
    with pytest.raises(ValueError):a.command(51_000_000)
    with pytest.raises(ValueError):b.command(52_000_000)
    # Future observations are not accepted into current model.
    future=observation(51_020_000,99);a.accept(future,receipt(ca),51_020_000);assert a.model.skips==1
    b.accept(observation(51_000_000),receipt(cb),51_020_000)
    np.testing.assert_array_equal(a.model.theta,old);np.testing.assert_array_equal(init.record['coef'],old)
    fresh=PredictiveController(init,'RLS');assert fresh.time_us==51_000_000 and fresh.model.updates==0
    np.testing.assert_array_equal(fresh.model.theta,old)


@pytest.mark.parametrize('fault',['missing','late','mask','negative'])
def test_fault_safe_ramp_four_bin_rearm_and_no_stale_updates(fault):
    init,*_=fixture();p=PredictiveController(init,'RLS');c=p.command(p.time_us);o=observation(p.time_us)
    if fault=='missing':o=None
    elif fault=='late':o=replace(o,available_us=o.stop_us+20000)
    elif fault=='mask':o=replace(o,valid=(False,)*20)
    else:o=replace(o,counts=(-1,)*20)
    p.accept(o,receipt(c),p.time_us+20000);assert p.safe and p.recover==0 and p.model.updates==0
    for j in range(4):
        c=p.command(p.time_us);assert sum(c.current_pA)<=sum(p.history[-1]);p.accept(observation(p.time_us),receipt(c),p.time_us+20000)
    assert p.recover==4 and p.model.updates==0
    c=p.command(p.time_us);p.accept(observation(p.time_us),receipt(c),p.time_us+20000);assert p.model.updates==1 and p.safe
    while p.time_us<52_000_000:
        c=p.command(p.time_us);p.accept(observation(p.time_us),receipt(c),p.time_us+20000)
    p.command(p.time_us);assert not p.safe


def test_bad_information_is_transactional_latched_and_safe():
    init,*_=fixture();p=PredictiveController(init,'RLS');c=p.command(p.time_us);p.model.p=-np.eye(41)*100;old=p.model.theta.copy();p.accept(observation(p.time_us),receipt(c),p.time_us+20000)
    assert p.failure is not None and p.safe;np.testing.assert_array_equal(old,p.model.theta)
    for _ in range(5):
        c=p.command(p.time_us);p.accept(observation(p.time_us),receipt(c),p.time_us+20000)
    assert not p.command(p.time_us).current_pA[0]


def test_invalid_receipt_cannot_mutate_history_or_clock():
    init,*_=fixture();p=PredictiveController(init);c=p.command(p.time_us);old=p.history.copy()
    with pytest.raises(ValueError):p.accept(observation(p.time_us),replace(receipt(c),trial_id='other'),p.time_us+20000)
    np.testing.assert_array_equal(old,p.history);assert p.time_us==51_000_000 and p.failure is not None


def test_deadline_and_invalid_plan_latch_without_unchecked_action():
    init,*_=fixture()
    class Clock:
        def __init__(self):self.t=0
        def __call__(self):self.t+=100_000_000;return self.t
    p=PredictiveController(init,clock=Clock());c=p.command(p.time_us);assert p.failure is not None and c.current_pA==(0.,0.,0.,0.)
    p=PredictiveController(init);p.history[:,1]=1;c=p.command(p.time_us);assert p.failure is not None and abs(c.current_pA[1]-1)<=30
    p=PredictiveController(init);p.model.theta[:]=1e5;c=p.command(p.time_us);assert p.failure is not None and c.current_pA==(0.,0.,0.,0.)
