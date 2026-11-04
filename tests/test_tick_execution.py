"""Scheduling adapter contracts; full neural equality lives in bounded profiles."""
from types import SimpleNamespace
import numpy as np
import pytest
from neuromancer.tick_execution import TickExecution,b
from neuromancer.substrate import Command


def engine():
 return SimpleNamespace(net=SimpleNamespace(add=lambda x:None),time_us=51_000_000,previous=np.zeros(4),command_ids=set(),_validate=lambda c,t,p,ids:np.array(c.current_pA))


def test_start_callback_finishes_observation_before_next_command():
 e=engine();driver=TickExecution(e);order=[]
 driver.operation=SimpleNamespace(clock=SimpleNamespace(t=51_020_000*b.us));driver.block_start=51_000_000;driver.table=SimpleNamespace(values=np.zeros((50,5)));driver.pending='prior'
 def finish(t):order.append(('observation',t));e.time_us=t;driver.pending=None
 driver._finish=finish
 def command(t):order.append(('command',t));return Command('fixture','c',t,(30.,0.,30.,0.))
 driver.controller=SimpleNamespace(command=command);driver._tick()
 assert order==[('observation',51_020_000),('command',51_020_000)]
 np.testing.assert_array_equal(driver.table.values[1],np.array([0,30,0,30,0])*1e-12)
 assert driver.pending[1].delivered_stop_us==51_040_000


def test_driver_rejects_invalid_run_boundaries():
 driver=TickExecution(engine())
 for seconds in (0,-1,.5):
  with pytest.raises(ValueError):driver.run(None,seconds)
 driver.engine.time_us+=1
 with pytest.raises(ValueError):driver.run(None,1)


def test_driver_cannot_restart_incomplete_interval():
 driver=TickExecution(engine());driver.pending='unfinished'
 with pytest.raises(RuntimeError):driver.run(None,1)
