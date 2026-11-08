"""Durable append-only certificate checkpoints; supervisor persistence is unchanged."""
import hashlib
import json
import os
from pathlib import Path

from neuromancer.supervisor import atomic_json as durable_json

FORMAT='m028-append-checkpoints-v1'
EXTRA_PROGRESS={}


def atomic_json(path,data):
    path=Path(path)
    if path.name!='progress.json' or 'checkpoints' not in data:
        return durable_json(path,data)
    ledger=path.with_name('checkpoints.jsonl')
    count=0;offset=0;chain='00'*32
    if path.exists():
        old=json.loads(path.read_text())
        if old.get('format')!=FORMAT:raise ValueError('Unexpected checkpoint format')
        count=old['checkpoint_count'];offset=old['ledger_bytes'];chain=old['ledger_chain']
    if ledger.exists() and ledger.stat().st_size!=offset:
        raise ValueError('Uncommitted ledger tail preserved; fresh stage directory required')
    rows=data['checkpoints']
    if len(rows)<count:raise ValueError('Checkpoint stream is append-only')
    with ledger.open('ab') as stream:
        for row in rows[count:]:
            encoded=(json.dumps(row,sort_keys=True,allow_nan=False)+'\n').encode()
            stream.write(encoded)
            chain=hashlib.sha256(bytes.fromhex(chain)+encoded).hexdigest()
            offset+=len(encoded)
        stream.flush();os.fsync(stream.fileno())
    summary={key:value for key,value in data.items() if key!='checkpoints'}
    summary['positive_denominators']=dict(EXTRA_PROGRESS)
    summary.update(format=FORMAT,checkpoint_count=len(rows),ledger_bytes=offset,ledger_chain=chain)
    # Original publication fsyncs file contents and atomically replaces the
    # pointer. Ledger contents are fsynced first. No new power-loss guarantee
    # for directory entries is claimed; production persistence is unchanged.
    return durable_json(path,summary)


def load_progress(path):
    path=Path(path)
    summary=json.loads(path.read_text())
    if summary.get('format')!=FORMAT:return summary
    raw=path.with_name('checkpoints.jsonl').read_bytes()
    if len(raw)<summary['ledger_bytes']:raise ValueError('Checkpoint ledger truncated')
    records=[];chain='00'*32
    for encoded in raw[:summary['ledger_bytes']].splitlines(keepends=True):
        chain=hashlib.sha256(bytes.fromhex(chain)+encoded).hexdigest()
        records.append(json.loads(encoded))
    if len(records)!=summary['checkpoint_count'] or chain!=summary['ledger_chain']:
        raise ValueError('Checkpoint ledger integrity failure')
    return {**summary,'checkpoints':records}
