"""Read-only observer for the cl-sdk 1.0.0 diagnostic ring ABI."""
import ctypes
import json
import mmap
import os
from pathlib import Path
import re
import struct
import sys
import time

import psutil

HEADER = struct.Struct('<Q5I4B5q')


def decode(data):
    magic, version, _, _, rate, _, paused, shutdown, ready, _, _, written, request, _, stim = (
        HEADER.unpack(data)
    )
    if (magic, version, rate) != (0x434C53444B415049, 6, 25000):
        raise ValueError('Unrecognized SDK ring ABI')
    return dict(written=written, request=request, stim=stim, paused=paused,
                shutdown=shutdown, ready=ready)


def observe(name, pid, output):
    if not re.fullmatch(r'/?[A-Za-z0-9_-]+', name):
        raise ValueError('Unexpected ring name')
    libc = ctypes.CDLL(None, use_errno=True)
    shm_open = libc.shm_open
    shm_open.argtypes = [ctypes.c_char_p, ctypes.c_int]
    shm_open.restype = ctypes.c_int
    fd = shm_open(('/' + name.lstrip('/')).encode(), os.O_RDONLY)
    if fd < 0:
        raise OSError(ctypes.get_errno(), 'Read-only shm_open failed')
    try:
        ring = mmap.mmap(fd, HEADER.size, access=mmap.ACCESS_READ)
    finally:
        os.close(fd)
    producer = psutil.Process(pid)
    identity = producer.create_time()
    with ring, (output / 'ring.jsonl').open('x', buffering=1) as log:
        for index in range(24000):
            begin = time.monotonic_ns()
            first = decode(ring[:])
            second = decode(ring[:])
            try:
                if producer.create_time() != identity:
                    raise psutil.NoSuchProcess(pid)
                status = producer.status()
                cpu = producer.cpu_times()
                cpu_ns = round((cpu.user + cpu.system) * 1e9)
            except psutil.NoSuchProcess:
                status, cpu_ns = 'gone', None
            row = dict(begin_ns=begin, observed_ns=time.monotonic_ns(), stable=first == second,
                       producer_pid=pid, producer_status=status, producer_cpu_ns=cpu_ns,
                       **second)
            log.write(json.dumps(row) + '\n')
            if index == 0:
                (output / 'observer.ready').touch()
            if status in ('gone', psutil.STATUS_ZOMBIE) or (output / 'observer.stop').exists():
                return
            time.sleep(.005)
    raise RuntimeError('Observer reached sample ceiling')


if __name__ == '__main__':
    observe(sys.argv[1], int(sys.argv[2]), Path(sys.argv[3]))
