"""Reduced Brian2 comparison against an independent scalar LIF simulator."""
import json
from math import ceil, exp, log, sqrt
from pathlib import Path
import sys
import time
import numpy as np

DT_MS = .1
STEPS = 2000
EDGES = ((0,1,120.,10),(0,2,70.,15),(1,2,-90.,20))


def scalar_simulator(drive, edges=EDGES):
    """Explicit event queue and scalar dynamics, with no Brian imports or calls."""
    voltage = [-65.] * 3
    excitation = [0.] * 3
    inhibition = [0.] * 3
    last_spike = [-20] * 3
    pending = [[] for _ in range(len(drive)+21)]
    spikes = []
    trace = []
    for tick, currents in enumerate(drive):
        fired = []
        for cell in range(3):
            if tick-last_spike[cell] >= 20:
                equilibrium = -65 + .1*(excitation[cell]+inhibition[cell]+currents[cell])
                voltage[cell] = equilibrium+(voltage[cell]-equilibrium)*exp(-DT_MS/20)
                if voltage[cell]>=-50:
                    fired.append(cell)
            excitation[cell] *= exp(-DT_MS/5)
            inhibition[cell] *= exp(-DT_MS/10)
        for cell in fired:
            spikes.append((tick,cell))
            for source,target,weight,delay in edges:
                if source==cell:
                    pending[tick+delay].append((target,weight))
        for target,weight in pending[tick]:
            if weight>0:
                excitation[target]+=weight
            else:
                inhibition[target]+=weight
        for cell in fired:
            last_spike[cell]=tick
            voltage[cell]=-65.
        trace.append((excitation.copy(),inhibition.copy()))
    return np.asarray(spikes,dtype=int).reshape(-1,2),np.asarray(trace)


def brian_simulator(drive):
    import brian2 as b
    from brian2.codegen.runtime.numpy_rt import NumpyCodeObject
    clock=b.Clock(dt=DT_MS*b.ms)
    external=b.TimedArray(drive*b.pA,dt=clock.dt)
    model='''
    dv/dt = (-65*mV-v)/(20*ms)+(exc+inh+external(t,i))/(200*pF) : volt (unless refractory)
    dexc/dt = -exc/(5*ms) : amp
    dinh/dt = -inh/(10*ms) : amp
    '''
    cells=b.NeuronGroup(3,model,threshold='v>=-50*mV',reset='v=-65*mV',
                       refractory=2*b.ms,method='exponential_euler',clock=clock,
                       codeobj_class=NumpyCodeObject,namespace={'external':external})
    cells.v=-65*b.mV
    synapses=[]
    for positive,field in [(True,'exc'),(False,'inh')]:
        rows=[edge for edge in EDGES if (edge[2]>0)==positive]
        source,target,weight,delay=map(list,zip(*rows))
        syn=b.Synapses(cells,cells,'weight : amp',on_pre=f'{field}_post += weight',
                       clock=clock,codeobj_class=NumpyCodeObject)
        syn.connect(i=source,j=target)
        syn.weight=np.asarray(weight)*b.pA
        syn.delay=np.asarray(delay)*clock.dt
        synapses.append(syn)
    spikes=b.SpikeMonitor(cells,codeobj_class=NumpyCodeObject)
    currents=b.StateMonitor(cells,['exc','inh'],record=True,when='end',clock=clock,
                            codeobj_class=NumpyCodeObject)
    b.Network(cells,*synapses,spikes,currents).run(len(drive)*clock.dt,namespace={})
    events=np.column_stack((np.rint(spikes.t[:]/clock.dt).astype(int),spikes.i[:]))
    traces=np.stack((np.asarray(currents.exc/b.pA).T,np.asarray(currents.inh/b.pA).T),axis=1)
    return events,traces


def observe(events,traces):
    counts=np.zeros((STEPS//200,3),dtype=int)
    np.add.at(counts,(events[:,0]//200,events[:,1]),1)
    isi=[np.diff(events[events[:,1]==cell,0]) for cell in range(3)]
    decay=[]
    for column in range(2):
        previous=traces[:-1,column]
        following=traces[1:,column]
        active=(np.abs(previous)>1e-5)&(np.abs(following)>1e-5)&(np.abs(following)<np.abs(previous))
        decay.append(float(np.median(-DT_MS/np.log(following[active]/previous[active]))))
    return counts,isi,decay


def main(output):
    from neuromancer.supervisor import Deadline,atomic_json
    deadline=Deadline.from_environment()
    start=time.perf_counter()
    analytic,_=scalar_simulator(np.full((STEPS,3),170.),edges=())
    expected=ceil(-20*log(2/17)/DT_MS)-1
    assert analytic[0,0]==expected
    events,current=scalar_simulator(np.full((STEPS,3),170.))
    first_arrival=int(events[events[:,1]==0,0][0])+10
    assert current[first_arrival-1,0,1]==0 and current[first_arrival,0,1]==120
    results=[]
    for seed in [None,15500,15501,15502]:
        deadline.check()
        name='deterministic' if seed is None else f'ou_{seed}'
        background=np.full((STEPS,3),170.)
        if seed is not None:
            rng=np.random.default_rng(seed)
            rho=exp(-DT_MS/5)
            innovation=rng.normal(size=(STEPS-1,3))
            noise=np.zeros(3)
            for tick,row in enumerate(innovation,start=1):
                noise=rho*noise+25*sqrt(1-rho*rho)*row
                background[tick]+=noise
        contrasts=[]
        for stimulus in [False,True]:
            drive=background.copy()
            if stimulus:
                drive[400:1000,0]+=100
            reference,reference_current=scalar_simulator(drive)
            comparison,comparison_current=brian_simulator(drive)
            rc,ri,rd=observe(reference,reference_current)
            bc,bi,bd=observe(comparison,comparison_current)
            count_equal=bool(np.array_equal(rc,bc))
            rate_error=float(np.abs(rc.sum(axis=0)-bc.sum(axis=0)).max()/.2)
            isi_equal=all(len(left)==len(right) for left,right in zip(ri,bi,strict=True))
            isi_error=None
            if isi_equal:
                isi_error=max((int(np.abs(np.sort(left)-np.sort(right)).max())
                    for left,right in zip(ri,bi,strict=True) if len(left)),default=0)
            trace_error=float(np.abs(reference_current-comparison_current).max())
            row=dict(case=name,stimulus=stimulus,counts_equal=count_equal,rate_error_hz=rate_error,
                     reference_rate_hz=(rc.sum(axis=0)/.2).tolist(),brian_rate_hz=(bc.sum(axis=0)/.2).tolist(),
                     isi_max_ticks=isi_error,trace_error_pA=trace_error,
                     reference_decay_ms=rd,brian_decay_ms=bd,
                     reference_covariance=np.cov(rc.T).tolist(),brian_covariance=np.cov(bc.T).tolist(),
                     passed=count_equal and rate_error<=.1 and isi_equal and isi_error<=1 and trace_error<=1e-8)
            results.append(row)
            contrasts.append((rc,bc))
            np.savez_compressed(output/f'{name}_{int(stimulus)}.npz',drive=drive,
                reference_spikes=reference,brian_spikes=comparison,reference_counts=rc,brian_counts=bc,
                reference_current=reference_current,brian_current=comparison_current)
        evoked_reference=contrasts[1][0]-contrasts[0][0]
        evoked_brian=contrasts[1][1]-contrasts[0][1]
        results[-1]['evoked_equal']=bool(np.array_equal(evoked_reference,evoked_brian))
        results[-1]['evoked_population_counts']=evoked_reference.sum(axis=1).tolist()
        atomic_json(output/'partial.json',results)
    passed=all(row['passed'] and row.get('evoked_equal',True) for row in results)
    atomic_json(output/'summary.json',dict(status='QUALIFIED' if passed else 'NOT QUALIFIED',
        first_spike_tick=expected,first_arrival_tick=first_arrival,elapsed_s=time.perf_counter()-start,
        engine_simulated_s=8*.2,rows=results))


if __name__=='__main__':
    main(Path(sys.argv[1]))
