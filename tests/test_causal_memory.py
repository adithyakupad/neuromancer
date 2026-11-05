from dataclasses import fields
import numpy as np

from neuromancer.causal_memory import audit_graph, build_condition, cue_gate, effective_edges
from neuromancer.reservoir import commands_for_trial, reset_trial
from neuromancer.substrate import Config


def test_c2_effective_graph_is_original_edge_subset_with_access():
    config = Config(network_id=15000,root_seed=20261106)
    recurrent = build_condition(config,'C0')
    dag = build_condition(config,'C2')
    try:
        graph = audit_graph(dag)
        assert graph['largest_scc']==1 and graph['self_edges']==0
        assert graph['excitatory_edges']>0 and graph['inhibitory_edges']>0
        assert all(1<=hops<=3 for channel in graph['recorder_hops'] for hops in channel)
        assert set(map(tuple,effective_edges(dag))).issubset(set(map(tuple,effective_edges(recurrent))))
        assert recurrent.public_metadata()['parameter_hashes']==dag.public_metadata()['parameter_hashes']
    finally:
        recurrent.close()
        dag.close()


def test_c2_restores_graph_and_replays_observations():
    engine = build_condition(Config(network_id=15000,root_seed=20261106),'C2')
    commands = commands_for_trial(1,0,20,engine.config.trial_id)[:4]
    try:
        original = effective_edges(engine)
        reset_trial(engine,159010,True)
        first = engine.run_commands(commands)
        hashes = engine.noise_hashes
        reset_trial(engine,159010,True)
        np.testing.assert_array_equal(effective_edges(engine),original)
        second = engine.run_commands(commands)
        assert hashes==engine.noise_hashes
        for left,right in zip(first,second,strict=True):
            for field in fields(left.observation):
                np.testing.assert_array_equal(getattr(left.observation,field.name),
                                              getattr(right.observation,field.name))
    finally:
        engine.close()


def test_access_gate_requires_decodability_even_with_paths_and_evoked_activity():
    strong = dict(accuracy=.75,evoked_rms_hz=[2.,2.],rate_hz=20.)
    metrics = dict(C0=strong,C2=strong.copy(),C1=dict(exact_sham_null=True))
    assert all(cue_gate(metrics).values())
    metrics['C2']['accuracy'] = .5
    result = cue_gate(metrics)
    assert result['cue_evoked_response'] and not result['cue_decoding'] and not result['cue_gap']
