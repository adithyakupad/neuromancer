"""Descriptive incomplete-cohort figure; no scientific gate or replicate pooling."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import numpy as np

p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
rows=list(csv.DictReader((a.root/'partial_descriptive_traces.csv').open()))
plt.rcParams.update({'font.family':'DejaVu Sans','svg.hashsalt':'m005a3-incomplete','font.size':9})
fig,axes=plt.subplots(3,1,figsize=(10,8),layout='constrained')
for ax,(n,r) in zip(axes,((0,41),(0,42),(1,41))):
    for name,color in [('ZERO','#666666'),('FIXED','#d68420'),('PI10_5','#146ba4'),('MAX','#a56ba8')]:
        chosen=sorted([v for v in rows if int(v['network'])==n and int(v['replicate'])==r and v['condition']=='LOSS' and v['controller']==name],key=lambda v:int(v['second']))
        assert len(chosen)==32
        y=[float(v['rate_hz'])-float(v['target_hz'])+1 for v in chosen]
        ax.plot(np.arange(32)+.5,y,label=name,color=color,lw=1)
    ax.axhline(1,color='black',ls='--',lw=.8);ax.axvline(16,color='black',ls=':',lw=.8)
    ax.set(title=f'Network {n}, noise {r}: single completed trial',xlabel='Control time (s)',ylabel='Rate minus calibration baseline (Hz)')
axes[0].legend(ncol=4,fontsize=8)
fig.suptitle('INTERRUPTED confirmation: 3 of 20 trials; descriptive only, no cohort qualification')
fig.savefig(str(a.output)+'.png',dpi=140)
fig.savefig(str(a.output)+'.svg',metadata={'Date':None})
plt.close(fig)
