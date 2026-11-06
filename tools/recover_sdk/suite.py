"""Fixed SDK-only comparisons under the existing external watchdog."""
import json
import os
from pathlib import Path
import subprocess
import sys

TOOLS = Path(__file__).resolve().parent
CASES = [('unmodified', 'after', 4), ('traced', 'after', 4),
         ('before', 'before', 3), ('after', 'after', 3), ('bounded', 'bounded', 3)]


def main(root):
    root.mkdir(parents=True, exist_ok=False)
    shadow = root / 'shadow'
    subprocess.run([sys.executable, str(TOOLS / 'shadow.py'), str(shadow)], check=True)
    outcomes = {}
    for name, mode, sessions in CASES:
        output = root / name
        env = dict(os.environ, CL_SDK_ACCELERATED_TIME='1', CL_SDK_VISUALISATION='0')
        env.pop('CL_SDK_REPLAY_PATH', None)
        paths = [str(TOOLS), str(Path('src').resolve())]
        if name == 'traced':
            paths.insert(0, str(shadow))
        env['PYTHONPATH'] = os.pathsep.join(paths)
        command = [sys.executable, 'scripts/m016_watch.py', str(output), '120',
                   sys.executable, str(TOOLS / 'probe.py'), str(output), mode, str(sessions)]
        result = subprocess.run(command, env=env, check=False)
        cleanup = False
        state = None
        if (output / 'returned.json').exists() and (root / f'{name}_descendants.json').exists():
            state = json.loads((output / 'returned.json').read_text())['status']
            watchdog = json.loads((root / f'{name}_descendants.json').read_text())
            cleanup = (json.loads((output / 'returned.json').read_text())['cleanup_verified']
                       and not watchdog['timed_out'] and not watchdog['forced_cleanup_pids']
                       and not watchdog['remaining'])
        outcomes[name] = dict(exit=result.returncode, status=state, cleanup=cleanup,
                              completed=len(list(output.glob('session-*/complete'))))
        (root / 'outcomes.json').write_text(json.dumps(outcomes, indent=2) + '\n')
        if not cleanup:
            break
    # The derivative SDK copy is transient and is excluded from upload.
    return int(any(row['exit'] or not row['cleanup'] for row in outcomes.values()))


if __name__ == '__main__':
    raise SystemExit(main(Path(sys.argv[1]).resolve()))
