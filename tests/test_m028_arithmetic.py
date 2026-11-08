"""Independent high-precision and M027 comparisons of compiled verification."""
from decimal import Decimal,localcontext
import os
from pathlib import Path
import subprocess
import sys

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
