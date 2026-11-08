"""Isolated verification backend substitution; production modules are untouched."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import types

import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def load_kernel(directory=None):
    directory=Path(directory or os.environ['M028_KERNEL_DIR']).resolve()
    manifest=json.loads((directory.parent/'build.json').read_text())
    expected=hashlib.sha256((ROOT/'tools/m028_arithmetic.pyx').read_bytes()).hexdigest()
    if manifest['source_sha256']!=expected:
        raise RuntimeError('Compiled arithmetic source identity differs')
    candidates=list(directory.glob('m028_arithmetic*.so'))
    if len(candidates)!=1:raise RuntimeError('One explicit compiled verification kernel required')
    binary=candidates[0]
    if hashlib.sha256(binary.read_bytes()).hexdigest()!=manifest['artifacts'][binary.name]:
        raise RuntimeError('Compiled arithmetic binary identity differs')
    spec=importlib.util.spec_from_file_location('m028_arithmetic',binary)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.environment_check()
    return module


def bounds(kernel):
    # A distinct namespace keeps baseline tests/benchmarks independent. The
    # M027 proof/orchestration source remains byte-identical and inspectable.
    module=types.ModuleType('m028_verified_bounds')
    source=ROOT/'tools/m027_residual_bounds.py'
    exec(compile(source.read_text(),str(source),'exec'),module.__dict__)
    for name in ['Enclosure','gamma','positive_add','positive_multiply','upward']:
        module.__dict__[name]=getattr(kernel,name)
    if hasattr(kernel,'information_update'):
        class FusedInformation(module.InformationCertificate):
            def update(self,features,observed):
                s,rs,h,rh=kernel.information_update(self.information.center,self.information.radius,
                    self.rhs.center,self.rhs.radius,features,observed,float(self.forgetting.center))
                self.information=kernel.Enclosure(s,rs)
                self.rhs=kernel.Enclosure(h,rh)
                self.updates+=1

            def state(self,theta,covariance):
                if not hasattr(self,'_identity'):
                    self._identity=np.eye(self.size)
                    self._identity.flags.writeable=False
                return kernel.state_bounds(self.information.center,self.information.radius,
                    self.rhs.center,self.rhs.radius,theta,covariance,self._identity)
        module.InformationCertificate=FusedInformation
    return module


def driver(bound_module):
    source=ROOT/'tools/m027_certify.py'
    spec=importlib.util.spec_from_file_location('m028_verified_driver',source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ['InformationCertificate','residual_planner_costs','check_fixed_objective']:
        setattr(module,name,getattr(bound_module,name))
    return module
