"""Fixture-only clock/trace bootstrap, deliberately avoids package/NumPy imports."""
import importlib.util
import json
import os
from pathlib import Path


def load_clock():
    # Execute the exact installed clock adapter as a standalone stdlib-only module.
    # Resolve package location without importing its eager public __init__.
    import importlib.machinery
    spec = importlib.machinery.PathFinder.find_spec('neuromancer')
    path = Path(next(iter(spec.submodule_search_locations)))/'clocks.py'
    clock_spec = importlib.util.spec_from_file_location('_fixture_qualified_clock', path)
    module = importlib.util.module_from_spec(clock_spec)
    clock_spec.loader.exec_module(module)
    return module


class WorkerTrace:
    def __init__(self, folder, enabled=True):
        self.enabled=enabled; self.folder=Path(folder)
        if enabled:
            self.clock=load_clock();self.clock_id=self.clock.clock_domain()
            assert self.clock_id==os.environ['NEUROMANCER_DEADLINE_CLOCK']
            self.folder.mkdir(parents=True,exist_ok=True)
            self.event('worker_entry')

    def event(self, kind, **fields):
        if not self.enabled:return None
        stamp=self.clock.now_ns()
        row=dict(kind=kind,monotonic_ns=stamp,clock_id=self.clock_id,
            remaining_ns=int(os.environ['NEUROMANCER_DEADLINE_NS'])-stamp,**fields)
        with (self.folder/'events.jsonl').open('a') as f:
            f.write(json.dumps(row)+'\n');f.flush()
        return stamp
