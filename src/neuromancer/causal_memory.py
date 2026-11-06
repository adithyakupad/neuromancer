"""M015 evaluator-only graph construction and access gate."""

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
import brian2 as b
from ._brian import BrianEngine, E_COUNT, N, digest
from .reservoir import set_recurrence


def layers(parameters):
    order = np.where(np.arange(N) < E_COUNT, 1, 2)
    order[parameters["stimulation"].ravel()] = 0
    order[parameters["recording"].ravel()] = 3
    return order


def build_condition(config, condition):
    if condition not in ("C0", "C1", "C2"):
        raise ValueError("Unknown condition")
    engine = BrianEngine(config)
    order = layers(engine.parameters)
    if condition == "C2":
        for synapse in engine.synapses:
            forward = order[synapse.i[:]] < order[synapse.j[:]]
            synapse.weight = synapse.weight[:] * forward
        engine.save("initial")
    set_recurrence(engine, condition != "C1")
    return engine


def effective_edges(engine):
    rows = []
    for synapse in engine.synapses:
        weights = np.asarray(synapse.weight[:] / b.pA)
        active = (weights != 0) & synapse.active
        delays = np.rint(synapse.delay[:] / b.us).astype(int)
        rows.append(
            np.column_stack(
                (synapse.i[:][active], synapse.j[:][active], weights[active], delays[active])
            )
        )
    return np.concatenate(rows)


def audit_graph(engine):
    edges = effective_edges(engine)
    pre, post = edges[:, :2].astype(int).T
    adjacency = csr_matrix((np.ones(len(pre)), (pre, post)), shape=(N, N))
    _, component = connected_components(adjacency, directed=True, connection="strong")
    recorder = engine.parameters["recording"].ravel()
    paths = []
    for channel in engine.parameters["stimulation"]:
        shortest = dijkstra(
            adjacency, directed=True, indices=channel, unweighted=True, min_only=True
        )[recorder]
        paths.append([int(hops) if np.isfinite(hops) else None for hops in shortest])
    return dict(
        edges=len(edges),
        excitatory_edges=int((edges[:, 2] > 0).sum()),
        inhibitory_edges=int((edges[:, 2] < 0).sum()),
        largest_scc=int(np.bincount(component).max()),
        self_edges=int((pre == post).sum()),
        recorder_hops=paths,
        effective_graph_sha256=digest(edges),
    )


def cue_gate(metrics):
    disconnected, recurrent, feedforward = (metrics[name] for name in ("C1", "C0", "C2"))
    return {
        "disconnected_null": disconnected["exact_sham_null"],
        "cue_decoding": min(recurrent["accuracy"], feedforward["accuracy"]) >= 11 / 16,
        "cue_gap": abs(recurrent["accuracy"] - feedforward["accuracy"]) <= 2 / 16,
        "cue_evoked_response": min(recurrent["evoked_rms_hz"] + feedforward["evoked_rms_hz"]) >= 1,
        "rate_ratio": recurrent["rate_hz"] > 0
        and 2 / 3 <= feedforward["rate_hz"] / recurrent["rate_hz"] <= 1.5,
    }
