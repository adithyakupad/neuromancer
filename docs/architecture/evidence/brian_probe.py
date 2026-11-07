"""Mission 001 bounded feasibility probe; not the V0 experiment.
Run: python docs/architecture/evidence/brian_probe.py
"""
import json
import platform
import time
import importlib.metadata
import brian2 as b
import numpy as np

b.prefs.codegen.target = 'numpy'

def probe(size):
    clock = b.Clock(dt=0.1*b.ms)
    b.seed(104)
    group = b.NeuronGroup(size, '''dv/dt = (-v + drive)/(20*ms) : 1 (unless refractory)
                                  drive : 1''', threshold='v>1', reset='v=0',
                          refractory=2*b.ms, method='exact', clock=clock)
    group.v = np.random.default_rng(105).uniform(0, .9, size)
    group.drive = .8
    exc = b.Synapses(group, group, on_pre='v_post += 0.01', clock=clock)
    exc.connect(condition='i != j', p=.02)
    mon = b.SpikeMonitor(group)
    net = b.Network(group, exc, mon)
    net.store('initial')
    t0 = time.perf_counter()
    net.run(100*b.ms)
    cold = time.perf_counter()-t0
    unstim = int(mon.num_spikes)
    net.restore('initial', restore_random_state=True)
    group.drive[:size//4] = 1.5
    t0 = time.perf_counter()
    net.run(100*b.ms)
    warm = time.perf_counter()-t0
    ids, times = np.array(mon.i), np.array(mon.t/b.ms)
    assert len(ids) > unstim, 'No causal stimulation response'
    net.restore('initial', restore_random_state=True)
    group.drive[:size//4] = 1.5
    net.run(50*b.ms)
    net.run(50*b.ms)
    assert np.array_equal(ids, np.array(mon.i)), 'Chunked spike identities differ'
    assert np.array_equal(times, np.array(mon.t/b.ms)), 'Chunked timestamps differ'
    assert float(net.t/b.ms) == 100
    return dict(n=size, synapses=len(exc), simulated_ms=100, cold_run_s=cold,
                warm_run_s=warm, unstimulated_spikes=unstim,
                stimulated_spikes=len(ids), restore_replay_and_chunk_equivalence=True)

if __name__ == '__main__':
    print(json.dumps(dict(python=platform.python_version(), machine=platform.machine(),
        versions={p:importlib.metadata.version(p) for p in ['brian2','numpy','sympy','cython']},
        target='numpy', results=[probe(n) for n in [200,1000]]), indent=2))
