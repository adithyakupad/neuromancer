"""Bounded selected-model cost probe: fixed first trial, no outcome access."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from neuromancer.necessity import FAMILIES,fit,forecast


def main(raw,models,output):
    raw=Path(raw)/'n0_r22';models=Path(models)/'n0_r22';output=Path(output)
    with np.load(raw/'prefix.npz',allow_pickle=False) as z:y=z['rates'];u=z['delivered']
    with np.load(raw/'plans.npz',allow_pickle=False) as z:plan=z['planned'][1]
    selected=json.load(open(models/'selected.json'));rows=[]
    for family in FAMILIES:
        m=selected[family];fits=[];predictions=[]
        for _ in range(5):
            start=time.perf_counter_ns();refit=fit(y,u,family,m['size'],m['diagnostics']['lambda_value']);fits.append(time.perf_counter_ns()-start)
            assert refit==m
        expected=forecast(m,y,u,plan)
        for _ in range(50):
            start=time.perf_counter_ns();result=forecast(m,y,u,plan);predictions.append(time.perf_counter_ns()-start);np.testing.assert_array_equal(result,expected)
        rows.append(dict(model=family,parameters=m['diagnostics']['parameters'],fit_median_ms=float(np.median(fits)/1e6),forecast100_median_us=float(np.median(predictions)/1e3),
            fit_ns=fits,forecast100_ns=predictions))
    result=dict(fixture='n0_r22, SHORT plan, no reserved observations',fit_repetitions=5,forecast_repetitions=50,models=rows,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Single-machine warm-cache API costs, not neural throughput or whole-experiment calibration cost.')
    (output/'model_cost.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('models');p.add_argument('output');a=p.parse_args();main(a.raw,a.models,a.output)
