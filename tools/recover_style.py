"""Run the frozen 12-pair M017 style workload with retained raw evidence."""
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time

import numpy as np
import psutil

WRAPPER = """
import json, runpy, sys
from pathlib import Path
from threadpoolctl import threadpool_info
script, output, reference = sys.argv[1:]
sys.argv = [script, output, '--neural', '--reference', reference]
runpy.run_path(script, run_name='__main__')
(Path(output) / 'threadpools.json').write_text(json.dumps(threadpool_info(), indent=2))
"""


def measure(side, source, output, reference):
    command = [str(source / 'env/bin/python'), '-c', WRAPPER,
               'scripts/m017_probe.py', str(output), str(reference)]
    env = dict(os.environ, PYTHONPATH=str(source / 'src'),
               VECLIB_MAXIMUM_THREADS='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    load_before = os.getloadavg()
    psutil.cpu_percent()
    start = time.monotonic_ns()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    peak = 0
    loads = []
    capped = False
    log = output.with_suffix('.log')
    with log.open('xb') as stream:
        child = subprocess.Popen(command, env=env, cwd=source, stdout=stream, stderr=stream)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, process.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            loads.append(psutil.cpu_percent())
            if peak > 2 * 1024**3:
                child.kill()
                capped = True
                break
            time.sleep(.05)
        code = child.wait()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    record = dict(side=side, exit=code, memory_cap_hit=capped,
                  elapsed_ns=time.monotonic_ns()-start,
                  cpu_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
                  load_before=load_before, load_after=os.getloadavg(),
                  system_cpu_samples=loads, sampled_rss_bytes=peak)
    if not code:
        measurement = json.loads((output / 'measurements.json').read_text())
        assert measurement['exact_equivalence']
        rss_factor = 1 if sys.platform == 'darwin' else 1024
        record['peak_rss_bytes'] = rss_factor * measurement['max_rss_native_units']
    output.with_suffix('.process.json').write_text(json.dumps(record, indent=2)+'\n')
    if code or record['peak_rss_bytes'] > 2 * 1024**3:
        raise RuntimeError(f'{side} resource or exact-output gate failed. See {log}')


def results(root):
    rng = np.random.default_rng(18017)
    draws = rng.integers(0, 12, size=(10000, 12))
    sides = ('baseline', 'style')
    raw = {side: [json.loads((root / f'{i:02d}-{side}' / 'measurements.json').read_text())
                  for i in range(12)] for side in sides}
    table = {}
    for key in raw['baseline'][0]['timings']:
        if key == 'brain_engineering':
            continue
        table[key] = {}
        for clock in ('wall_ns', 'cpu_ns'):
            b, s = (np.array([r['timings'][key][clock] for r in raw[side]]) for side in sides)
            row = dict(pair_median_ratios=(np.median(s, axis=1)/np.median(b, axis=1)).tolist())
            for q in (50, 95, 99):
                baseline = np.percentile(b, q)
                candidate = np.percentile(s, q)
                boot = (np.percentile(s[draws].reshape(10000, -1), q, axis=1)
                        / np.percentile(b[draws].reshape(10000, -1), q, axis=1))
                row[str(q)] = dict(baseline_ms=float(baseline/1e6), style_ms=float(candidate/1e6),
                                   ratio=float(candidate/baseline),
                                   interval=np.percentile(boot, [2.5, 97.5]).tolist(),
                                   order_ratios=[float(np.percentile(s[j::2], q)
                                                       / np.percentile(b[j::2], q))
                                                 for j in range(2)])
            table[key][clock] = row
    process = {side: [json.loads((root / f'{i:02d}-{side}.process.json').read_text())
                      for i in range(12)] for side in sides}
    b, s = (np.array([r['peak_rss_bytes'] for r in process[side]]) for side in sides)
    peak_boot = np.max(s[draws], axis=1)/np.max(b[draws], axis=1)
    table['peak_rss'] = dict(baseline=int(b.max()), style=int(s.max()),
                             ratio=float(s.max()/b.max()),
                             interval=np.percentile(peak_boot, [2.5, 97.5]).tolist())
    (root / 'statistics.json').write_text(json.dumps(table, indent=2)+'\n')


def main(source, output, reference):
    output.mkdir()
    environment = dict(platform=platform.platform(), python=sys.version, workers=1,
                       probe_sha256={}, env={}, revisions={
                           'baseline': '4ec262486ab953591b90c860dd3515ce531789b7',
                           'style': 'f5703ce048c30ac4fa050c5b5f9bde3e3b73c296',
                       })
    for side in ('baseline', 'style'):
        environment['probe_sha256'][side] = hashlib.sha256(
            (source / side / 'scripts/m017_probe.py').read_bytes()).hexdigest()
        environment['env'][side] = (source / side / 'environment.txt').read_text()
    assert len(set(environment['probe_sha256'].values())) == 1
    assert len(set(environment['env'].values())) == 1
    (output / 'environment.json').write_text(json.dumps(environment, indent=2)+'\n')
    for pair in range(12):
        order = ('baseline', 'style') if pair % 2 == 0 else ('style', 'baseline')
        for side in order:
            measure(side, source / side, output / f'{pair:02d}-{side}', reference)
    results(output)


if __name__ == '__main__':
    main(*(Path(value).resolve() for value in sys.argv[1:]))
