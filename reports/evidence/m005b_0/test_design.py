"""Independent synthetic analytical checks; no new neural outcomes."""
import numpy as np
import pytest
from prototype import initialize_raw,new_model,bank,plan,safe_ramp
from neuromancer.control import project
from neuromancer.online_identify import features,standardized


def fixture():
    g=np.random.default_rng(20261105);q=g.uniform(0,120,2550)
    for k in range(1,len(q)):q[k]=np.clip(q[k],q[k-1]-30,q[k-1]+30)
    u=np.zeros((2550,4));u[:,::2]=q[:,None];y=np.full((2550,4),8.)
    for j in range(10):y[9:]+=.001*(j+1)*q[9-j:2550-j,None]
    y+=g.normal(0,.01,y.shape)
    return u,y,initialize_raw(y,u)


def test_raw_initializer_and_restricted_rank():
    u,y,(r,z,v,p)=fixture();assert r['diagnostics']['reduced_rank']==11 and r['diagnostics']['rank']==11
    a=z.T@z+len(z)*.1*np.diag(np.r_[0.,np.ones(40)])
    np.testing.assert_allclose(np.linalg.solve(a,z.T@v),r['coef'],atol=1e-10);np.testing.assert_allclose(p,np.linalg.inv(a))
    with pytest.raises(ValueError):initialize_raw(y,np.zeros_like(u))


def test_all625_plans_match_original_projection():
    for prior in (0.,37.3,120.):
        a,b,q=bank(prior)
        for i in range(625):
            p=np.array([prior,0,prior,0.])
            for k in range(100):
                d=a[i] if k<50 else b[i];p,_=project([d,0,d,0],p)
                np.testing.assert_array_equal(p,[q[i,k],0,q[i,k],0])


def test_multistep_predictions_and_global_minimum():
    u,y,(r,z,v,p)=fixture();h=u[-9:];result=plan(r,np.array(r['coef']),h,10.,51_000_000,limit_s=10)
    # Independent original40-feature regression, not collapsed-kernel predictor.
    q=result['bank'];expected=[]
    for i in range(625):
        future=np.zeros((100,4));future[:,::2]=q[i,:,None];all_u=np.vstack([h,future]);x=features(all_u,np.arange(9,109));pred=standardized(r,x)@np.array(r['coef'])+r['output_mean'];expected.append(pred)
    np.testing.assert_allclose(expected,result['predictions'],atol=1e-11)
    j=result['chosen'];assert result['cost'][j]<=min(result['cost'])+1e-12
    d=2*.02*q.sum(1);np.testing.assert_allclose(d,result['exposure'])


def test_zero_gain_ties_do_not_choose_dose():
    u,y,(r,z,v,p)=fixture();theta=np.zeros((41,4));r['output_mean']=[8.]*4
    result=plan(r,theta,np.zeros((9,4)),8.,51_000_000,limit_s=10)
    assert result['q0']==result['q1']==0 and not result['first'].any()


def test_first_prediction_fixed_adaptive_identical_and_batch_rls():
    u,y,(r,z,v,p)=fixture();a=new_model(r,z,v,p,False);b=new_model(r,z,v,p,True);h=u[-9:]
    np.testing.assert_array_equal(plan(r,a.theta,h,10.,51_000_000,limit_s=10)['first'],plan(r,b.theta,h,10.,51_000_000,limit_s=10)['first'])
    info=np.linalg.inv(p);rhs=z.T@v
    for k in range(20):
        x=features(u,np.array([2400+k]))[0];zz=standardized(r,x[None])[0];obs=y[2400+k]
        b.update(x,obs,51_020_000+k*20000,51_020_000+k*20000)
        info=.999*info+np.outer(zz,zz);rhs=.999*rhs+np.outer(zz,obs-r['output_mean'])
    np.testing.assert_allclose(b.theta,np.linalg.solve(info,rhs),atol=1e-9)


def test_completed_observation_causality_and_skips():
    u,y,(r,z,v,p)=fixture();a=new_model(r,z,v,p,True);b=new_model(r,z,v,p,True);old=a.theta.copy();x=features(u,np.array([2400]))[0]
    # Changing an unconsumed future label cannot affect the already-made plan.
    y[2450:]=99;np.testing.assert_array_equal(a.theta,b.theta)
    a.update(x,np.full(4,np.nan),51_020_000,51_020_000);assert a.skips==1;np.testing.assert_array_equal(a.theta,old)
    a.update(x,y[2400],51_040_000,51_060_000);assert a.skips==2
    with pytest.raises(ValueError):a.update(x,y[2400],51_040_000,51_040_000)


def test_timeout_discards_plan_and_safe_ramp_is_feasible():
    u,y,(r,z,v,p)=fixture();ticks=iter((0,300_000_000))
    with pytest.raises(TimeoutError):plan(r,r['coef'],u[-9:],10.,51_000_000,clock=lambda:next(ticks))
    prev=np.array([120.,120.,0.,0.]);rows=safe_ramp(prev)
    assert not rows[-1].any() and (abs(np.diff(np.vstack([prev,rows]),axis=0))<=30).all() and (rows.sum(1)<=240).all()


def test_invalid_history_model_and_mismatch_are_explicit():
    u,y,(r,z,v,p)=fixture();theta=np.array(r['coef']);theta[:]=100
    with pytest.raises(ValueError):plan(r,theta,u[-9:],10.,51_000_000,limit_s=10)
    bad=u[-9:].copy();bad[:,1]=1
    with pytest.raises(ValueError):plan(r,r['coef'],bad,10.,51_000_000)
    with pytest.raises(ValueError):plan(r,r['coef'],u[-9:],10.,51_020_000)
    # Finite wrong-sign model stays current-feasible; no performance guarantee.
    theta=np.array(r['coef']);theta[1:]*=-1
    out=plan(r,theta,np.zeros((9,4)),10.,51_000_000,limit_s=10)
    assert (out['first']>=0).all() and (out['first']<=120).all() and (out['first'].sum(1)<=240).all()
