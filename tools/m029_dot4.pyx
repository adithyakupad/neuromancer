# Included only in the separate M029 verification kernel.
def ordered_dot4(left, right):
    """Fixed k-order products for the four residual output columns."""
    left = np.ascontiguousarray(left, dtype=np.float64)
    right = np.ascontiguousarray(right, dtype=np.float64)
    if left.ndim != 2 or right.ndim != 2 or right.shape != (left.shape[1], 4):
        raise CertificateFailure('Invalid ordered residual operands')
    cdef const double[:, ::1] a = left
    cdef const double[:, ::1] b = right
    result = np.empty((a.shape[0], 4), dtype=np.float64)
    cdef double[:, ::1] out = result
    cdef Py_ssize_t i, k
    cdef double c0, c1, c2, c3, value
    for i in range(a.shape[0]):
        c0 = c1 = c2 = c3 = 0.0
        for k in range(a.shape[1]):
            value = a[i, k]
            c0 = c0 + value * b[k, 0]
            c1 = c1 + value * b[k, 1]
            c2 = c2 + value * b[k, 2]
            c3 = c3 + value * b[k, 3]
        out[i, 0] = c0
        out[i, 1] = c1
        out[i, 2] = c2
        out[i, 3] = c3
    return result
