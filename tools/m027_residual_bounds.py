"""Residual certificates for fixed-input RLS, separate from production RLS.

The information equations start once at the exact binary64 initial state.
No archived state is used to reset the accumulated information or its radius.
All bounds use the approved normal finite binary64 arithmetic model.
"""
import numpy as np

from tools.portable_numeric_verification import (
    CertificateFailure, Enclosure, gamma, positive_add, positive_multiply, upward,
)


def row_sum_upper(values):
    """Upper bound for a nonnegative last-axis sum, including its reduction."""
    values = np.asarray(values, dtype=np.float64)
    if np.any(values < 0) or not np.isfinite(values).all():
        raise CertificateFailure('Invalid nonnegative reduction')
    denominator = np.nextafter(1-gamma(values.shape[-1]), -np.inf)
    return upward(values.sum(axis=-1)/denominator)


def norm_upper(ball):
    magnitude = positive_add(np.abs(ball.center), ball.radius)
    return float(np.max(row_sum_upper(magnitude)))


class InformationCertificate:
    """Exact ideal RLS information S,h enclosed by center/radius recurrences.

    S_k=lambda*S_(k-1)+z*z.T, h_k=lambda*h_(k-1)+z*v.T.
    Initial S_0=P_0^-1 and h_0=S_0*theta_0, with a verified inverse.
    Dimensions are inferred for independent small-matrix soundness tests.
    """
    def __init__(self, theta, covariance, forgetting=.999):
        theta = np.asarray(theta, dtype=np.float64)
        covariance = np.asarray(covariance, dtype=np.float64)
        if theta.ndim != 2 or covariance.shape != (len(theta), len(theta)):
            raise CertificateFailure('Invalid information dimensions')
        if not 0 < forgetting <= 1:
            raise CertificateFailure('Invalid forgetting factor')
        self.forgetting = Enclosure(forgetting)
        self.size = len(theta)
        self.updates = 0
        try:
            approximate = np.linalg.inv(covariance)
        except np.linalg.LinAlgError as error:
            raise CertificateFailure('Singular initial covariance') from error
        residual = Enclosure(np.eye(self.size)).subtract(Enclosure(approximate).product(Enclosure(covariance)))
        contraction = norm_upper(residual)
        if contraction >= 1:
            raise CertificateFailure('Cannot verify initial inverse')
        # A*P=I-R: P^-1=(I-R)^-1*A, Neumann bound on the inverse error.
        error = Enclosure(contraction).multiply(Enclosure(norm_upper(Enclosure(approximate))))
        radius = error.divide_positive(Enclosure(1.).subtract(Enclosure(contraction)))
        self.information = Enclosure(approximate, float(upward(np.abs(radius.center)+radius.radius)))
        self.rhs = self.information.product(Enclosure(theta))

    def update(self, features, observed):
        z = Enclosure(np.asarray(features, dtype=np.float64).reshape(self.size, 1))
        v = Enclosure(np.asarray(observed, dtype=np.float64).reshape(1, -1))
        self.information = self.information.multiply(self.forgetting).add(z.product(z.transpose))
        self.rhs = self.rhs.multiply(self.forgetting).add(z.product(v))
        self.updates += 1

    @classmethod
    def from_equations(cls, information, rhs):
        """A fixed independently enclosed regression problem, not a trajectory reset."""
        if information.center.ndim != 2 or information.center.shape[0] != information.center.shape[1]:
            raise CertificateFailure('Invalid fixed information dimensions')
        if rhs.center.ndim != 2 or len(rhs.center) != len(information.center):
            raise CertificateFailure('Invalid fixed right-hand side')
        result = cls.__new__(cls)
        result.size = len(information.center)
        result.information = information
        result.rhs = rhs
        result.updates = 0
        result.forgetting = Enclosure(.999)
        return result

    def state(self, theta, covariance):
        """A posteriori error relative to the continuously accumulated ideal state.

        For R=I-S*B, eta=||R||inf<1 implies
        ||S^-1||inf <= ||B||inf/(1-eta).
        ||theta-S^-1*h||inf <= ||S^-1||inf * ||S*theta-h||inf.
        This is not an independent assertion that the rounded trajectory is exact.
        """
        b = Enclosure(covariance)
        inverse_residual = Enclosure(np.eye(self.size)).subtract(self.information.product(b))
        contraction = norm_upper(inverse_residual)
        if contraction >= 1:
            raise CertificateFailure('Cannot certify an invertible information matrix')
        inverse_bound = Enclosure(norm_upper(b)).divide_positive(Enclosure(1.).subtract(Enclosure(contraction)))
        inverse_upper = float(upward(np.abs(inverse_bound.center)+inverse_bound.radius))
        residual = self.rhs.subtract(self.information.product(Enclosure(theta)))
        residual_upper = positive_add(np.abs(residual.center), residual.radius)
        residual_by_output = residual_upper.max(axis=0)
        coefficient_radius = positive_multiply(inverse_upper, residual_by_output)
        covariance_radius = float(positive_multiply(inverse_upper, contraction))
        return dict(contraction=contraction, inverse_upper=inverse_upper,
                    residual_by_output=residual_by_output,
                    coefficient_radius=coefficient_radius, covariance_radius=covariance_radius)

    def functional_difference(self, query, covariance, left_state, right_state):
        """Bound query*(theta_left-theta_right) while retaining nullspace cancellation.

        S^-1=B*(I-(I-S*B))^-1, so each row has
        ||L*S^-1||1 <= ||L*B||1/(1-eta).
        Query uncertainty is included in L*B before the row-norm bound.
        """
        contraction = left_state['contraction']
        if contraction >= 1:
            raise CertificateFailure('Invalid inverse contraction')
        projected = query.product(Enclosure(covariance))
        row_bound = row_sum_upper(positive_add(np.abs(projected.center), projected.radius))
        dual = Enclosure(row_bound).divide_positive(Enclosure(1.).subtract(Enclosure(contraction)))
        dual_upper = upward(np.abs(dual.center)+dual.radius)
        residual = positive_add(left_state['residual_by_output'], right_state['residual_by_output'])
        return positive_multiply(dual_upper[:, None], residual[None, :])


def planner_queries(record, history, delivered):
    """Horizon-mean FIR design rows (1250,41); four outputs share each row.

    Exact-real query, not a replacement for production planner arithmetic.
    Nonnegative delivered currents allow mean absolute signal bounds as well.
    """
    full = np.c_[np.broadcast_to(history[:, 0], (625, 9)), delivered]
    queries = [Enclosure(np.ones((625, 2)))]
    for lag in range(10):
        averaged = Enclosure(full[:, 9-lag:109-lag].reshape(625, 2, 50)).mean((2,))
        for channel in range(4):
            signal = averaged if channel in (0, 2) else Enclosure(np.zeros((625, 2)))
            index = 4*lag+channel
            feature = signal.subtract(Enclosure(record['mean'][index])).divide_positive(Enclosure(record['scale'][index]))
            queries.append(feature)
    return Enclosure(np.stack([q.center for q in queries], axis=-1).reshape(-1, 41),
                     np.stack([q.radius for q in queries], axis=-1).reshape(-1, 41))


def objective_from_means(means, target, dose, switch):
    error = means.subtract(Enclosure(target))
    tracking = error.multiply(error).mean((1,)).multiply(Enclosure(2.))
    costs = tracking.add(Enclosure(dose, positive_multiply(2*gamma(105), np.abs(dose))))
    return costs.add(Enclosure(switch, positive_multiply(2*gamma(12), np.abs(switch))))


def expression_magnitude(record, theta):
    """Absolute expression envelope for the original FIR planner, in Hz.

    The gamma(512) budget exceeds the original forty-term offset dot product,
    ten lag additions and 200-value horizon/channel mean reduction, including
    coefficient division and addition. The 120 pA maximum is unchanged.
    This check rejects domains where a relative normal-arithmetic bound is
    unsupported; it is not a model or amplitude tolerance.
    """
    b = Enclosure(theta[1:]).divide_positive(Enclosure(np.asarray(record['scale'])[:, None]))
    offset = Enclosure(np.asarray(record['output_mean'])).add(Enclosure(theta[0]))
    offset = offset.subtract(Enclosure(np.asarray(record['mean'])[None, :]).product(b).reshape((4,)))
    kernels = b.reshape((10, 4, 4)).part((slice(None), 0, slice(None)))
    kernels = kernels.add(b.reshape((10, 4, 4)).part((slice(None), 2, slice(None))))
    for values in (b.center, offset.center, kernels.center):
        nonzero = np.abs(values[values != 0])
        if len(nonzero) and (nonzero.min() < 2.**-450 or nonzero.max() > 2.**400):
            raise CertificateFailure('Planner arithmetic outside certified normal domain')
    normalized = positive_add(np.abs(b.center), b.radius)
    magnitude = Enclosure(np.abs(record['output_mean'])).add(Enclosure(np.abs(theta[0])))
    magnitude = magnitude.add(Enclosure(np.abs(np.asarray(record['mean']))[None, :]).product(Enclosure(normalized)).reshape((4,)))
    # All ten lags and both active channels, no assumption about stimulus stationarity.
    active = normalized.reshape(10, 4, 4)[:, (0, 2), :].reshape(-1, 4).T
    magnitude = magnitude.add(Enclosure(120.).multiply(Enclosure(row_sum_upper(active))))
    upper = float(np.max(positive_add(np.abs(magnitude.center), magnitude.radius)))
    if upper > 100:
        raise CertificateFailure('Absolute expression cannot certify existing 100 Hz guard')
    return upper


def check_fixed_objective(native, archived):
    """Rounded immutable cost terms must cancel exactly in the difference proof."""
    for name in ('dose', 'switch', 'exposure'):
        left, right = np.asarray(native[name]), np.asarray(archived[name])
        if left.dtype != right.dtype or left.shape != right.shape or left.tobytes() != right.tobytes():
            raise CertificateFailure('Fixed planner objective component differs: '+name)


def residual_planner_costs(certificate, record, theta, covariance, archived_theta,
                           archived_covariance, history, target, native):
    """Cost difference certificate around the unchanged native 625-candidate plan.

    The ideal information equations supply shared dependence; archived state
    enters only a posteriori residuals, never a new initial condition.
    Both ordinary prediction-rounding paths are enclosed independently.
    """
    left = certificate.state(theta, covariance)
    right = certificate.state(archived_theta, archived_covariance)
    query = planner_queries(record, history, native['bank'])
    output_radius = certificate.functional_difference(query, covariance, left, right)
    mean_radius = row_sum_upper(output_radius)/4
    mean_radius = upward(mean_radius.reshape(625, 2))
    magnitude = positive_add(expression_magnitude(record, theta), expression_magnitude(record, archived_theta))
    mean_radius = positive_add(mean_radius, positive_multiply(gamma(512), magnitude))
    means = native['predictions'].reshape(625, 2, 50, 4).mean(axis=(2, 3))
    error = means-target
    # Very small nonzero differences would require a gradual-underflow square model.
    nonzero = np.abs(error[error != 0])
    if len(nonzero) and nonzero.min() < 2.**-450:
        raise CertificateFailure('Tracking square outside certified normal domain')
    changes = positive_add(positive_multiply(2*np.abs(error), mean_radius), positive_multiply(mean_radius, mean_radius))
    radius = row_sum_upper(changes)
    magnitude_cost = positive_add(np.abs(native['cost']), radius)
    radius = positive_add(radius, positive_multiply(2*gamma(20), magnitude_cost))
    return Enclosure(native['cost'], radius), left, right
