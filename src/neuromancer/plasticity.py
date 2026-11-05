"""Optional M013 evaluator-side plasticity; V1 equations and public API unchanged.

Eligibility is dimensionless. Synaptic weights and learning rate are pA.
No training labels, true gain or hidden state enter the public observation API.
"""
import copy
import numpy as np


def decay(trace, elapsed_ms, tau_ms):
    if tau_ms <= 0 or np.any(np.asarray(elapsed_ms) < 0):
        raise ValueError('Invalid trace interval')
    return np.asarray(trace) * np.exp(-np.asarray(elapsed_ms) / tau_ms)


def reward_update(weights_pA, eligibility, rewards, *, enabled, learning_rate_pA=.1):
    weights = np.asarray(weights_pA, dtype=float)
    traces = np.asarray(eligibility, dtype=float)
    rewards = np.asarray(rewards, dtype=float)
    if traces.ndim != 2 or traces.shape[1:] != weights.shape or rewards.shape != (len(traces),):
        raise ValueError('Expected eligibility[trial,synapse] and reward[trial]')
    if not all(np.all(np.isfinite(x)) for x in (weights, traces, rewards)):
        raise ValueError('Nonfinite learning input')
    if not np.isfinite(learning_rate_pA) or learning_rate_pA < 0:
        raise ValueError('Invalid learning rate')
    if not enabled:
        return weights.copy()
    mean_modulated_trace = np.mean(rewards[:, None] * traces, axis=0)
    proposed_weights = weights + learning_rate_pA * mean_modulated_trace
    return np.clip(proposed_weights, 0., 30.)


class Eligibility:
    """Independent analytical pair-rule reference, time in ms; pre wins ties."""
    def __init__(self):
        self.pre = 0.
        self.post = 0.
        self.trace = 0.
        self.time_ms = 0.

    def event(self, time_ms, pre=False, post=False):
        elapsed = time_ms - self.time_ms
        self.pre = float(decay(self.pre, elapsed, 20.))
        self.post = float(decay(self.post, elapsed, 20.))
        self.trace = float(decay(self.trace, elapsed, 200.))
        self.time_ms = time_ms
        if pre:
            self.trace -= self.post
            self.pre += 1.
        if post:
            self.trace += self.pre
            self.post += 1.
        return self.trace

    def checkpoint(self):
        return copy.deepcopy(vars(self))

    def restore(self, state):
        vars(self).update(copy.deepcopy(state))


TRACE_MODEL = """
dx/dt = -x/(20*ms) : 1 (event-driven)
dy/dt = -y/(20*ms) : 1 (event-driven)
deligibility/dt = -eligibility/(200*ms) : 1 (event-driven)
"""
PRE_RULE = 'eligibility -= y; x += 1'
POST_RULE = 'eligibility += x; y += 1'


class PlasticReservoir:
    """Private instrument: original network plus non-delivering E/E trace synapses.

    The original synapses deliver current. This second object observes matching
    arrivals/spikes, with identical delays, and never delivers extra neural current.
    """
    def __init__(self, config):
        import brian2 as b
        from brian2.codegen.runtime.numpy_rt import NumpyCodeObject
        from ._brian import BrianEngine
        self.engine = BrianEngine(config)
        self.enabled = False
        self._learning_snapshots = {}
        excitatory = self.engine.synapses[0]
        self.indices = np.flatnonzero(np.asarray(excitatory.j) < 800)
        self.traces = b.Synapses(self.engine.group, self.engine.group, TRACE_MODEL,
            on_pre=PRE_RULE, on_post=POST_RULE,
            clock=self.engine.clock, codeobj_class=NumpyCodeObject)
        self.traces.connect(i=np.asarray(excitatory.i)[self.indices],
                            j=np.asarray(excitatory.j)[self.indices])
        self.traces.pre.delay = excitatory.delay[self.indices]
        self.engine.net.add(self.traces)
        self.checkpoint('plastic_initial')

    def eligibility(self):
        import brian2 as b
        elapsed_ms = np.asarray((self.engine.net.t-self.traces.lastupdate[:])/b.ms)
        return decay(np.asarray(self.traces.eligibility[:]), elapsed_ms, 200.)

    def weights(self):
        import brian2 as b
        return np.asarray(self.engine.synapses[0].weight[self.indices]/b.pA).copy()

    def learn(self, eligibility, rewards):
        import brian2 as b
        weights = reward_update(self.weights(), eligibility, rewards, enabled=self.enabled)
        self.engine.synapses[0].weight[self.indices] = weights*b.pA

    def checkpoint(self, name):
        self.engine.save(name)
        self._learning_snapshots[name] = self.enabled

    def restore(self, name):
        self.engine.restore(name)
        self.enabled = self._learning_snapshots[name]

    def close(self):
        self.engine.close()
