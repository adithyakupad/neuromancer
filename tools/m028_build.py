"""Build the verification-only extension outside the installable research wheel."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main(output):
    output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[1]
    setup=output/'setup.py'
    setup.write_text('''from setuptools import setup,Extension
from Cython.Build import cythonize
from Cython.Compiler import Options
Options.warning_errors=True
setup(name="neuromancer-verification-kernels",ext_modules=cythonize([
    Extension("m028_arithmetic",[%r],extra_compile_args=["-O3","-fno-fast-math","-ffp-contract=off","-frounding-math"])
],build_dir=%r,compiler_directives={"language_level":3,"boundscheck":False,"wraparound":True,"cdivision":True}))
'''%(str(root/'tools/m028_arithmetic.pyx'),str(output/'generated')))
    started=time.monotonic()
    with (output/'build.log').open('wb') as log:
        result=subprocess.run([sys.executable,str(setup),'build_ext','--build-lib',str(output/'lib'),'--build-temp',str(output/'objects')],stdout=log,stderr=subprocess.STDOUT,cwd=output,timeout=110)
    manifest=dict(returncode=result.returncode,wall_s=time.monotonic()-started,
                  source_sha256=hashlib.sha256((root/'tools/m028_arithmetic.pyx').read_bytes()).hexdigest(),
                  flags=['-O3','-fno-fast-math','-ffp-contract=off','-frounding-math'],artifacts={})
    for path in (output/'lib').glob('*'):
        manifest['artifacts'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest['generated_sources']={str(path.relative_to(output)):hashlib.sha256(path.read_bytes()).hexdigest()
                                   for path in (output/'generated').rglob('*.c')}
    (output/'build.json').write_text(json.dumps(manifest,indent=2))
    return result.returncode


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    raise SystemExit(main(parser.parse_args().output.resolve()))
