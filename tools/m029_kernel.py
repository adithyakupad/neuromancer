"""Source-bound M028 overlay for deterministic four-output proof products."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
FLAGS = ['-O3', '-fno-fast-math', '-ffp-contract=off', '-frounding-math']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def compose():
    original = (ROOT/'tools/m028_arithmetic.pyx').read_text()
    extra = (ROOT/'tools/m029_dot4.pyx').read_text()
    changes = {
        'def positive_product(a,b):': 'def positive_product(a,b,ordered=False):',
        'return upward((a@b)/(1-gamma(a.shape[-1])))':
            'return upward((ordered_dot4(a,b) if ordered else a@b)/(1-gamma(a.shape[-1])))',
        '    center_product=left@right\n    uncertain=positive_product(left_radius,np.abs(right))\n'
        '    absolute=positive_product(np.abs(left),np.abs(right))':
            '    ordered = right.ndim == 2 and right.shape[1] == 4\n'
            '    center_product = ordered_dot4(left,right) if ordered else left@right\n'
            '    uncertain = positive_product(left_radius,np.abs(right),ordered)\n'
            '    absolute = positive_product(np.abs(left),np.abs(right),ordered)',
    }
    source = original
    for old, new in changes.items():
        if source.count(old) != 1:
            raise ValueError('M028 kernel overlay boundary differs')
        source = source.replace(old, new)
    return (source+'\n'+extra).encode()


def build(output):
    output.mkdir(parents=True, exist_ok=False)
    source = output/'m029_arithmetic.pyx'
    source.write_bytes(compose())
    setup = output/'setup.py'
    setup.write_text(f'''from setuptools import Extension, setup
from Cython.Build import cythonize
from Cython.Compiler import Options
Options.warning_errors = True
setup(name='neuromancer-m029-verification', ext_modules=cythonize([
    Extension('m029_arithmetic', [{str(source)!r}], extra_compile_args={FLAGS!r})
]))
''')
    started = time.monotonic()
    with (output/'build.log').open('wb') as log:
        result = subprocess.run([sys.executable, str(setup), 'build_ext', '--build-lib', str(output/'lib')],
                                stdout=log, stderr=subprocess.STDOUT, cwd=output, timeout=110)
    binaries = {p.name: digest(p.read_bytes()) for p in (output/'lib').glob('*.so')}
    record = dict(returncode=result.returncode, composed_sha256=digest(source.read_bytes()),
                  generated_c_sha256=digest(source.with_suffix('.c').read_bytes())
                  if source.with_suffix('.c').exists() else None,
                  artifacts=binaries, flags=FLAGS, wall_s=time.monotonic()-started)
    (output/'build.json').write_text(json.dumps(record, indent=2)+'\n')
    return result.returncode


def load(directory=None):
    directory = Path(directory or os.environ['M029_KERNEL_DIR']).resolve()
    record = json.loads((directory.parent/'build.json').read_text())
    binaries = list(directory.glob('m029_arithmetic*.so'))
    if record['returncode'] or record['composed_sha256'] != digest(compose()) or len(binaries) != 1:
        raise ValueError('Ordered residual kernel provenance differs')
    binary = binaries[0]
    if digest(binary.read_bytes()) != record['artifacts'][binary.name]:
        raise ValueError('Ordered residual binary hash differs')
    spec = importlib.util.spec_from_file_location('m029_arithmetic', binary)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.environment_check()
    return module


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=lambda path: Path(path).resolve())
    parser.add_argument('--prerequisite', action='store_true')
    args = parser.parse_args()
    if args.prerequisite:
        sys.path.insert(0, str(ROOT))
        from tools.m028_backend import bounds, driver

        sys.exit(driver(bounds(load())).run(args.output, '256'))
    sys.exit(build(args.output))
