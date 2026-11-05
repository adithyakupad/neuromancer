"""Outer observation and cleanup for SDK children that create new sessions."""
import json
from pathlib import Path
import subprocess
import sys
import time

import psutil


def living(pid, created):
    try:
        process=psutil.Process(pid)
        if process.create_time()==created and process.status()!=psutil.STATUS_ZOMBIE:
            return process
    except psutil.NoSuchProcess:
        pass
    return None


def main():
    output=Path(sys.argv[1])
    budget=float(sys.argv[2])
    command=[sys.executable,'scripts/m014_supervise.py',str(output),str(budget),*sys.argv[3:]]
    start=time.monotonic()
    launcher=subprocess.Popen(command)
    tracked={}
    sampled_peak=0
    timeout=False
    try:
        while launcher.poll() is None:
            for child in psutil.Process(launcher.pid).children(recursive=True):
                try:
                    identity=(child.pid,child.create_time())
                    row=tracked.setdefault(identity,dict(pid=child.pid,created=identity[1],
                        name=child.name(),peak_rss_bytes=0,cpu_seconds=0.))
                    row['peak_rss_bytes']=max(row['peak_rss_bytes'],child.memory_info().rss)
                    cpu=child.cpu_times()
                    row['cpu_seconds']=max(row['cpu_seconds'],cpu.user+cpu.system)
                except psutil.NoSuchProcess:
                    continue
            sampled_peak=max(sampled_peak,sum(process.memory_info().rss
                for process in (living(*identity) for identity in tracked) if process is not None))
            if time.monotonic()-start>budget+6:
                timeout=True
                break
            time.sleep(.025)
    finally:
        remaining=[process for process in (living(*identity) for identity in tracked) if process is not None]
        survivors=[process.pid for process in remaining]
        for process in remaining:
            try:process.kill()
            except psutil.NoSuchProcess:pass
        if launcher.poll() is None:
            launcher.kill()
        launcher.wait(timeout=2)
        psutil.wait_procs(remaining,timeout=2)
        leftovers=[identity[0] for identity in tracked if living(*identity) is not None]
        evidence=dict(timed_out=timeout,forced_cleanup_pids=survivors,remaining=leftovers,
                      exit_code=launcher.returncode,sampled_peak_tree_rss_bytes=sampled_peak,
                      elapsed_s=time.monotonic()-start,processes=list(tracked.values()))
        output.with_name(output.name+'_descendants.json').write_text(json.dumps(evidence,indent=2))
    return 1 if timeout or survivors or leftovers else launcher.returncode


if __name__=='__main__':
    raise SystemExit(main())
