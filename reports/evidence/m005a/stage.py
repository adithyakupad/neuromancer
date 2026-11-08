"""Bounded post-acquisition orchestration; confirmation never starts here."""
import argparse,json,subprocess,sys,time
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('analysis',type=Path);p.add_argument('tag')
    p.add_argument('--selection',type=Path);a=p.parse_args();e=Path('reports/evidence/m005a')
    started=time.time();manifest=json.loads((a.raw/'provenance.json').read_text());deadline=(a.raw/'provenance.json').stat().st_mtime+manifest['wall_limit_s']+60
    while not (a.raw/'summary.json').exists():
        if time.time()>deadline:raise SystemExit('Acquisition did not complete within cap; no downstream analysis')
        time.sleep(5)
    summary=json.loads((a.raw/'summary.json').read_text());assert summary['status']=='complete'
    for f in a.raw.glob('n*_r*/trial.json'):
        m=json.loads(f.read_text());assert m['peak_rss_bytes']<2*1024**3
    size=sum(f.stat().st_blocks*512 for f in Path('runs').glob('m005a-*/**/*') if f.is_file())
    assert size<500*1024**2
    commands=[['analyze.py',str(a.raw),str(a.analysis)]+(['--selection',str(a.selection)] if a.selection else []),
              ['verify.py',str(a.raw),str(a.analysis),str(e/f'{a.tag}_verification.json')],
              ['secondary.py',str(a.raw),str(a.analysis)]]
    if a.selection:commands.append(['figures.py',str(a.analysis),str(a.raw)])
    records=[]
    for row in commands:
        command=[sys.executable,str(e/row[0]),*row[1:]];began=time.perf_counter()
        with (e/f'{a.tag}_{Path(row[0]).stem}.log').open('w') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
        records.append(dict(command=command,returncode=result.returncode,wall_s=time.perf_counter()-began))
        (e/f'{a.tag}_stages.json').write_text(json.dumps(dict(commands=records,allocated_runs_bytes_before_analysis=size,elapsed_s=time.time()-started),indent=2)+'\n')
        if result.returncode:raise SystemExit(f'Stage failed; preserved {row[0]}')
    print(json.dumps(json.loads((a.analysis/'summary.json').read_text()),indent=2))


if __name__=='__main__':main()
