# cython: language_level=3, boundscheck=False, wraparound=True, cdivision=True
"""Verification-only IEEE binary64 interval kernels. No production imports change."""
from libc.math cimport fabs, isfinite, nextafter, INFINITY
from libc.float cimport DBL_MIN
cdef extern from "fenv.h":
    int fegetround()
    int FE_TONEAREST
import numpy as np
from functools import lru_cache
from tools.portable_numeric_verification import CertificateFailure

UNIT_ROUNDOFF = np.finfo(np.float64).eps/2

def environment_check():
    if sizeof(double) != 8 or fegetround() != FE_TONEAREST:
        raise CertificateFailure('Compiled verifier requires binary64 round-to-nearest')
    return dict(double_bytes=sizeof(double), round_to_nearest=True, fast_math=False,
                fma_contraction=False, subnormal_inputs_supported=False)

cdef double normal_up(double value) except -1.0:
    if not isfinite(value) or value < 0:
        raise CertificateFailure('Nonfinite or negative radius')
    if value == 0:
        return 0
    if value < DBL_MIN:
        raise CertificateFailure('Radius underflow needs a separate arithmetic model')
    value = nextafter(value, INFINITY)
    if not isfinite(value):
        raise CertificateFailure('Outward radius overflow')
    return value

def upward(value):
    a = np.asarray(value, dtype=np.float64)
    cdef const double[::1] source = np.ascontiguousarray(a).reshape(-1)
    result = np.empty(a.size, dtype=np.float64)
    cdef double[::1] target = result
    cdef Py_ssize_t i
    for i in range(source.shape[0]):
        target[i] = normal_up(source[i])
    return result.reshape(a.shape)

def binary(a, b, int operation):
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if a.shape != b.shape and a.ndim != 0 and b.ndim != 0:
        a, b = np.broadcast_arrays(a,b)
    shape = b.shape if a.ndim == 0 else a.shape
    cdef const double[::1] left = np.ascontiguousarray(a).reshape(-1)
    cdef const double[::1] right = np.ascontiguousarray(b).reshape(-1)
    result = np.empty(int(np.prod(shape)), dtype=np.float64)
    cdef double[::1] target = result
    cdef Py_ssize_t i
    cdef double x, y, value
    cdef bint scalar_left = a.ndim == 0, scalar_right = b.ndim == 0
    for i in range(target.shape[0]):
        x, y = left[0 if scalar_left else i], right[0 if scalar_right else i]
        if not isfinite(x) or not isfinite(y):
            raise CertificateFailure('Nonfinite arithmetic input')
        if operation == 0:
            if x < 0 or y < 0:
                raise CertificateFailure('Negative radius addition')
            value = normal_up(x+y)
        elif operation == 1:
            if x < 0 or y < 0:
                raise CertificateFailure('Negative radius product')
            value = x*y
            if x > 0 and y > 0 and value < DBL_MIN:
                raise CertificateFailure('Radius product underflow needs a separate arithmetic model')
            value = normal_up(value)
        elif operation == 2:
            if y == 0:
                raise CertificateFailure('Zero division')
            value = x/y
            if not isfinite(value):
                raise CertificateFailure('Nonfinite division')
            if x != 0 and fabs(value) < DBL_MIN:
                raise CertificateFailure('Division underflow needs a separate arithmetic model')
        elif operation == 3:
            value = x*y
            if x != 0 and y != 0 and fabs(value) < DBL_MIN:
                raise CertificateFailure('Product underflow needs a separate arithmetic model')
            if not isfinite(value):
                raise CertificateFailure('Nonfinite center product')
        else:
            value = x+y
            if value == 0 and x != -y:
                raise CertificateFailure('Addition underflow or non-IEEE arithmetic')
            if not isfinite(value):
                raise CertificateFailure('Nonfinite center addition')
        target[i] = value
    return result.reshape(shape)

def is_zero(value):
    cdef const double[::1] data=np.ascontiguousarray(value,dtype=np.float64).reshape(-1)
    cdef Py_ssize_t i
    for i in range(data.shape[0]):
        if data[i] != 0:return False
    return True

def positive_add(a,b):
    return binary(a,b,0)

def positive_multiply(a,b):
    return binary(a,b,1)

def checked_divide(a,b):
    return binary(a,b,2)

@lru_cache(maxsize=64)
def gamma(length):
    error = length*UNIT_ROUNDOFF
    if not 0 <= error < 1:
        raise CertificateFailure('Dot-product error model is invalid')
    return float(np.nextafter(error/(1-error), np.inf))

def positive_product(a,b):
    a, b = np.asarray(a,dtype=np.float64), np.asarray(b,dtype=np.float64)
    cdef const double[::1] left = np.ascontiguousarray(a).reshape(-1)
    cdef const double[::1] right = np.ascontiguousarray(b).reshape(-1)
    cdef double minimum_a=INFINITY, minimum_b=INFINITY, value
    cdef Py_ssize_t i
    for i in range(left.shape[0]):
        value=left[i]
        if value < 0 or not isfinite(value):
            raise CertificateFailure('Invalid nonnegative dot product')
        if value > 0 and value < minimum_a: minimum_a=value
    for i in range(right.shape[0]):
        value=right[i]
        if value < 0 or not isfinite(value):
            raise CertificateFailure('Invalid nonnegative dot product')
        if value > 0 and value < minimum_b: minimum_b=value
    if minimum_a < INFINITY and minimum_b < INFINITY and minimum_a < DBL_MIN/minimum_b:
        raise CertificateFailure('Dot-product underflow needs a separate arithmetic model')
    return upward((a@b)/(1-gamma(a.shape[-1])))

def validate(center,radius):
    cdef const double[::1] c=np.ascontiguousarray(center).reshape(-1)
    cdef const double[::1] r=np.ascontiguousarray(radius).reshape(-1)
    cdef Py_ssize_t i
    cdef double x,y
    if c.shape[0] != r.shape[0]:
        raise CertificateFailure('Mismatched enclosure storage')
    for i in range(c.shape[0]):
        x,y=c[i],r[i]
        if not isfinite(x) or not isfinite(y) or y < 0:
            raise CertificateFailure('Invalid enclosure')
        if x != 0 and fabs(x) < DBL_MIN:
            raise CertificateFailure('Subnormal center needs a separate underflow model')
        if y != 0 and y < DBL_MIN:
            raise CertificateFailure('Radius underflow needs a separate arithmetic model')

class Enclosure:
    def __init__(self,center,radius=0.):
        self.center=np.asarray(center,dtype=np.float64)
        self.radius=np.broadcast_to(np.asarray(radius,dtype=np.float64),self.center.shape).copy()
        validate(self.center,self.radius)

    def reshape(self,shape):
        return Enclosure(self.center.reshape(shape),self.radius.reshape(shape))

    @property
    def transpose(self):
        return Enclosure(self.center.T,self.radius.T)

    def part(self,item):
        return Enclosure(self.center[item],self.radius[item])

    def negative(self):
        return Enclosure(-self.center,self.radius)

    def add(self,other):
        center=binary(self.center,other.center,4)
        rounding=positive_multiply(2*UNIT_ROUNDOFF/(1-UNIT_ROUNDOFF),np.abs(center))
        radius=positive_add(positive_add(self.radius,other.radius),rounding)
        return Enclosure(center,radius)

    def subtract(self,other):
        return self.add(other.negative())

    def multiply(self,other):
        center=binary(self.center,other.center,3)
        radius=positive_add(positive_multiply(np.abs(self.center),other.radius),positive_multiply(self.radius,np.abs(other.center)))
        radius=positive_add(radius,positive_multiply(self.radius,other.radius))
        rounding=positive_multiply(2*UNIT_ROUNDOFF/(1-UNIT_ROUNDOFF),np.abs(center))
        return Enclosure(center,positive_add(radius,rounding))

    def product(self,other):
        center=self.center@other.center
        # Multiplying a finite array by an exactly zero radius gives exact zero.
        # Keep the original subsequent outward additions, preserving M027 bytes.
        left_zero=is_zero(self.radius);right_zero=is_zero(other.radius)
        first=np.zeros_like(center) if right_zero else positive_product(np.abs(self.center),other.radius)
        second=np.zeros_like(center) if left_zero else positive_product(self.radius,np.abs(other.center))
        cross=np.zeros_like(center) if left_zero or right_zero else positive_product(self.radius,other.radius)
        radius=positive_add(first,second)
        radius=positive_add(radius,cross)
        rounding=positive_multiply(2*gamma(self.center.shape[-1]),positive_product(np.abs(self.center),np.abs(other.center)))
        return Enclosure(center,positive_add(radius,rounding))

    def divide_positive(self,denominator):
        lower=np.nextafter(denominator.center-denominator.radius,-np.inf)
        if not np.all(lower > 0):
            raise CertificateFailure('Cannot certify a positive RLS denominator')
        center=checked_divide(self.center,denominator.center)
        error=positive_add(self.radius,positive_multiply(np.abs(center),denominator.radius))
        radius=upward(checked_divide(error,lower))
        rounding=positive_multiply(2*UNIT_ROUNDOFF/(1-UNIT_ROUNDOFF),np.abs(center))
        return Enclosure(center,positive_add(radius,rounding))

    def mean(self,axes):
        count=int(np.prod([self.center.shape[axis] for axis in axes]))
        center=self.center.mean(axis=axes)
        radius=upward(self.radius.sum(axis=axes)/(1-gamma(count)))
        magnitude=upward(np.abs(self.center).sum(axis=axes)/(1-gamma(count)))
        radius=positive_add(radius,positive_multiply(2*gamma(count),magnitude))
        radius=upward(checked_divide(radius,count))
        radius=positive_add(radius,positive_multiply(2*UNIT_ROUNDOFF,np.abs(center)))
        return Enclosure(center,radius)

    def contains(self,value):
        value=np.asarray(value)
        if value.shape!=self.center.shape or value.dtype!=np.float64:return False
        lower=np.nextafter(self.center-self.radius,-np.inf)
        upper=np.nextafter(self.center+self.radius,np.inf)
        return bool(np.all((value>=lower)&(value<=upper)))

environment_check()

cdef double checked_center(double value) except -1.7976931348623157e308:
    if not isfinite(value):
        raise CertificateFailure('Nonfinite center')
    if value != 0 and fabs(value) < DBL_MIN:
        raise CertificateFailure('Subnormal center needs a separate underflow model')
    return value

cdef double up_multiply(double x,double y) except -1.0:
    cdef double value=x*y
    if x != 0 and y != 0 and value < DBL_MIN:
        raise CertificateFailure('Radius product underflow needs a separate arithmetic model')
    return normal_up(value)

def information_update(s,rs,h,rh,features,observed,double forgetting):
    """Fuse the identical M027 scalar operation tree; no state is omitted."""
    z=np.asarray(features,dtype=np.float64).reshape(-1,1)
    v=np.asarray(observed,dtype=np.float64).reshape(1,-1)
    if s.shape!=(len(z),len(z)) or h.shape!=(len(z),v.shape[1]) or rs.shape!=s.shape or rh.shape!=h.shape:
        raise CertificateFailure('Information update dimensions differ')
    if not 0 < forgetting <= 1:raise CertificateFailure('Invalid forgetting factor')
    validate(s,rs);validate(h,rh)
    validate(z,np.zeros_like(z));validate(v,np.zeros_like(v))
    outer_s=z@z.T
    outer_h=z@v
    absolute_s=positive_product(np.abs(z),np.abs(z.T))
    absolute_h=positive_product(np.abs(z),np.abs(v))
    result=[]
    cdef double g=gamma(1),k=2*UNIT_ROUNDOFF/(1-UNIT_ROUNDOFF)
    cdef double denom=1-g,base,center,rr,outer_r,product
    cdef const double[::1] old_c,old_r,outer,outer_upper
    cdef double[::1] new_c,new_r
    cdef Py_ssize_t i
    for center_array,radius_array,outer_array,absolute_array in [(s,rs,outer_s,absolute_s),(h,rh,outer_h,absolute_h)]:
        old_c=np.ascontiguousarray(center_array).reshape(-1)
        old_r=np.ascontiguousarray(radius_array).reshape(-1)
        outer=np.ascontiguousarray(outer_array).reshape(-1)
        outer_upper=np.ascontiguousarray(absolute_array).reshape(-1)
        c_array=np.empty_like(center_array);r_array=np.empty_like(radius_array)
        new_c=c_array.reshape(-1);new_r=r_array.reshape(-1)
        for i in range(old_c.shape[0]):
            # Radius of multiplication by an exact, positive forgetting factor.
            base=checked_center(old_c[i]*forgetting)
            if old_c[i]!=0 and base==0:
                raise CertificateFailure('Product underflow needs a separate arithmetic model')
            rr=normal_up(normal_up(up_multiply(old_r[i],forgetting)))
            rr=normal_up(rr+up_multiply(k,fabs(base)))
            product=checked_center(outer[i])
            # Width-one product has no cancellation; its nonnegative magnitude
            # equals abs(center). Preserve the original gamma(1) operation tree.
            outer_r=normal_up(up_multiply(2*g,outer_upper[i]))
            center=checked_center(base+product)
            if center==0 and base!=-product:
                raise CertificateFailure('Addition underflow or non-IEEE arithmetic')
            new_c[i]=center
            new_r[i]=normal_up(normal_up(rr+outer_r)+up_multiply(k,fabs(center)))
        result.extend([c_array,r_array])
    return tuple(result)

def residual_magnitude(left,left_radius,right,offset,offset_radius):
    """Magnitude enclosure of offset-left@right with exact right-hand array."""
    validate(left,left_radius);validate(right,np.zeros_like(right));validate(offset,offset_radius)
    center_product=left@right
    uncertain=positive_product(left_radius,np.abs(right))
    absolute=positive_product(np.abs(left),np.abs(right))
    if center_product.shape!=offset.shape:raise CertificateFailure('Residual dimensions differ')
    cdef const double[::1] cp=np.ascontiguousarray(center_product).reshape(-1)
    cdef const double[::1] ur=np.ascontiguousarray(uncertain).reshape(-1)
    cdef const double[::1] ap=np.ascontiguousarray(absolute).reshape(-1)
    cdef const double[::1] oc=np.ascontiguousarray(offset).reshape(-1)
    cdef const double[::1] ora=np.ascontiguousarray(offset_radius).reshape(-1)
    magnitude=np.empty_like(center_product)
    cdef double[::1] out=magnitude.reshape(-1)
    cdef double g=gamma(left.shape[1]),k=2*UNIT_ROUNDOFF/(1-UNIT_ROUNDOFF)
    cdef double radius,value,product
    cdef Py_ssize_t i
    for i in range(cp.shape[0]):
        product=checked_center(cp[i])
        radius=normal_up(normal_up(ur[i]))
        radius=normal_up(radius+up_multiply(2*g,ap[i]))
        value=checked_center(oc[i]-product)
        if value==0 and oc[i]!=product:
            raise CertificateFailure('Addition underflow or non-IEEE arithmetic')
        radius=normal_up(normal_up(ora[i]+radius)+up_multiply(k,fabs(value)))
        out[i]=normal_up(fabs(value)+radius)
    return magnitude

def state_bounds(s,rs,h,rh,theta,covariance,identity):
    covariance=np.asarray(covariance,dtype=np.float64)
    theta=np.asarray(theta,dtype=np.float64)
    if s.shape!=covariance.shape or theta.shape!=h.shape:
        raise CertificateFailure('State dimensions differ')
    magnitude=residual_magnitude(s,rs,covariance,identity,np.zeros_like(identity))
    cdef double g=gamma(s.shape[1]),k=2*UNIT_ROUNDOFF/(1-UNIT_ROUNDOFF)
    cdef double norm_den=np.nextafter(1-g,-np.inf)
    cdef double eta=float(upward(magnitude.sum(axis=1)/norm_den).max())
    if eta>=1:raise CertificateFailure('Cannot certify an invertible information matrix')
    bnorm=upward(np.abs(covariance))
    cdef double norm_b=float(upward(bnorm.sum(axis=1)/norm_den).max())
    cdef double denominator=1-eta
    cdef double d_radius=normal_up(up_multiply(k,fabs(denominator)))
    cdef double lower=nextafter(denominator-d_radius,-INFINITY)
    if lower<=0:raise CertificateFailure('Cannot certify a positive RLS denominator')
    cdef double center=checked_center(norm_b/denominator)
    cdef double error=normal_up(up_multiply(fabs(center),d_radius))
    cdef double inverse_radius=normal_up(error/lower)
    inverse_radius=normal_up(inverse_radius+up_multiply(k,fabs(center)))
    cdef double inverse_upper=normal_up(fabs(center)+inverse_radius)
    residual=residual_magnitude(s,rs,theta,h,rh).max(axis=0)
    coefficient=positive_multiply(inverse_upper,residual)
    return dict(contraction=eta,inverse_upper=inverse_upper,residual_by_output=residual,
                coefficient_radius=coefficient,covariance_radius=up_multiply(inverse_upper,eta))
