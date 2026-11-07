from dataclasses import replace
from types import SimpleNamespace
import numpy as np
import pytest

from neuromancer.cl_adapter import CountPI, FIXTURE_MAP, SimulatorSession
from neuromancer.neural_io import (ChannelMap, ElectrodeRequest, FrameClock, MAX_TIMESTAMP,
                                  SampleFrames, SessionState, SpikeEvent, bin_frames, validate_stim)


def frames():
    return SampleFrames(FrameClock('fixture',100),100,600,tuple(range(100,600)),
                        tuple(range(64)),np.zeros((500,64),dtype=np.int16),.195)


def test_exact_frame_and_bin_boundaries_and_overflow():
    clock=frames().clock
    assert clock.frame_at(20_000)==600
    assert clock.relative_us(599)==19_960
    assert [clock.bin_at(frame) for frame in (100,599,600)]==[0,0,1]
    assert clock.frame_at(0)==100
    for invalid in [-1,1,True,MAX_TIMESTAMP+1]:
        with pytest.raises(ValueError):clock.frame_at(invalid)
    with pytest.raises(ValueError):clock.relative_us(MAX_TIMESTAMP)
    with pytest.raises(ValueError):clock.relative_us(99)
    with pytest.raises(ValueError):FrameClock('overflow',MAX_TIMESTAMP).frame_at(40)


def test_mapping_rejects_duplicate_unsupported_and_invalid_geometry():
    for change in [dict(recording=(8,)*20),dict(stimulation=(1,5,6,7)),
                   dict(stimulation=(4,5,6,64)),dict(geometry_um=((0.,0.),)*64)]:
        with pytest.raises(ValueError):replace(FIXTURE_MAP,**change)
    with pytest.raises(ValueError):
        SimulatorSession(ChannelMap(64,(0,1,2,3),tuple(range(8,28)),(0,1,2,3)))


def test_simultaneous_events_boundary_and_causal_availability():
    batch=frames()
    result=bin_frames(batch,(SpikeEvent(100,9),SpikeEvent(100,8),SpikeEvent(599,8)),
                      FIXTURE_MAP,600,100)
    assert result.counts[:2]==(2,1)
    for events in [(SpikeEvent(100,8),SpikeEvent(100,8)),(SpikeEvent(600,8),),
                   (SpikeEvent(99,8),),(SpikeEvent(150,8),SpikeEvent(149,9)),
                   (SpikeEvent(150,64),),(SpikeEvent(150,8,(0.,)),)]:
        with pytest.raises(ValueError):bin_frames(batch,events,FIXTURE_MAP,600,100)
    with pytest.raises(ValueError):bin_frames(batch,(),FIXTURE_MAP,599,100)
    with pytest.raises(ValueError):bin_frames(batch,(),FIXTURE_MAP,600,99)


def test_missing_and_delayed_samples_are_not_valid_silence():
    batch=frames()
    sparse=replace(batch,indices=batch.indices[1:],samples=batch.samples[1:])
    missing=bin_frames(sparse,(),FIXTURE_MAP,600,100)
    assert missing.missing_frames==1 and not any(missing.valid)
    delayed=bin_frames(batch,(),FIXTURE_MAP,1100,100)
    assert delayed.late and not any(delayed.valid)
    for invalid in [replace(batch,stop=100),replace(batch,frames_per_second=50_000),
                    replace(batch,samples=batch.samples.astype(float)),
                    replace(batch,indices=(100,)+batch.indices[:-1]),
                    replace(batch,indices=tuple(reversed(batch.indices)))]:
        with pytest.raises(ValueError):bin_frames(invalid,(),FIXTURE_MAP,600,100)


def test_stim_request_gate_and_receipt_gated_pi():
    batch=frames()
    observation=bin_frames(batch,(),FIXTURE_MAP,600,100)
    request=ElectrodeRequest('a',batch.clock,0,600,1100)
    assert validate_stim(request,observation,batch.clock,FIXTURE_MAP,600)==4
    for invalid in [replace(request,logical_channel=99),replace(request,lead_us=None),
                    replace(request,clock=FrameClock('other',100)),
                    replace(request,phases_us_uA=((160,1.),(160,1.)))]:
        with pytest.raises(ValueError):validate_stim(invalid,observation,batch.clock,FIXTURE_MAP,600)
    with pytest.raises(ValueError):validate_stim(request,observation,batch.clock,FIXTURE_MAP,1099)
    controller=CountPI()
    assert controller.propose(observation) and controller.integral==0
    controller.resolve(False)
    assert controller.integral==0
    assert not controller.propose(replace(observation,valid=(False,)*20))
    assert not controller.propose(replace(observation,late=True))
    assert controller.propose(observation) and controller.integral==0
    controller.resolve(True)
    assert controller.integral==2


@pytest.mark.parametrize('flag',[False,None,1])
def test_unknown_or_hardware_identity_rejected_before_open(monkeypatch,flag):
    from neuromancer import cl_adapter
    def forbidden_open():
        pytest.fail('Hardware open attempted')
    sdk=SimpleNamespace(__file__='/private/tmp/cl/__init__.py',
                        is_simulator=lambda:flag,open=forbidden_open)
    dist=SimpleNamespace(version='1.0.0',locate_file=lambda _:'/private/tmp/cl/__init__.py')
    monkeypatch.setattr(cl_adapter,'import_module',lambda _:sdk)
    monkeypatch.setattr(cl_adapter.metadata,'distribution',lambda _:dist)
    session=SimulatorSession()
    with pytest.raises(RuntimeError,match='hardware_unqualified'):
        with session.open():pass
    assert session.state is SessionState.HARDWARE_UNQUALIFIED
