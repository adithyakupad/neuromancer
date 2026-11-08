"""One prospective worker-count matrix followed by one full qualification."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from m029_parallel import ROOT, THREADS, head, launch, read

sys.path.insert(0, str(ROOT))
from neuromancer.supervisor import atomic_json


def capacity():
    cpus = len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else os.cpu_count()
    if sys.platform == 'darwin':
        memory = int(subprocess.check_output(['sysctl', '-n', 'hw.memsize']))
    else:
        memory = os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')
        limit = Path('/sys/fs/cgroup/memory.max')
        if limit.exists() and limit.read_text().strip() != 'max':
            memory = min(memory, int(limit.read_text()))
        quota = Path('/sys/fs/cgroup/cpu.max')
        if quota.exists():
            budget, period = quota.read_text().split()
            if budget != 'max':
                cpus = min(cpus, max(1, int(budget) // int(period)))
    return cpus, memory


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    cpus, memory = capacity()
    counts = [n for n in (1, 2, 4) if n <= cpus and n * 1024**3 <= memory]
    os.environ.update(dict.fromkeys(THREADS, '1'))
    with (output / 'numerical-runtime.txt').open('w') as stream:
        subprocess.run([sys.executable, '-c', 'import numpy as np; np.show_config(); np.show_runtime()'],
                       stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=20)
    plan = dict(source=head(), cpus=cpus, memory_bytes=memory, worker_counts=counts,
                component_branches=8, component_limit_s=180, full_limit_s=240)
    atomic_json(output / 'plan.json', plan)
    if not counts:
        return 1
    reference = None
    measures = []
    for count in counts:
        directory = output / f'workers-{count}'
        if launch(directory, count, 8):
            atomic_json(output / 'selection.json', dict(failure=f'Component failed with {count} workers'))
            return 1
        report = read(directory / 'stage.json')
        digests = [(row['branch'], row['numerical_sha256']) for row in report['rows']]
        if reference is not None and digests != reference:
            atomic_json(output / 'selection.json', dict(failure='Worker-count numerical fingerprints differ'))
            return 1
        reference = digests
        measures.append((read(directory / 'launcher.json')['wall_s'], count))
    fastest = min(measures)[1]
    atomic_json(output / 'selection.json', dict(measures=measures, workers=fastest,
                component_fingerprints_equal=True))
    code = launch(output / 'full', fastest, 40)
    if code:
        return code
    full = read(output / 'full/stage.json')
    if [(r['branch'], r['numerical_sha256']) for r in full['rows'][:8]] != reference:
        raise ValueError('Full stage differs from component fingerprints')
    atomic_json(output / 'qualification.json', dict(source=plan['source'], passed=True, workers=fastest,
                branches=40, updates=128000, plans=2560, release_qualified=False))
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=lambda value: Path(value).resolve())
    sys.exit(run(parser.parse_args().output))
