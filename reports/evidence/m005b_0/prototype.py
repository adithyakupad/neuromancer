"""DESIGN-ONLY synthetic feasibility helpers. No neural runner/controller deployment."""
import numpy as np
from neuromancer.clocks import now_ns
from neuromancer.control import project
from neuromancer.online_identify import features, ridge, OnlineFIR

GRID=np.arange(0.,121.,5.)


def initialize_raw(y,u):
    y=np.asarray(y,float);u=np.asarray(u,float)
    if y.shape!=u.shape or y.shape!=(2550,4):raise ValueError('Complete raw51s prefix required')
    if not np.isfinite(y).all() or not np.isfinite(u).all():raise ValueError('Nonfinite prefix')
    if np.any(u[:,1::2]!=0) or np.any(u[:,0]!=u[:,2]):raise ValueError('C02 only')
    k=np.arange(800,2350);x=features(u,k);mu=x.mean(0);scale=np.maximum(x.std(0),1.);ym=y[k].mean(0)
    z=np.c_[np.ones(len(x)),(x-mu)/scale];v=y[k]-ym
    reduced=np.c_[np.ones(len(k)),*[u[k-j,0] for j in range(10)]]
    reduced[:,1:]=(reduced[:,1:]-reduced[:,1:].mean(0))/np.maximum(reduced[:,1:].std(0),1.)
    rank=int(np.linalg.matrix_rank(reduced));condition=float(np.linalg.cond(reduced))
    if rank!=11 or condition>1e6:raise ValueError('Unidentified C02 history')
    theta,p=ridge(z,v,.1)
    record=dict(coef=theta.tolist(),mean=mu.tolist(),scale=scale.tolist(),output_mean=ym.tolist(),diagnostics=dict(rank=int(np.linalg.matrix_rank(z)),reduced_rank=rank,reduced_condition=condition,information_condition=float(np.linalg.cond(np.linalg.inv(p))),parameters=theta.size,rows=len(z)))
    return record,z,v,p


def new_model(record,z,v,p,adaptive):
    m=OnlineFIR(record,z,v,p,'RLS999' if adaptive else 'FROZEN')
    # New instance only; initial coefficients unchanged, clock explicitly adapted.
    m.time_us=51_000_000
    return m


def bank(previous):
    """Vectorized C02 delivery, inward endpoints match original projector."""
    if not np.isfinite(previous) or not 0<=previous<=120:raise ValueError('Invalid actuator state')
    q0=np.repeat(GRID,len(GRID));q1=np.tile(GRID,len(GRID));hold=np.c_[np.repeat(q0[:,None],50,axis=1),np.repeat(q1[:,None],50,axis=1)]
    delivered=np.empty_like(hold);p=np.full(len(hold),previous)
    for k in range(100):
        lo=np.maximum(0.,p-30);hi=np.minimum(120.,p+30)
        for _ in range(64):
            a=p-lo>30;b=hi-p>30
            if not(a.any() or b.any()):break
            lo[a]=np.nextafter(lo[a],p[a]);hi[b]=np.nextafter(hi[b],p[b])
        else:raise ArithmeticError('Unrepresentable bounds')
        p=np.clip(hold[:,k],lo,hi);delivered[:,k]=p
    return q0,q1,delivered


def plan(record,theta,history,target,origin_us,*,limit_s=.25,clock=now_ns):
    start=clock();end=start+int(limit_s*1e9)
    def check():
        if clock()>=end:raise TimeoutError('Planner decision expired')
    if type(origin_us) is not int or origin_us<51_000_000 or (origin_us-51_000_000)%1_000_000:raise ValueError('Invalid causal origin')
    h=np.asarray(history,float);theta=np.asarray(theta,float)
    if h.shape!=(9,4) or not np.isfinite(h).all() or np.any(h[:,1::2]!=0) or np.any(h[:,0]!=h[:,2]) or np.any(h<0) or np.any(h>120) or np.any(abs(np.diff(h,axis=0))>30):raise ValueError('Nine delivered C02 rows required')
    if not np.isfinite(target) or theta.shape!=(41,4) or not np.isfinite(theta).all():raise ValueError('Invalid model/target')
    mu=np.asarray(record['mean']);scale=np.asarray(record['scale']);ym=np.asarray(record['output_mean'])
    if mu.shape!=(40,) or scale.shape!=(40,) or ym.shape!=(4,) or not np.isfinite(np.r_[mu,scale,ym]).all() or (scale<=0).any():raise ValueError('Invalid fixed normalization')
    check();q0,q1,q=bank(h[-1,0]);check()
    b=theta[1:]/scale[:,None];c=ym+theta[0]-mu@b
    kernels=b.reshape(10,4,4)[:,0,:]+b.reshape(10,4,4)[:,2,:]
    full=np.c_[np.broadcast_to(h[:,0],(625,9)),q];pred=np.broadcast_to(c,(625,100,4)).copy()
    for j in range(10):pred+=full[:,9-j:109-j,None]*kernels[j]
    if not np.isfinite(pred).all() or np.abs(pred).max()>100:raise ValueError('Invalid candidate forecast')
    check();means=pred.reshape(625,2,50,4).mean(axis=(2,3));tracking=((means-target)**2).sum(1)
    dose=.02*np.sum(.02*(q/120)**2,axis=1);switch=.01*((q0-h[-1,0])**2+(q1-q0)**2)/120**2;cost=tracking+dose+switch;exposure=q.sum(1)*.02*2
    near=np.flatnonzero(cost<=cost.min()+1e-12);i=int(near[np.lexsort((q1[near],q0[near],exposure[near]))[0]])
    check();first=np.zeros((50,4));first[:,::2]=q[i,:50,None]
    return dict(first=first,chosen=i,q0=float(q0[i]),q1=float(q1[i]),cost=cost,tracking=tracking,dose=dose,switch=switch,exposure=exposure,predictions=pred,bank=q,origin_us=origin_us,minimum_forecast=float(pred.min()),elapsed_ns=clock()-start)


def safe_ramp(previous):
    p=np.asarray(previous,float);rows=[]
    for _ in range(50):p,_=project(np.zeros(4),p);rows.append(p.copy())
    return np.array(rows)
