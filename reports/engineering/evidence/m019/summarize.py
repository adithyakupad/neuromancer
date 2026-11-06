"""Summarize a retained M019 suite directory without running the SDK."""
import hashlib
import json
from pathlib import Path
import sys


def read(path):
    return json.loads(path.read_text()) if path.is_file() else None


def json_lines(path):
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def last_event(rows, event):
    return next((row for row in reversed(rows) if row['event'] == event), None)


def analyze_session(directory):
    client = json_lines(directory / 'client.jsonl')
    ring = json_lines(directory / 'ring.jsonl')
    source = json_lines(directory / 'm018_source_trace.jsonl')
    next_begin = last_event(client, 'next_begin')
    next_failure = last_event(client, 'next_failed')
    observation = last_event(client, 'processed')
    held = []
    if next_begin and next_failure:
        target = next_failure['target']
        held = [
            sample for sample in ring if sample['stable']
            and next_begin['host_ns'] <= sample['begin_ns']
            and sample['observed_ns'] <= next_failure['host_ns']
            and sample['request'] == target and sample['written'] < target
        ]
    return dict(
        completed=(directory / 'complete').exists(),
        processed=sum(row['event'] == 'processed' for row in client),
        receipts=sum(row.get('receipts', 0) for row in client),
        last_processed=observation,
        last_next=next_begin,
        next_failure=next_failure,
        source_last_read=next(
            (row for row in reversed(source) if row['kind'] == 'm018_read_begin'), None
        ),
        source_last_batch=next(
            (row for row in reversed(source) if row['kind'] == 'm018_read_end'), None
        ),
        ring_samples=len(ring),
        held_samples=len(held),
        first_held=held[0] if held else None,
        last_held=held[-1] if held else None,
        held_statuses=sorted({row['producer_status'] for row in held}),
    )


def sha256(path):
    with path.open('rb') as data:
        return hashlib.file_digest(data, 'sha256').hexdigest()


def summarize(root):
    outcomes = read(root / 'outcomes.json')
    directories = sorted(path for path in root.iterdir() if path.is_dir())
    return {
        'outcomes': outcomes,
        'conditions': {
            condition.name: {
                'supervisor': read(condition / 'returned.json'),
                'watchdog': read(root / (condition.name + '_descendants.json')),
                'sessions': {
                    trial.name: analyze_session(trial)
                    for trial in sorted(condition.glob('session-*'))
                },
            }
            for condition in directories
        },
        'sha256': {
            str(path.relative_to(root)): sha256(path)
            for path in sorted(root.rglob('*')) if path.is_file()
        },
    }


if __name__ == '__main__':
    print(json.dumps(summarize(Path(sys.argv[1])), indent=2))
