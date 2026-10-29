"""Evaluator scheduling optimization; unchanged neural equations/controllers.

A Brian start-of-bin operation finishes the previous public20ms record before
asking for the next command. Network preparation runs once/second; no future
observation or planned future delivery is exposed to the controller.
"""
from dataclasses import replace
import time
import numpy as np
from ._brian import b,innovations,digest,BIN_US
from .observation import Observation,bin_events
from .substrate import Receipt,StepResult

class TickExecution:
    def __init__(self,engine):
        self.engine=engine;self.controller=None;self.pending=None;self.records=[];self.fault=None;self.on_record=None;self.deadline=None
        self.operation=b.NetworkOperation(self._tick,dt=.02*b.second,when='start',order=-100,name='public_tick_driver*')
        self.operation.active=False;engine.net.add(self.operation)

    def _finish(self,stop):
        e=self.engine;c,receipt=self.pending;start=c.start_us
        if stop!=start+BIN_US:raise RuntimeError('Nonsequential driver completion')
        began=time.perf_counter_ns();times=np.rint(np.asarray(e.monitor.t[e._cursor:]/b.us)).astype(np.int64);neurons=np.asarray(e.monitor.i[e._cursor:],dtype=np.int64).copy()
        if e.config.retain_spikes:e._cursor=len(e.monitor.i)
        else:e.monitor.resize(0);e.monitor.variables['N'].set_value(0);e._cursor=0
        ch=e.lookup[neurons];selected=ch>=0
        counts,rates,coverage,times,ch=bin_events(times[selected],ch[selected],start,stop,np.ones(20,bool));sector,filtered=e.rate_filter.update(counts,stop)
        o=Observation(e.config.trial_id,start,stop,stop,tuple(map(int,counts)),tuple(rates),tuple(map(int,coverage)),(True,)*20,tuple(map(int,times)),tuple(map(int,ch)),sector,filtered,e.rate_filter.initialized)
        r=StepResult(o,receipt,0,time.perf_counter_ns()-began)
        presented=None if self.fault is not None and self.fault(start) else o
        self.controller.accept(presented,receipt,stop);e.time_us=stop;self.pending=None;self.records.append(r)
        if self.on_record is not None:self.on_record(r,presented,self.controller)

    def _tick(self):
        if self.deadline is not None:self.deadline.check()
        e=self.engine;t=int(round(float(self.operation.clock.t/b.us)))
        if self.pending is not None:self._finish(t)
        if t!=e.time_us:raise RuntimeError('Driver/neural/controller clock disagreement')
        c=self.controller.command(t);currents=e._validate(c,t,e.previous,e.command_ids)
        e.previous=currents.copy();e.command_ids.add(c.command_id)
        self.table.values[(t-self.block_start)//BIN_US,1:]=currents*1e-12
        receipt=Receipt(c.trial_id,c.command_id,t,t,t+BIN_US,c.current_pA,tuple(map(float,currents)),'delivered','')
        self.pending=(c,receipt)

    def run(self,controller,seconds,*,deadline=None,fault=None,on_record=None):
        if type(seconds) is not int or seconds<=0 or self.engine.time_us%1_000_000:raise ValueError('Whole-second boundary required')
        if self.pending is not None:raise RuntimeError('Unfinished prior driver interval')
        self.controller=controller;self.records=[];self.fault=fault;self.on_record=on_record;self.deadline=deadline;e=self.engine
        self.operation.active=True
        try:
            for _ in range(seconds):
                if deadline is not None:deadline.check()
                self.block_start=e.time_us;block=e.time_us//1_000_000
                if block!=e._noise_block:
                    noise,fine=innovations(e.config,block);e.noise_hashes[str(block)]=dict(fine=fine,effective=digest(noise));e.group.namespace['innovation']=b.TimedArray(noise,dt=e.config.dt_us/1_000_000*b.second);e.group.namespace['noise_origin']=block*1_000_000*b.us;e._noise_block=block
                self.table=b.TimedArray(np.zeros((50,5))*b.amp,dt=.02*b.second);e.group.namespace['stim_table']=self.table;e.group.namespace['stim_origin']=self.block_start*b.us
                e.net.run(1*b.second,namespace={});self._finish(self.block_start+1_000_000)
                if int(round(float(e.net.t/b.us)))!=e.time_us:raise RuntimeError('Clock mismatch after optimized run')
                for field in ('v','I_E','I_I','eta'):
                    if not np.isfinite(np.asarray(getattr(e.group,field))).all():raise RuntimeError('Nonfinite neural state')
            return self.records
        finally:self.operation.active=False;self.controller=None
