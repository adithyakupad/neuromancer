"""A posteriori singular-value bounds from reconstruction and orthogonality.

Thin U,V factors are converted conceptually to polar orthonormal factors.
Weyl's bound then encloses singular values of the exact binary64 input matrix.
No rounded Gram eigenvalue is treated as a true singular value.
"""
import numpy as np

from tools.m027_residual_bounds import Enclosure, CertificateFailure, norm_upper
from tools.portable_numeric_verification import positive_add, positive_multiply, upward


def sqrt_upper(value):
    if value < 0 or not np.isfinite(value):
        raise CertificateFailure('Invalid square-root bound')
    return float(upward(np.sqrt(value)))


def polar_distance(error):
    if not 0 <= error < 1:
        raise CertificateFailure('Cannot certify singular-vector orthogonality')
    lower = np.nextafter(1-error, -np.inf)
    root_lower = np.nextafter(np.sqrt(lower), -np.inf)
    denominator = np.nextafter(1+root_lower, -np.inf)
    return float(upward(error/denominator))


def singular_values(matrix):
    matrix = np.asarray(matrix, dtype=np.float64)
    u, s, vt = np.linalg.svd(matrix, full_matrices=False)
    ub, vb, sigma = Enclosure(u), Enclosure(vt.T), Enclosure(np.diag(s))
    identity = Enclosure(np.eye(len(s)))
    u_error = norm_upper(identity.subtract(ub.transpose.product(ub)))
    v_error = norm_upper(identity.subtract(vb.transpose.product(vb)))
    u_distance = polar_distance(u_error)
    v_distance = polar_distance(v_error)
    residual = Enclosure(matrix).subtract(ub.product(sigma).product(vb.transpose))
    residual_norm = sqrt_upper(float(positive_multiply(norm_upper(residual), norm_upper(residual.transpose))))
    v_norm = sqrt_upper(float(positive_add(1., v_error)))
    error = positive_add(residual_norm, positive_multiply(positive_multiply(u_distance, s[0]), v_norm))
    error = float(positive_add(error, positive_multiply(s[0], v_distance)))
    lower = np.maximum(0., np.nextafter(s-error, -np.inf))
    upper = np.nextafter(s+error, np.inf)
    return dict(center=s, lower=lower, upper=upper, absolute_error=error,
                reconstruction_upper=residual_norm, left_orthogonality_upper=u_error,
                right_orthogonality_upper=v_error)


def condition_interval(matrix):
    certificate = singular_values(matrix)
    if certificate['lower'][-1] <= 0:
        raise CertificateFailure('Smallest singular value has no positive certified lower bound')
    lower = np.nextafter(certificate['lower'][0]/certificate['upper'][-1], -np.inf)
    upper = np.nextafter(certificate['upper'][0]/certificate['lower'][-1], np.inf)
    return float(lower), float(upper), certificate
