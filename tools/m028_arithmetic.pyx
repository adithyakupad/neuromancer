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
