"""Frozen M005B finite-bank planner; no simulator or observation-state access."""
import numpy as np
from .clocks import now_ns
GRID=np.arange(0.,121.,5.)

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

