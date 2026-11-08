"""Independent high-precision and M027 comparisons of compiled verification."""
from decimal import Decimal,localcontext
import os
from pathlib import Path
import subprocess
import sys
import runpy
import types

import numpy as np
import pytest

from tools.m028_backend import load_kernel,bounds
from tools import m027_residual_bounds as original
from tools.portable_numeric_verification import CertificateFailure


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    if 'M028_KERNEL_DIR' in os.environ:return load_kernel()
    output=tmp_path_factory.mktemp('compiled')/'build'
    subprocess.run([sys.executable,'tools/m028_build.py',str(output)],check=True,timeout=115)
    return load_kernel(output/'lib')


@pytest.mark.parametrize('shape', [(),(4,),(3,4),(41,41)])
def test_same_center_radius_elementwise_and_product(kernel,shape):
    rng=np.random.default_rng(2801)
    values=rng.normal(size=shape)
    radius=np.full(shape,1e-8)
    old=original.Enclosure(values,radius)
    new=kernel.Enclosure(values,radius)
    for name in ['add','subtract','multiply','divide_positive']:
        other=np.full(shape,2.)
        left=getattr(old,name)(original.Enclosure(other,1e-9))
        right=getattr(new,name)(kernel.Enclosure(other,1e-9))
        np.testing.assert_array_equal(left.center,right.center)
        np.testing.assert_array_equal(left.radius,right.radius)
    if shape==(41,41):
        left=old.product(old.transpose);right=new.product(new.transpose)
        np.testing.assert_array_equal(left.center,right.center)
        np.testing.assert_array_equal(left.radius,right.radius)


def test_decimal_cancellation_gain_covariance_and_steps(kernel):
    Ball=kernel.Enclosure
    with localcontext() as context:
        context.prec=90
        z=Ball(np.array([[1.],[.125]]));p=Ball(np.diag([1.,1e6]));theta=Ball(np.zeros((2,1)))
        exact_p=[[Decimal(1),Decimal(0)],[Decimal(0),Decimal(1000000)]]
        exact_theta=[Decimal(0),Decimal(0)]
        lam=Decimal.from_float(.999)
        exact_z=[Decimal(1),Decimal('.125')]
        for step in range(32):
            zp=z.transpose.product(p)
            gain=p.product(z).divide_positive(Ball(.999).add(zp.product(z)))
            exact_zp=[sum(exact_z[i]*exact_p[i][j] for i in range(2)) for j in range(2)]
            denominator=lam+sum(exact_zp[i]*exact_z[i] for i in range(2))
            exact_gain=[sum(exact_p[i][j]*exact_z[j] for j in range(2))/denominator for i in range(2)]
            residual=Decimal(1)-sum(exact_z[i]*exact_theta[i] for i in range(2))
            exact_theta=[exact_theta[i]+exact_gain[i]*residual for i in range(2)]
            exact_p=[[(exact_p[i][j]-exact_gain[i]*exact_zp[j])/lam for j in range(2)] for i in range(2)]
            exact_p=[[(exact_p[i][j]+exact_p[j][i])/2 for j in range(2)] for i in range(2)]
            theta=theta.add(gain.product(Ball([[1.]]).subtract(z.transpose.product(theta))))
            p=p.subtract(gain.product(zp)).divide_positive(Ball(.999))
            p=p.add(p.transpose).divide_positive(Ball(2.))
            for ball,expected in [(gain,exact_gain),(theta,exact_theta),(p,np.array(exact_p,dtype=object).ravel())]:
                lo=np.nextafter(ball.center-ball.radius,-np.inf).ravel()
                hi=np.nextafter(ball.center+ball.radius,np.inf).ravel()
                assert all(Decimal.from_float(float(a))<=b<=Decimal.from_float(float(c)) for a,b,c in zip(lo,expected,hi))


def test_domains_and_no_contraction(kernel):
    Ball=kernel.Enclosure
    tiny=np.finfo(float).tiny
    for value in [np.nan,np.inf,np.nextafter(0.,1.)]:
        with pytest.raises(CertificateFailure):Ball(value)
    with pytest.raises(CertificateFailure):Ball(1.).divide_positive(Ball(0.))
    with pytest.raises(CertificateFailure):Ball(tiny).multiply(Ball(tiny))
    with pytest.raises(CertificateFailure):Ball(1e308).multiply(Ball(1e308))
    zero=Ball(np.zeros(4)).product(Ball(np.zeros(4)))
    assert float(zero.radius)==0
    product=Ball(1+2.**-27).multiply(Ball(1-2.**-27)).add(Ball(-1.))
    assert float(product.center)==0. # An FMA would produce -2^-54.
    assert kernel.environment_check()['round_to_nearest']


def test_information_no_reset_and_original_match(kernel):
    compiled=bounds(kernel)
    theta=np.zeros((3,2));p=np.eye(3)
    old=original.InformationCertificate(theta,p)
    new=compiled.InformationCertificate(theta,p)
    for index in range(65):
        z=np.array([1.,(index%3)/4,-.25]);v=np.array([.5,-.25])
        old.update(z,v);new.update(z,v)
        np.testing.assert_array_equal(old.information.center,new.information.center)
        np.testing.assert_array_equal(old.information.radius,new.information.radius)
        np.testing.assert_array_equal(old.rhs.radius,new.rhs.radius)
    assert new.updates==65
    assert original.Enclosure is not compiled.Enclosure


@pytest.mark.parametrize('name,args',[
    ('test_gain_covariance_and_coefficient_against_decimal',(False,)),
    ('test_gain_covariance_and_coefficient_against_decimal',(True,)),
    ('test_functional_residual_keeps_information_history',()),
    ('test_prediction_and_objective_decimal_enclosure',()),
    ('test_full_planner_cost_bound_with_independent_decimal_candidate',()),
])
def test_independent_m027_decimal_cases_on_compiled_backend(kernel,name,args):
    # Reuse the independent Decimal oracle verbatim, substituting only the
    # implementation under test in a separate function-global namespace.
    reference=runpy.run_path('tests/test_m027_residual_bounds.py')[name]
    module=bounds(kernel)
    namespace=dict(reference.__globals__)
    for key in ['InformationCertificate','Enclosure','objective_from_means','residual_planner_costs']:
        namespace[key]=getattr(module,key)
    tested=types.FunctionType(reference.__code__,namespace)
    tested(*args)


def test_immutable_query_cache_requires_same_inputs(kernel):
    from neuromancer.predictive_planner import bank
    module=bounds(kernel)
    record=dict(mean=np.zeros(40),scale=np.ones(40))
    history=np.zeros((9,4));delivered=bank(0.)[2]
    first=module.planner_queries(record,history,delivered)
    second=module.planner_queries(record,history,delivered)
    assert first is second and module.query_cache_stats==dict(hits=1,misses=1)
    expected=original.planner_queries(record,history,delivered)
    assert first.center.tobytes()==expected.center.tobytes()
    assert first.radius.tobytes()==expected.radius.tobytes()
    changed=delivered.copy();changed[0,0]=1.
    with pytest.raises(ValueError,match='different candidate bank'):
        module.planner_queries(record,history,changed)
    record['scale'][0]=2.
    third=module.planner_queries(record,history,delivered)
    assert third is not first


def test_positive_denominator_lower_is_independent_decimal_bound(kernel):
    z=np.array([1.,.125]);p=np.diag([1.,1e6])
    exact=Decimal(1)+Decimal(15625)+Decimal.from_float(.999)
    lower=kernel.denominator_lower(z,p)
    assert 0 < Decimal.from_float(lower) <= exact
    assert kernel.denominator_lower(np.zeros(2),p) > .998
    with pytest.raises(CertificateFailure,match='positive RLS denominator'):
        kernel.denominator_lower(np.ones(2),-100*np.eye(2))
