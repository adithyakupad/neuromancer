"""Bounded M028 kernel measurements and unchanged M027 archive orchestration."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import runpy
import sys
import time

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.m028_backend import load_kernel,bounds,driver


def kernel_benchmark(output,compiled):
    from tools import m027_residual_bounds as original
    from neuromancer.predictive import FIRModel
    from neuromancer.supervisor import Deadline,atomic_json
    output.mkdir(parents=True,exist_ok=False)
    deadline=Deadline.from_environment()
    initial,_,_,inputs,rates=runpy.run_path('tests/test_predictive.py')['fixture']()
    rows=[]
    digests={}
    for pair in range(3):
        order=['original','compiled'] if pair%2==0 else ['compiled','original']
        for name in order:
            module=original if name=='original' else compiled
            model=FIRModel(initial.record,initial.information_inverse,'RLS')
            certificate=module.InformationCertificate(model.theta,model.p)
            latencies=[]
            began=time.perf_counter_ns();cpu=time.process_time_ns()
            for index in range(256):
                deadline.check()
                k=2400+index%100
                x=np.concatenate([inputs[k-lag] for lag in range(10)])
                tick=time.perf_counter_ns()
                certificate.update(model.standardized(x),rates[k]-model.record['output_mean'])
                model.update(x,rates[k])
                state=certificate.state(model.theta,model.p)
                if model.failure is not None:raise RuntimeError(model.failure)
                latencies.append(time.perf_counter_ns()-tick)
            digest=hashlib.sha256(b''.join(a.tobytes() for a in [certificate.information.center,
                certificate.information.radius,certificate.rhs.center,certificate.rhs.radius,
                state['coefficient_radius']])).hexdigest()
            if pair in digests and digests[pair]!=digest:
                raise RuntimeError('Optimized verification differs from M027 on fixed fixture')
            digests[pair]=digest
            rows.append(dict(pair=pair,backend=name,wall_s=(time.perf_counter_ns()-began)/1e9,
                cpu_s=(time.process_time_ns()-cpu)/1e9,latencies_ns=latencies,
                p50_ns=float(np.quantile(latencies,.5)),p95_ns=float(np.quantile(latencies,.95)),
                p99_ns=float(np.quantile(latencies,.99)),maximum_ns=max(latencies),digest=digest))
    result=dict(rows=rows,updates_per_sample=256,paired_samples=3,exact_certificate_equality=True,
                peak_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                release_qualified=False)
    atomic_json(output/'benchmark.json',result)
    print(json.dumps([{k:v for k,v in row.items() if k!='latencies_ns'} for row in rows]))
    return 0


def main(output,stage,backend):
    from neuromancer.supervisor import atomic_json
    if backend=='compiled':
        kernel=load_kernel()
        module=bounds(kernel)
    else:
        from tools import m027_residual_bounds as module
    if stage=='kernel':return kernel_benchmark(output,module)
    archive_driver=driver(module)
    if stage=='multi':
        class FixedMatrixJSON:
            @staticmethod
            def loads(value):
                data=json.loads(value)
                if isinstance(data,dict) and 'jobs' in data:data['jobs']=data['jobs'][:2]
                return data
            dumps=staticmethod(json.dumps)
        archive_driver.json=FixedMatrixJSON
        archive_driver.run(output,'all')
        result=json.loads((output/'certificate.json').read_text())
        passed=result['completed_branches']==4 and result['failure'] is None
        atomic_json(output/'component-qualification.json',dict(component='first-four-manifest-branches',
                    component_pass=passed,original_complete_study_result_retained=True,release_qualified=False))
        atomic_json(output/'backend.json',dict(query_cache=getattr(module,'query_cache_stats',{}),
                    denominators=getattr(archive_driver,'denominator_stats',{})))
        return 0 if passed else 1
    result=archive_driver.run(output,stage)
    atomic_json(output/'backend.json',dict(query_cache=getattr(module,'query_cache_stats',{}),
                denominators=getattr(archive_driver,'denominator_stats',{})))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--stage',choices=['kernel','256','first','dependency','multi','all'],required=True)
    parser.add_argument('--backend',choices=['original','compiled'],default='compiled')
    args=parser.parse_args()
    raise SystemExit(main(args.output,args.stage,args.backend))
