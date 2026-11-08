"""Isolated verification backend substitution; production modules are untouched."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import types
import ast
from collections import OrderedDict,deque

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
        module.covariance_certificates=deque(maxlen=4)
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
                result=kernel.state_bounds(self.information.center,self.information.radius,
                    self.rhs.center,self.rhs.radius,theta,covariance,self._identity)
                module.covariance_certificates.append((covariance,np.array(covariance,copy=True),result['covariance_radius']))
                return result
        module.InformationCertificate=FusedInformation
    # Queries depend on fixed normalization/history/bank, never model state.
    original_query=module.planner_queries
    cache=OrderedDict()
    stats=dict(hits=0,misses=0)
    def cached_queries(record,history,delivered):
        mean=np.asarray(record['mean'],dtype=np.float64)
        scale=np.asarray(record['scale'],dtype=np.float64)
        history=np.asarray(history,dtype=np.float64)
        delivered=np.asarray(delivered)
        if mean.shape!=(40,) or scale.shape!=(40,) or history.shape!=(9,4) or delivered.shape!=(625,100) or delivered.dtype!=np.float64:
            raise ValueError('Invalid immutable query dimensions or dtype')
        key=(mean.tobytes(),scale.tobytes(),history.tobytes(),delivered.dtype.str,delivered.shape)
        if key in cache:
            query,stored=cache[key]
            if not np.array_equal(stored.view(np.uint64),delivered.view(np.uint64)):
                raise ValueError('Same declared query inputs produced a different candidate bank')
            cache.move_to_end(key);stats['hits']+=1
            return query
        query=original_query(record,history,delivered)
        query.center.flags.writeable=False;query.radius.flags.writeable=False
        stored=delivered.copy();stored.flags.writeable=False
        cache[key]=(query,stored)
        if len(cache)>32:cache.popitem(last=False)
        stats['misses']+=1
        return query
    module.planner_queries=cached_queries
    module.query_cache_stats=stats
    module.compiled_kernel=kernel
    return module


def driver(bound_module):
    source=ROOT/'tools/m027_certify.py'
    tree=ast.parse(source.read_text(),filename=str(source))
    replacements=0
    # Shadow only the verifier's local artifact writer. Production supervisor
    # objects and its own persistence function are never patched.
    class WriterImport(ast.NodeTransformer):
        def visit_ImportFrom(self,node):
            nonlocal replacements
            if node.module=='neuromancer.supervisor' and any(a.name=='atomic_json' for a in node.names):
                replacements+=1
                return [ast.ImportFrom(module=node.module,names=[a for a in node.names if a.name!='atomic_json'],level=0),
                        ast.ImportFrom(module='tools.m028_io',names=[ast.alias(name='atomic_json')],level=0)]
            if node.module=='neuromancer.predictive' and any(a.name=='FIRModel' for a in node.names) and hasattr(bound_module,'compiled_kernel'):
                return ast.Assign(targets=[ast.Name(id='FIRModel',ctx=ast.Store())],
                                  value=ast.Name(id='_checked_model_type',ctx=ast.Load()))
            return node
    tree=WriterImport().visit(tree)
    if replacements!=1:raise RuntimeError('Unexpected M027 verifier writer boundary')
    module=types.ModuleType('m028_verified_driver')
    module.__file__=str(source)
    if hasattr(bound_module,'compiled_kernel'):
        from neuromancer.predictive import FIRModel as OriginalModel
        denominator_stats=dict(count=0,minimum_lower=None)
        class CheckedModel(OriginalModel):
            def update(self,x,y,valid=True):
                if valid and self.failure is None and self.kind=='RLS':
                    radius=None
                    for array,snapshot,value in reversed(bound_module.covariance_certificates):
                        if array is self.p:
                            if not np.array_equal(array,snapshot):raise ValueError('Certified covariance was mutated')
                            radius=value;break
                    if radius is None:
                        if self.updates:raise ValueError('Missing continuous covariance certificate')
                        radius=0. # The shared archived initialization is exact.
                    lower=bound_module.compiled_kernel.denominator_lower(self.standardized(x),self.p,.999,radius)
                    self.certified_denominator_lower=lower
                    denominator_stats['count']+=1
                    previous=denominator_stats['minimum_lower']
                    denominator_stats['minimum_lower']=lower if previous is None else min(previous,lower)
                return super().update(x,y,valid)
        module._checked_model_type=CheckedModel
        module.denominator_stats=denominator_stats
        from tools import m028_io
        m028_io.EXTRA_PROGRESS=denominator_stats
    exec(compile(ast.fix_missing_locations(tree),str(source),'exec'),module.__dict__)
    for name in ['InformationCertificate','residual_planner_costs','check_fixed_objective']:
        setattr(module,name,getattr(bound_module,name))
    return module
