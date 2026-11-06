"""Compare the original SDK experiment to a repaired host artifact, read-only."""
import json
from pathlib import Path
import sys

import cl

CASES = ('C0', 'C1', 'C2', 'C4', 'C5', 'C6', 'PI', 'FROZEN', 'C1_REPEAT')
FIELDS = ('index', 'start', 'stop', 'available', 'counts', 'valid', 'missing',
          'late', 'spikes', 'request', 'decision', 'receipts', 'pi_integral')


def read(path):
    return json.loads(path.read_text())


def verify(root, archived):
    windows = receipts = 0
    for case in CASES:
        location = root / case
        current = read(location / 'ticks.json')
        reference = read(archived / case / 'ticks.json')
        assert len(current) == len(reference) == 16
        for now, old in zip(current, reference, strict=True):
            assert all(now[field] == old[field] for field in FIELDS), (case, now['index'])
            windows += 1
            receipts += len(now['receipts'])
        path, = location.glob('*.h5')
        with cl.RecordingView(str(path)) as view:
            start, stop = current[0]['start'], current[-1]['stop']
            assert int(view.attributes['start_timestamp']) == start
            assert int(view.attributes['end_timestamp']) == stop
            assert view.attributes['application']['expected_final_frame'] == stop
            assert view.samples.shape == (8000, 64)
    assert (windows, receipts) == (144, 28)
    supervisor = read(root / 'returned.json')
    watcher = read(root.with_name(root.name + '_descendants.json'))
    assert supervisor['status'] == 'COMPLETED' and supervisor['cleanup_verified']
    assert supervisor['finished_ns'] < supervisor['deadline_ns']
    assert not (watcher['timed_out'] or watcher['remaining'] or watcher['forced_cleanup_pids'])
    return dict(windows=windows, receipts=receipts, exact_reference_records=True,
                supervision_s=(supervisor['finished_ns']-supervisor['started_ns'])/1e9,
                peak_tree_rss_bytes=watcher['sampled_peak_tree_rss_bytes'])


if __name__ == '__main__':
    print(json.dumps(verify(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
