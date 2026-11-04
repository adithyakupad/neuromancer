"""Render measured performance tables/figures; no experiment acquisition."""
import csv,json,pathlib,xml.etree.ElementTree as ET
import numpy as np
p=pathlib.Path('reports/performance/evidence');comparison=json.load(open(p/'comparison_final.json'));a,b=comparison['stages'];pair=json.load(open(p/'paired_latency.json'));workflow=json.load(open(p/'workflow_comparison.json'));rows=[]
for label,x,y,unit in [('1s block',a['block_s'],b['block_s'],'s'),('1s stepped20ms',a['chunked_s'],b['chunked_s'],'s'),('representative workflow',workflow['stages'][0]['median_workflow_s'],workflow['stages'][1]['median_workflow_s'],'s'),('noise generation',a['noise_s'],b['noise_s'],'s'),('planner bank p95',a['bank_ms']['p95'],b['bank_ms']['p95'],'ms'),('planner final-matrix p95',a['planner_ms']['p95'],b['planner_ms']['p95'],'ms'),('planner interleaved p95',pair['summary_ms']['reference']['p95'],pair['summary_ms']['optimized']['p95'],'ms'),('planner interleaved maximum',pair['summary_ms']['reference']['maximum'],pair['summary_ms']['optimized']['maximum'],'ms'),('neural peak RSS',a['neural_peak_rss_bytes'],b['neural_peak_rss_bytes'],'bytes'),('noise traced peak',a['noise_peak_traced_bytes'],b['noise_peak_traced_bytes'],'bytes')]:rows.append(dict(component=label,baseline=x,candidate=y,unit=unit,speedup_or_size_ratio=x/y,reduction=1-y/x))
with (p/'comparison.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
text='| Component | Baseline | Candidate | Unit | Baseline/candidate |\n|---|---:|---:|---|---:|\n'+''.join(f"| {r['component']} |{r['baseline']:.6g}|{r['candidate']:.6g}|{r['unit']}|{r['speedup_or_size_ratio']:.3f}|\n" for r in rows)
(p/'comparison_table.md').write_text(text)
retention={}
for label in ('reference','final'):
 r=json.load(open(p/f'retention_{label}/result.json'));retention[label]={str(keep):{'median_wall_s':float(np.median([x['wall_s'] for x in r['rows'] if x['retain']==keep])),'retained_payload_bytes':max(x['retained_event_payload_bytes'] for x in r['rows'] if x['retain']==keep)} for keep in (False,True)}
assert json.load(open(p/'retention_reference/result.json'))['rows'][0]['observation_signature']==json.load(open(p/'retention_final/result.json'))['rows'][0]['observation_signature']
(p/'retention_comparison.json').write_text(json.dumps(retention,indent=2)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.rcParams.update({'svg.hashsalt':'neuromancer-v1-1-performance','font.size':10})
fig,axes=plt.subplots(1,3,figsize=(12,4));colors=['#506b8e','#c77835']
for ax,values,title,unit in [(axes[0],[a['chunked_s'],b['chunked_s']],'1s integration,20ms stepping','wall seconds'),(axes[1],[a['neural_peak_rss_bytes']/2**20,b['neural_peak_rss_bytes']/2**20],'Neural process peak RSS','MiB'),(axes[2],[pair['summary_ms']['reference']['p95'],pair['summary_ms']['optimized']['p95']],'Interleaved planner p95','milliseconds')]:
 ax.bar(['V1','1.1rc1'],values,color=colors);ax.set_title(title);ax.set_ylabel(unit);ax.set_ylim(0,max(values)*1.15)
fig.suptitle('Equivalent engineering fixtures;2x /30% targets not met');fig.text(.5,.01,'Separate final run p95 worsened4.71 to6.88ms; interleaved maximum12.17 to27.07ms.',ha='center',fontsize=8);fig.tight_layout(rect=[0,.06,1,.94]);fig.savefig(p/'performance_comparison.png',dpi=150,metadata={'Software':'NEUROMANCER benchmark report'});fig.savefig(p/'performance_comparison.svg',metadata={'Date':None});plt.close(fig)
print(text);print('retention',json.dumps(retention))
