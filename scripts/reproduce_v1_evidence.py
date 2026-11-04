"""Reproduce committed V1 tables/figures; never acquires neural trajectories."""
import argparse,hashlib,json,os,sys
from pathlib import Path
from neuromancer.supervisor import Deadline,supervise,atomic_json

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 d=Deadline.from_environment() if 'NEUROMANCER_DEADLINE_NS' in os.environ else Deadline.after(1200)
 os.environ.update(NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id,VECLIB_MAXIMUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR=str(out/'mpl-cache'))
 source=Path('reports/evidence/v1_finish/m005b');aux=source.parent;py=sys.executable
 commands=[[py,'-m','neuromancer.m005b_analysis',str(source/'primary'),str(out/'analysis')],[py,str(aux/'verify_study.py'),str(source/'primary'),str(out/'model_verification.json')],[py,str(aux/'verify_metrics.py'),str(source/'primary'),str(out/'analysis'),str(out/'statistics_verification.json')],[py,str(aux/'research_figures.py'),str(source/'primary'),str(out/'analysis'),str(out/'figures')]]
 atomic_json(out/'commands.json',commands);result=supervise(commands,out/'supervision',d,workers=1)
 if result['status']!='COMPLETED':raise RuntimeError('Incomplete evidence reproduction; retain logs')
 comparisons={}
 for name in ('trial_metrics.csv','timecourses.csv','network_qualification.csv','summary.json'):
  old=(source/'analysis_primary'/name).read_bytes();new=(out/'analysis'/name).read_bytes();comparisons[name]=dict(byte_equal=old==new,sha256=hashlib.sha256(new).hexdigest());assert old==new,name
 for name in ('tracking_and_cumulative.png','tracking_and_cumulative.svg','network_and_cost.png','network_and_cost.svg'):
  old=(source/'figures_primary'/name).read_bytes();new=(out/'figures'/name).read_bytes();comparisons[name]=dict(byte_equal=old==new,sha256=hashlib.sha256(new).hexdigest())
 # Source artifacts are retained even if OS/font rendering prevents byte identity.
 d.check();atomic_json(out/'reproduction.json',dict(status='PASS',new_neural_acquisition=False,comparisons=comparisons,figures_byte_identical=all(x['byte_equal'] for k,x in comparisons.items() if k.endswith(('.png','.svg'))),remaining_s=d.remaining()));d.check()
if __name__=='__main__':main()
