"""Bounded profiling of the unchanged verifier; never a qualification result."""
import argparse
import cProfile
import importlib.util
import json
from pathlib import Path
import platform
import pstats
import resource
import time


def main(output):
    output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('original_certificate', 'tools/portable_numeric_verification.py')
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    from neuromancer.predictive import FIRModel
    from neuromancer.supervisor import atomic_json

    timings = {}

    def timed(name, function):
        def measure(*args, **kwargs):
            start = time.perf_counter_ns()
            try:
                return function(*args, **kwargs)
            finally:
                row = timings.setdefault(name, {'calls': 0, 'seconds': 0.})
                row['calls'] += 1
                row['seconds'] += (time.perf_counter_ns()-start)/1e9
        return measure

    for name in ['rls_step', 'planner_enclosure', 'certify_choice']:
        setattr(original, name, timed(name, getattr(original, name)))
    FIRModel.update = timed('native_update', FIRModel.update)
    original.np.load = timed('archive_open', original.np.load)

    class FirstBranchJSON:
        # Instrumentation selects the declared profile workload only. No file is edited.
        @staticmethod
        def loads(value):
            result = json.loads(value)
            if isinstance(result, dict) and 'jobs' in result:
                result['jobs'] = result['jobs'][:1]
            if isinstance(result, dict) and 'branches' in result:
                result['branches'] = [b for b in result['branches'] if b['controller']=='RLS-MPC'][:1]
            return result

        dumps = staticmethod(json.dumps)

    profiler = cProfile.Profile()
    start = time.monotonic_ns()
    cpu_start = time.process_time_ns()
    profiler.enable()
    prerequisite_code = original.certify_trajectory(output/'original-256')
    original.json = FirstBranchJSON
    first_branch_code = original.certify_archive(output/'original-first-branch')
    profiler.disable()
    profiler.dump_stats(str(output/'original.prof'))
    with (output/'profile.txt').open('w') as stream:
        pstats.Stats(profiler, stream=stream).sort_stats('cumulative').print_stats(65)
    result = dict(profile_only=True, qualification_pass=False, workload='original 256 + n0_r47 STATIC_RLS-MPC',
                  wall_s=(time.monotonic_ns()-start)/1e9, cpu_s=(time.process_time_ns()-cpu_start)/1e9,
                  peak_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  rss_units='bytes' if platform.system()=='Darwin' else 'KiB',
                  prerequisite_code=prerequisite_code, first_branch_code=first_branch_code, timings=timings)
    atomic_json(output/'profile.json', result)
    print(json.dumps(result))
    return 0 if prerequisite_code==0 and first_branch_code==1 else 1


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    raise SystemExit(main(parser.parse_args().output))
