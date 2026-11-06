"""Run the frozen M019 matrix once, retaining failed and incomplete cases."""
import json
from pathlib import Path
import subprocess
import sys

from m019_probe import CONDITIONS


def main(root):
    root.mkdir(parents=True, exist_ok=False)
    outcomes = {}
    for condition in CONDITIONS:
        output = root / condition
        command = [sys.executable, 'scripts/m016_watch.py', str(output), '120',
                   sys.executable, 'scripts/m019_probe.py', str(output), condition, '3']
        returncode = subprocess.run(command, check=False).returncode
        try:
            supervisor = json.loads((output / 'returned.json').read_text())
            watchdog = json.loads(output.with_name(condition + '_descendants.json').read_text())
            worker_log = (output / 'supervision/worker-0.log').read_text()
            cleanup = ('Observer needed forced cleanup' not in worker_log
                       and supervisor['cleanup_verified'] and not watchdog['timed_out']
                       and not watchdog['forced_cleanup_pids'] and not watchdog['remaining'])
        except (OSError, ValueError, KeyError):
            cleanup = False
        outcomes[condition] = dict(returncode=returncode, cleanup_verified=cleanup,
                                   completed=len(list(output.glob('session-*/complete'))))
        (root / 'outcomes.json').write_text(json.dumps(outcomes, indent=2) + '\n')
        if not cleanup:
            break
    return int(len(outcomes) != len(CONDITIONS) or
               any(x['returncode'] or not x['cleanup_verified'] for x in outcomes.values()))


if __name__ == '__main__':
    raise SystemExit(main(Path(sys.argv[1]).resolve()))
