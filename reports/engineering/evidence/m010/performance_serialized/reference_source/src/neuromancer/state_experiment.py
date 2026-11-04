"""M003.2 zero-backbone origin selection and bounded matched-branch acquisition."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
from dataclasses import asdict
import gc
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import time
import numpy as np
from .calibration import ramp
from .calibration_diagnostic import save_json
from .diagnostic import schedule, provenance, peak_rss_bytes
from .identification_experiment import bank, audit
from .reachability import state_hashes
from .state_dependence import thresholds, label, origin_rate
from .substrate import Config

NAMES = ('S', 'C0', 'C1', 'C2', 'C3', 'P', 'R')


def plans(config):
    from ._brian import stream
    desired = np.zeros((7, 100, 4))
    for j, duration in enumerate((5, 20, 10, 30)):
        desired[j+1, :duration, (j+config.network_id+config.replicate_id) % 4] = 90
    pairs = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    pair = pairs[(config.network_id+config.replicate_id) % 6]
    for start in (0, 30): desired[5, start:start+5, list(pair)] = 120
    vectors = bank()[stream(config, 5, block=32).permutation(16)[:4]]
    for j, vector in enumerate(vectors): desired[6, j*25+5:(j+1)*25] = vector
    planned = np.array([ramp(row) for row in desired])
    for row in planned: assert audit(row)['violations'] == 0
    return desired, planned


def arrays(results):
    start = results[0].observation.start_us
    for j, r in enumerate(results):
        o, receipt = r.observation, r.receipt; t = start+j*20000
        assert (o.start_us, o.stop_us, o.available_us) == (t, t+20000, t+20000)
        assert o.valid == (True,)*20 and o.coverage_us == (20000,)*20
        assert (receipt.requested_start_us, receipt.delivered_start_us, receipt.delivered_stop_us) == (t, t, t+20000)
        assert receipt.status == 'delivered' and receipt.requested_current_pA == receipt.delivered_current_pA
    offsets = np.cumsum([0]+[len(r.observation.event_time_us) for r in results])
    return dict(counts=np.array([r.observation.counts for r in results], np.int32),
                rates=np.array([r.observation.filtered_sector_rate_hz for r in results]),
                sector=np.array([r.observation.sector_rate_hz for r in results]),
                delivered=np.array([r.receipt.delivered_current_pA for r in results]),
                requested=np.array([r.receipt.requested_current_pA for r in results]),
                time_us=np.array([[r.observation.start_us, r.observation.stop_us, r.observation.available_us] for r in results]),
                valid=np.array([r.observation.valid for r in results]),
                coverage_us=np.array([r.observation.coverage_us for r in results]),
                event_offset=offsets, event_time_us=np.array([t for r in results for t in r.observation.event_time_us], np.int64),
                event_channel=np.array([c for r in results for c in r.observation.channel_id], np.int16))


def run_trial(n, rep, output):
    from ._brian import BrianEngine
    folder = Path(output)/f'n{n}_r{rep}'; folder.mkdir(exist_ok=False)
    engine = None; began = time.perf_counter_ns()
    try:
        config = Config(network_id=n, replicate_id=rep, trial_id=f'state-n{n}-r{rep}', efficacy=0. if rep == 31 else 1.)
        engine = BrianEngine(config); desired, planned = plans(config)
        np.savez_compressed(folder/'plans.npz', desired=desired, planned=planned)
        backbone = engine.run_commands(schedule(engine, np.zeros((1250, 4))))
        bounds = thresholds(np.array([r.observation.filtered_sector_rate_hz for r in backbone[750:1250]]))
        origins = {}; candidates = []; costs = []
        for candidate in range(50):
            backbone.extend(engine.run_commands(schedule(engine, np.zeros((10, 4)))))
            history = np.array([r.observation.filtered_sector_rate_hz for r in backbone[-50:]])
            chosen = label(history, bounds); a = origin_rate(history)
            candidates.append(dict(time_us=engine.time_us, rate=a, label=chosen))
            if chosen is None or chosen in origins: continue
            sub = folder/chosen; sub.mkdir(); origin_us = engine.time_us
            np.savez_compressed(sub/'origin.npz', history=history, input_history=np.zeros((50, 4)),
                                rate=a, bounds=bounds, time_us=origin_us)
            engine.save('origin'); hashes = state_hashes(engine); initial = np.asarray(engine.monitor.count).copy()
            noise = None; branch_arrays = []; receipts = []
            for i, name in enumerate(NAMES):
                engine.restore('origin')
                assert state_hashes(engine) == hashes and engine.time_us == origin_us and not engine.previous.any()
                start = time.perf_counter_ns(); rows = engine.run_commands(schedule(engine, planned[i])); wall = time.perf_counter_ns()-start
                data = arrays(rows); np.testing.assert_array_equal(data['delivered'], planned[i])
                neurons = np.asarray(engine.monitor.count).copy()-initial
                for c, ids in enumerate(engine.parameters['recording']): assert data['counts'][:, c].sum() == neurons[ids].sum()
                np.savez_compressed(sub/f'{name}.npz', **data, neurons=neurons)
                if noise is None: noise = dict(engine.noise_hashes)
                else: assert engine.noise_hashes == noise
                entry = dict(name=name, origin_us=origin_us, stratum=chosen, **audit(planned[i]), wall_ns=wall,
                             neural_ns=sum(r.neural_wall_ns for r in rows), observation_ns=sum(r.observation_wall_ns for r in rows))
                receipts.append(entry); costs.append(entry)
                if rep == 31:
                    if i == 0: sham = data
                    else:
                        for key in ('counts', 'rates', 'sector', 'event_time_us', 'event_channel'):
                            np.testing.assert_array_equal(data[key], sham[key])
            origins[chosen] = dict(time_us=origin_us, rate=a, checkpoint_hashes=hashes, noise_hashes=noise, receipts=receipts)
            save_json(sub/'origin.json', origins[chosen])
            engine.restore('origin'); assert state_hashes(engine) == hashes
        np.savez_compressed(folder/'backbone.npz', **arrays(backbone))
        report = dict(status='complete' if len(origins) == 2 else 'missing_origins', network_id=n, replicate_id=rep,
                      bounds=bounds, candidates=candidates, origins=origins, engine=engine.provenance(),
                      recording=engine.parameters['recording'].tolist(), stimulation=engine.parameters['stimulation'].tolist(),
                      wall_ns=time.perf_counter_ns()-began, peak_rss_bytes=peak_rss_bytes(), branch_costs=costs)
        save_json(folder/'trial.json', report)
        return dict(network_id=n, replicate_id=rep, status=report['status'], wall_ns=report['wall_ns'])
    except Exception as error:
        failure = dict(status='failed', network_id=n, replicate_id=rep, error=f'{type(error).__name__}: {error}')
        save_json(folder/'failure.json', failure); return failure
    finally:
        if engine is not None: engine.close()
        del engine; gc.collect()


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    jobs = [(n, rep) for n in range(10) for rep in range(26, 31)]+[(n, 31) for n in range(3)]
    protocol = Path('docs/research/007_M003_2_STATE_DEPENDENCE_PROTOCOL.md')
    record = provenance(); record.update(jobs=jobs, protocol_sha256=hashlib.sha256(protocol.read_bytes()).hexdigest(),
                                         wall_limit_s=2700, maximum_simulated_seconds=3339)
    save_json(args.output/'provenance.json', record); began = time.perf_counter_ns(); results = []
    with ProcessPoolExecutor(max_workers=3, mp_context=mp.get_context('spawn')) as pool:
        futures = [pool.submit(run_trial, n, r, str(args.output)) for n, r in jobs]
        try:
            for future in as_completed(futures, timeout=2700):
                result = future.result(); results.append(result); print(f'{len(results)}/53 {result}', flush=True)
                save_json(args.output/'progress.json', results)
        except TimeoutError:
            for process in pool._processes.values(): process.terminate()
            raise SystemExit('Acquisition wall budget exceeded; evidence retained')
    save_json(args.output/'summary.json', dict(status='complete' if all(r['status'] == 'complete' for r in results) else 'partial',
              trials=results, wall_ns=time.perf_counter_ns()-began))
    if any(r['status'] != 'complete' for r in results): raise SystemExit('Incomplete origins/cohort; preserve failure')


if __name__ == '__main__': main()
