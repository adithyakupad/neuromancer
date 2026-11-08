"""M002.3 frozen observation-only calibration; no simulator or gain inputs."""
from dataclasses import dataclass
import math
import numpy as np
from .observation import Observation
from .substrate import Receipt

DOSES=(0.,30.,60.,90.,120.)


def ramp(desired):
    rows=np.asarray(desired,dtype=float).copy()
    if rows.ndim!=2 or rows.shape[1]!=4 or not np.isfinite(rows).all():
        raise ValueError('Expected finite current rows')
    if np.any(rows<0) or np.any(rows>120) or np.any(rows.sum(axis=1)>240):
        raise ValueError('Invalid requested current; no clipping of bounds')
    prior=np.zeros(4)
    for row in rows:
        row[:]=np.clip(row,prior-30,prior+30);prior=row.copy()
    return rows


def prefix_schedule():
    desired=np.zeros((2550,4))
    for j,q in enumerate(DOSES[1:]):desired[950+400*j:1150+400*j,::2]=q
    return ramp(desired)


def inverse(h,excursion):
    h=np.asarray(h,dtype=float)
    if h.shape!=(5,) or not np.isfinite(h).all() or h[0]!=0 or np.any(np.diff(h)<=1e-9):
        raise ValueError('Nonmonotone or ill-conditioned calibration')
    if not math.isfinite(excursion) or not 0<=excursion<=h[-1]:
        raise ValueError('Target outside measured range; extrapolation forbidden')
    return float(np.interp(excursion,h,DOSES))


@dataclass(frozen=True,slots=True)
class Calibration:
    baseline_hz: float
    h_hz: tuple[float,...]
    targets_hz: tuple[float,float]
    span_hz: float
    lookup_pA: tuple[float,float] | None
    valid: bool
    reason: str
    frozen_at_us: int = 47_000_000


def fit(observations: tuple[Observation,...], receipts: tuple[Receipt,...]) -> Calibration:
    """Consume exactly completed [0,47)s records; later observations are rejected."""
    if len(observations)!=2350 or len(receipts)!=2350:
        raise ValueError('Calibration requires exactly the declared prefix through47s')
    rows=[];counts=[]
    for k,(o,r) in enumerate(zip(observations,receipts,strict=True)):
        start=k*20_000;stop=start+20_000
        if (o.start_us,o.stop_us,o.available_us)!=(start,stop,stop):raise ValueError('Noncausal observation timing')
        if len(o.counts)!=20 or len(o.valid)!=20 or not all(o.valid) or tuple(o.coverage_us)!=(20_000,)*20:
            raise ValueError('Incomplete observations')
        if any(type(c) is not int or c<0 for c in o.counts):raise ValueError('Invalid spike counts')
        if (r.requested_start_us,r.delivered_start_us,r.delivered_stop_us)!=(start,start,stop):
            raise ValueError('Receipt timing mismatch')
        if o.trial_id!=r.trial_id or r.requested_current_pA!=r.delivered_current_pA:
            raise ValueError('Receipt identity or delivery mismatch')
        rows.append(r.delivered_current_pA);counts.append(o.counts)
    if not np.array_equal(rows,prefix_schedule()[:2350]):raise ValueError('Wrong calibration delivery schedule')
    scalar=np.asarray(counts,dtype=np.int64).reshape(2350,4,5)[:,:,:4].sum(axis=(1,2))/1.6
    baseline=float(scalar[350:750].mean())
    h=[0.]+[float(scalar[1000+400*j:1150+400*j].mean()-scalar[800+400*j:950+400*j].mean()) for j in range(4)]
    scale=.6*h[-1];targets=(baseline+.1*scale,baseline+.9*scale);span=.8*scale
    try:lookup=(inverse(h,.1*scale),inverse(h,.9*scale));reason='valid'
    except ValueError as error:lookup=None;reason=str(error)
    return Calibration(baseline,tuple(h),targets,span,lookup,lookup is not None,reason)
