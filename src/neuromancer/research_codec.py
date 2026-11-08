"""Lossless model-state audit encoding; never changes estimator/controller math."""
import hashlib
import numpy as np


def model_digest(model):
    h=hashlib.sha256()
    for value in (model.theta,model.p,np.array([model.bias_p])):
        a=np.ascontiguousarray(value,dtype=np.float64);h.update(a.tobytes())
    return h.digest()


def compact_plan(plan):
    keys=('chosen','q0','q1','cost','tracking','dose','switch','exposure','origin_us','minimum_forecast','elapsed_ns','theta','history')
    result={k:plan[k] for k in keys};result['selected_forecast']=plan['predictions'][plan['chosen']].copy()
    return result
