"""Bounded stock-SDK diagnostic without custom source, recording or stimulation."""
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import time


def report(event, **fields):
    print(json.dumps(dict(event=event, host_monotonic_ns=time.monotonic_ns(), **fields)),
          flush=True)


def main():
    os.environ['CL_SDK_ACCELERATED_TIME'] = '1'
    os.environ['CL_SDK_VISUALISATION'] = '0'
    os.environ.pop('CL_SDK_REPLAY_PATH', None)
    import cl

    distribution = metadata.distribution('cl-sdk')
    expected_path = Path(distribution.locate_file('cl/__init__.py')).resolve()
    if (distribution.version != '1.0.0' or Path(cl.__file__).resolve() != expected_path
            or cl.is_simulator() is not True):
        raise RuntimeError('Unqualified SDK simulator')
    report('environment', python=platform.python_version(), machine=platform.machine(),
           platform=platform.platform(), sdk=distribution.version)

    for session in range(9):
        report('session_open_begin', session=session)
        with cl.open() as neurons:
            if neurons.get_frames_per_second() != 25000:
                raise RuntimeError('Unexpected simulator sample rate')
            channels = neurons.get_channel_count()
            origin = neurons.timestamp()
            report('session_open_end', session=session, frame=origin, channels=channels)
            report('next_begin', session=session, expected_stop=origin + 500)
            ticks = 0
            for tick in neurons.loop(50, stop_after_ticks=16):
                start = origin + ticks * 500
                if (tick.frames.shape != (500, channels)
                        or tick.analysis.start_timestamp != start
                        or tick.analysis.stop_timestamp != start + 500):
                    raise RuntimeError('Unexpected stock SDK frame interval')
                ticks += 1
                report('next_end', session=session, start=start, stop=start + 500)
                report('next_begin', session=session, expected_stop=start + 1000
                       if ticks < 16 else None)
            if ticks != 16:
                raise RuntimeError('Stock SDK ended early')
        report('session_close_end', session=session)


if __name__ == '__main__':
    main()
