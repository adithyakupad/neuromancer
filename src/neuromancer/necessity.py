"""M003.1 fixed linear model comparison; input-only forecasts have no rate input."""
import numpy as np
from .identify import Predictor

FIT=slice(800,2350)
LAMBDAS=(.0001,.001,.01,.1)
FAMILIES=('STATIC','FIR','ARX','AR','STATIC_SHUFFLED','FIR_SHUFFLED','ARX_SHUFFLED')


def design(y,u,family,size):
    k=np.arange(FIT.start,FIT.stop);base=family.split('_')[0];current=np.asarray(u).copy()
    if family.endswith('_SHUFFLED'):current[FIT]=np.roll(current[FIT],500,axis=0)
    blocks=[]
    if base in ('AR','ARX'):blocks += [y[k-l] for l in range(1,size+1)]
    q=1 if base=='STATIC' else size if base=='FIR' else 4 if base=='ARX' else 0
    blocks += [current[k-l] for l in range(q)]
    x=np.hstack(blocks)
    if not np.isfinite(x).all():raise ValueError('Invalid causal fitting features')
    return x


def fit(y,u,family,size,lam):
    y=np.asarray(y);u=np.asarray(u)
    if y.shape!=u.shape or y.ndim!=2 or y.shape[1]!=4 or len(y)<2350:raise ValueError('Aligned complete Nx4 arrays required')
    if family not in FAMILIES or lam<=0 or not np.isfinite(lam):raise ValueError('Invalid model')
    base=family.split('_')[0]
    if size not in ({'STATIC':(1,),'FIR':(10,50),'AR':(1,4),'ARX':(1,4)}[base]):raise ValueError('Unregistered history')
    x=design(y,u,family,size);target=y[FIT];mu=x.mean(axis=0);scale=np.maximum(x.std(axis=0),1);ym=target.mean(axis=0)
    z=np.c_[np.ones(len(x)),(x-mu)/scale];s=np.linalg.svd(z,compute_uv=False);rank=int(np.linalg.matrix_rank(z));condition=float(s[0]/s[-1]) if s[-1]>0 else 1e300
    penalty=np.diag(np.r_[0.,np.full(x.shape[1],np.sqrt(lam))]);aug=np.vstack([z/np.sqrt(len(x)),penalty])
    beta=np.linalg.lstsq(aug,np.vstack([(target-ym)/np.sqrt(len(x)),np.zeros((x.shape[1]+1,4))]),rcond=None)[0]
    p=size if base in ('AR','ARX') else 0;q=1 if base=='STATIC' else size if base=='FIR' else 4 if base=='ARX' else 0
    radius=0.
    if p:
        companion=np.zeros((4*p,4*p));companion[:4]=np.hstack([(beta[1+4*l:1+4*(l+1)]/scale[4*l:4*(l+1),None]).T for l in range(p)])
        if p>1:companion[4:,:-4]=np.eye(4*(p-1))
        radius=float(np.abs(np.linalg.eigvals(companion)).max())
    penalized=float(np.linalg.cond(aug));valid=bool(rank==z.shape[1] and condition<=1e6 and penalized<=1e8 and radius<.999 and np.isfinite(beta).all())
    return dict(family=family,size=size,p=p,q=q,coef=beta.tolist(),mean=mu.tolist(),scale=scale.tolist(),output_mean=ym.tolist(),
        diagnostics=dict(valid=valid,parameters=int(beta.size),features=x.shape[1],rank=rank,condition=condition,penalized_condition=penalized,spectral_radius=radius,
        singular_values=s.tolist(),lambda_value=lam,fit_rows=[800,2350],target_start_us=16_000_000,target_stop_us=47_000_000))


def forecast_inputs(record,u_history,plan):
    if record['p'] or record['family'].split('_')[0] not in ('STATIC','FIR'):raise ValueError('Not an input-only predictor')
    q=record['q'];u=np.asarray(u_history,dtype=float);plan=np.asarray(plan,dtype=float)
    if plan.ndim!=2 or plan.shape[1]!=4 or u.ndim!=2 or u.shape[1]!=4 or len(u)<q-1:raise ValueError('Invalid current history/plan')
    if not record['diagnostics']['valid'] or not np.isfinite(plan).all() or not np.isfinite(u[-max(q-1,1):]).all():raise ValueError('Invalid model/current')
    history=np.vstack([u[-q:] if q>1 else np.empty((0,4)),plan]);start=len(history)-len(plan)
    k=np.arange(start,len(history));x=np.hstack([history[k-l] for l in range(q)])
    result=np.array(record['output_mean'])+np.c_[np.ones(len(plan)),(x-record['mean'])/record['scale']]@np.array(record['coef'])
    if not np.isfinite(result).all() or np.abs(result).max(initial=0)>100:raise ValueError('Unbounded forecast; never clipped')
    return result


def forecast(record,y_history,u_history,plan):
    if not record['p']:return forecast_inputs(record,u_history,plan)
    mapped={k:record[k] for k in ('p','coef','mean','scale','output_mean','diagnostics')};mapped['family']='AR' if record['family']=='AR' else 'ARX'
    return Predictor.load(mapped).forecast(y_history,u_history,plan)


def select(rows):
    valid=[r for r in rows if r['loss'] is not None]
    if not valid:raise ValueError('No globally valid model')
    best=min(r['loss'] for r in valid)
    return min((r for r in valid if r['loss']<=best+1e-12),key=lambda r:(r['features'],-r['lambda']))


def gate(competitor,arx):
    delta=np.asarray(competitor)-np.asarray(arx);relative=delta/np.maximum(competitor,.04)
    def ci(v):
        v=np.asarray(v);indices=np.random.default_rng(20261101).integers(0,len(v),(10000,len(v)));draws=v[indices].mean(axis=1)
        return dict(mean=float(v.mean()),lower=float(np.quantile(draws,.025)),upper=float(np.quantile(draws,.975)))
    absolute=ci(delta);rel=ci(relative);points=absolute['mean']>=.04 and rel['mean']>=.10 and int((delta>0).sum())>=8
    return dict(scientific_gate='PASS' if points and absolute['lower']>0 else 'HOLD' if points else 'FAIL',absolute=absolute,relative=rel,
        positive_networks=int((delta>0).sum()),floor_count=int((np.asarray(competitor)<.04).sum()))
