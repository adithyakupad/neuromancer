"""Summarize retained SDK matrix artifacts without invoking the simulator."""
import argparse
import hashlib
import json
from pathlib import Path
import re

CASES = ('C0', 'C1', 'C2', 'C4', 'C5', 'C6', 'PI', 'FROZEN', 'C1_REPEAT')


def read_json(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def last_event(events, kind):
    return next((event for event in reversed(events) if event['kind'] == kind), None)


def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def summarize(root):
    worker_log = (root / 'supervision/worker-0.log').read_text()
    timeout = re.search(r'TimeoutError: Timeout waiting for timestamp (\d+)', worker_log)
    target = int(timeout[1]) if timeout else None
    completed = {row['case'] for row in read_json(root / 'completed.json', [])}
    cases = {}
    for name in CASES:
        directory = root / name
        if not directory.exists():
            continue
        ledger = read_jsonl(directory / 'source.jsonl')
        unexpected = {event['kind'] for event in ledger} - {'open', 'commit', 'close'}
        if unexpected:
            raise ValueError(f'{name} scientific ledger contains {sorted(unexpected)}')
        source = read_jsonl(directory / 'm018_source_trace.jsonl')
        client = read_jsonl(directory / 'client_trace.jsonl')
        rows = read_json(directory / 'ticks.json', [])
        opened = last_event(source, 'm018_source_open')
        read_begin = last_event(source, 'm018_read_begin')
        read_end = last_event(source, 'm018_read_end')
        if read_end is not None and read_end['stop'] - read_end['start'] != read_end['count']:
            raise ValueError(f'{name} source frame arithmetic is inconsistent')
        processed = last_event(client, 'm018_tick_processed')
        cases[name] = {
            'complete': name in completed,
            'ticks_persisted': len(rows),
            'last_persisted_stop': rows[-1]['stop'] if rows else None,
            'recording_count': len(list(directory.glob('*.h5'))),
            'source_open': opened,
            'last_read_begin': read_begin,
            'last_read_end': read_end,
            'source_close': ledger[-1] if ledger and ledger[-1]['kind'] == 'close' else None,
            'source_close_begin': last_event(source, 'm018_source_close_begin'),
            'source_close_end': last_event(source, 'm018_source_close_end'),
            'source_commits': sum(row['kind'] == 'commit' for row in ledger),
            'client_session_open': last_event(client, 'm018_session_open_end'),
            'client_recording_open': last_event(client, 'm018_recording_open_end'),
            'last_next_begin': last_event(client, 'm018_next_begin'),
            'last_next_end': last_event(client, 'm018_next_end'),
            'last_processed': processed,
            'recording_stop_begin': last_event(client, 'm018_recording_stop_begin'),
            'recording_stop_end': last_event(client, 'm018_recording_stop_end'),
            'client_session_close': last_event(client, 'm018_session_close_end'),
            'source_reg_cleared': last_event(client, 'm018_clear_source_end'),
        }
    supervisor = read_json(root / 'returned.json', {})
    descendants = read_json(root.with_name(root.name + '_descendants.json'), {})
    return {
        'target_frame': target,
        'status': supervisor.get('status'),
        'cleanup_verified': supervisor.get('cleanup_verified'),
        'supervised_elapsed_s': (
            (supervisor['finished_ns'] - supervisor['started_ns']) / 1e9
            if 'finished_ns' in supervisor else None
        ),
        'watchdog_timed_out': descendants.get('timed_out'),
        'forced_cleanup_pids': descendants.get('forced_cleanup_pids'),
        'remaining_descendants': descendants.get('remaining'),
        'sampled_peak_tree_rss_bytes': descendants.get('sampled_peak_tree_rss_bytes'),
        'cases': cases,
        'files_sha256': {
            str(path.relative_to(root.parent)): file_hash(path)
            for path in sorted(root.parent.rglob('*')) if path.is_file()
        },
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('matrix', type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.matrix), indent=2))
