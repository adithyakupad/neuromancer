"""Deterministic scientific figures from frozen evaluator CSVs."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg');matplotlib.rcParams['svg.hashsalt']='neuromancer-m004'
import matplotlib.pyplot as plt


def save(fig,path,name):
    fig.tight_layout();fig.savefig(path/f'{name}.png',dpi=150,metadata={'Software':'NEUROMANCER M004'})
    fig.savefig(path/f'{name}.svg',metadata={'Date':None,'Creator':'NEUROMANCER M004'});plt.close(fig)


def table(path):return list(csv.DictReader(path.open()))


def main():
    p=argparse.ArgumentParser();p.add_argument('--analysis',type=Path,required=True);args=p.parse_args();base=args.analysis
    summary=json.loads((base/'comparison.json').read_text());chosen=summary['selected_model'];rolling=table(base/'rolling.csv');effects=table(base/'effects.csv');alarms=table(base/'detections.csv');coef=table(base/'coefficients.csv')
    fig,axes=plt.subplots(2,2,figsize=(12,7),sharex=True)
    for col,stage in enumerate(('D','V')):
        for row,condition in enumerate(('LOSS','STATIC')):
            ax=axes[row,col]
            for model in ('FROZEN',chosen,'ARX','ORACLE'):
                rr=[r for r in rolling if r['stage']==stage and r['condition']==condition and r['model']==model and (stage=='V' or r['replicate']=='33')]
                means=[np.mean([float(r['mse_hz2']) for r in rr if float(r['origin_s'])==t]) for t in range(39,79)]
                ax.plot(range(39,79),means,label=model)
            ax.axvline(59,color='black',ls='--');ax.set(title=f'{stage} {condition}',xlabel='Prospective origin (s)',ylabel='1 s mean-rate MSE (Hz²)')
    axes[0,0].legend(fontsize=8);save(fig,base,'prospective_prediction')
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for col,stage in enumerate(('D','V')):
        ax=axes[col];rr=[r for r in alarms if r['stage']==stage and r['condition'] in ('STATIC','LOSS') and (stage=='V' or r['replicate']=='33')]
        for row,r in enumerate(rr):
            times=json.loads(r['alarms_s']);ax.scatter(times,[row]*len(times),marker='x' if r['condition']=='STATIC' else 'o',color='tab:blue' if r['condition']=='STATIC' else 'tab:orange')
        ax.axvline(59,color='black',ls='--');ax.axvline(69,color='gray',ls=':');ax.set_ylim(-1,len(rr));ax.set(title=f'{stage}: x stationary, o efficacy loss',xlabel='Completed alarm time (s)',ylabel='Trial (every trial retained)',xlim=(39,80))
    save(fig,base,'detection_raster')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for col,stage in enumerate(('D','V')):
        ax=axes[col]
        for model in ('FROZEN',chosen,'ARX','ORACLE'):
            rr=[r for r in effects if r['stage']==stage and r['condition']=='LOSS' and r['model']==model and (stage=='V' or r['replicate']=='33')]
            ax.plot((54,64,74),[np.mean([float(r['mse_hz2']) for r in rr if int(r['origin_s'])==t]) for t in (54,64,74)],marker='o',label=model)
        ax.set(title=f'{stage}: evaluator-only continuation contrast',xlabel='Same-origin probe time (s)',ylabel='Mean effect MSE (Hz²)');ax.axvline(59,color='black',ls='--')
    axes[0].legend(fontsize=8);save(fig,base,'intervention_contrasts')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for col,stage in enumerate(('D','V')):
        rr=[r for r in coef if r['stage']==stage and r['condition']=='LOSS' and r['model']==chosen and (stage=='V' or r['replicate']=='33') and r['kernel_gain_proxy']!='']
        axes[col].plot(range(39,80),[np.mean([float(r['kernel_gain_proxy']) for r in rr if int(r['time_s'])==t]) for t in range(39,80)],label='Kernel-scale proxy')
        axes[col].plot([39,59,59,79],[1,1,.6,.6],ls='--',label='Evaluator true gain')
        axes[col].set(title=f'{stage}: proxy is not physical gain identification',xlabel='Completed observation time (s)',ylabel='Relative kernel scale');axes[col].legend(fontsize=8)
    save(fig,base,'kernel_proxy')


if __name__=='__main__':main()
