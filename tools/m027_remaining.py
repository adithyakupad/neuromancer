"""Run original remaining gates, with one inherited deadline and honest stops."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def run(output):
    from neuromancer.supervisor import Deadline, atomic_json
    output.mkdir(parents=True, exist_ok=False)
    deadline = Deadline.from_environment()
    commands = [
        [sys.executable, 'tools/m027_fit_svd.py', str(output/'fixed-fit-svd')],
        [sys.executable, 'scripts/m017_probe.py', str(output/'golden'), '--neural',
         '--reference', 'reports/engineering/evidence/m017/golden_final'],
        [sys.executable, 'scripts/reproduce_v1_evidence.py', '--output', str(output/'v1')],
        [sys.executable, 'scripts/m017_reproduce.py', str(output/'archives')],
    ]
    rows = []
    for index, command in enumerate(commands):
        deadline.check()
        with (output/f'command-{index}.log').open('wb') as stream:
            # Descendants share the supervisor's process group and original deadline.
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
        rows.append(dict(command=command, returncode=result.returncode))
        atomic_json(output/'progress.json', dict(commands=rows, release_qualified=False))
        if result.returncode:
            atomic_json(output/'certificate.json', dict(remaining_gates_pass=False,
                failure='Existing exact gate failed or a portable subcertificate is incomplete',
                commands=rows, release_qualified=False))
            return 1
    deadline.check()
    atomic_json(output/'certificate.json', dict(remaining_gates_pass=True, commands=rows,
        scope='Fixed residual/spectral checks and original exact replay on this host',
        cross_platform_release_qualified=False, release_qualified=False))
    return 0


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    raise SystemExit(run(parser.parse_args().output))
