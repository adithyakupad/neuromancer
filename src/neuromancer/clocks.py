"""Suspend-inclusive same-boot clocks; never silently fall back to uptime."""
import ctypes
from pathlib import Path
import sys
import threading
import time


class ClockError(RuntimeError):
    pass


def check_reading(before: int, after: int, reference: int, active: int,
                  previous: tuple[int, int, int] | None, quantum: int = 1) -> None:
    if min(before, after, reference, active) < 0 or before > after:
        raise ClockError('Invalid or backward continuous clock')
    if not before-quantum <= reference <= after+quantum:
        raise ClockError('Independent continuous-clock APIs disagree')
    if active > after+quantum:
        raise ClockError('Uptime exceeds continuous time')
    if previous is not None:
        old_before, old_after, old_active = previous
        if before < old_before or active < old_active:
            raise ClockError('Clock moved backward')
        if after-old_before+2*quantum < active-old_active:
            raise ClockError('Continuous elapsed time fell behind active elapsed time')


class SuspendClock:
    def __init__(self):
        self._lock = threading.Lock()
        self._previous = None
        self._failure = None
        if sys.platform == 'darwin':
            self.lib = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
            class Timebase(ctypes.Structure):
                _fields_ = [('numer', ctypes.c_uint32), ('denom', ctypes.c_uint32)]
            base = Timebase()
            info = self.lib.mach_timebase_info
            info.argtypes = [ctypes.POINTER(Timebase)]; info.restype = ctypes.c_int
            if info(ctypes.byref(base)) != 0 or not base.numer or not base.denom:
                raise ClockError('Invalid Mach timebase')
            self.numer, self.denom = base.numer, base.denom
            for name in ('mach_continuous_time', 'mach_absolute_time'):
                f = getattr(self.lib, name); f.argtypes = []; f.restype = ctypes.c_uint64
            raw = self.lib.clock_gettime_nsec_np
            raw.argtypes = [ctypes.c_int]; raw.restype = ctypes.c_uint64
            self._continuous = lambda: self.lib.mach_continuous_time()*self.numer//self.denom
            self._active = lambda: self.lib.mach_absolute_time()*self.numer//self.denom
            self._reference = lambda: raw(4)  # SDK CLOCK_MONOTONIC_RAW, not UPTIME_RAW(8).
            boot = ctypes.create_string_buffer(64); size = ctypes.c_size_t(len(boot))
            query = self.lib.sysctlbyname
            query.argtypes = [ctypes.c_char_p,ctypes.c_void_p,ctypes.POINTER(ctypes.c_size_t),ctypes.c_void_p,ctypes.c_size_t]
            query.restype = ctypes.c_int
            if query(b'kern.bootsessionuuid',boot,ctypes.byref(size),None,0) != 0:
                raise ClockError('Cannot establish boot identity; no persisted deadline accepted')
            boot_id = boot.value.decode('ascii')
            name = 'darwin.mach_continuous_time.ns.v1'
            self.quantum = (self.numer+self.denom-1)//self.denom
        elif sys.platform.startswith('linux') and hasattr(time, 'CLOCK_BOOTTIME'):
            self._continuous = lambda: time.clock_gettime_ns(time.CLOCK_BOOTTIME)
            self._active = time.monotonic_ns
            self._reference = self._continuous
            boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            name = 'linux.CLOCK_BOOTTIME.ns.v1'
            self.quantum = 1
        else:
            raise ClockError('No qualified suspend-inclusive clock on this platform')
        if not boot_id:
            raise ClockError('Empty boot identity')
        self.domain = name+'@'+boot_id
        self.sample()

    def sample(self) -> dict:
        with self._lock:
            if self._failure is not None:
                raise ClockError('Clock quarantined after prior inconsistency') from self._failure
            try:
                before = self._continuous(); active = self._active()
                reference = self._reference(); after = self._continuous()
                check_reading(before,after,reference,active,self._previous,self.quantum)
            except Exception as exc:
                self._failure = exc
                raise ClockError('Unreliable suspend-inclusive clock reading') from exc
            # Offset growth is expected during suspension, not a clock fault.
            gap = max(0, before-active-self._previous[1]+self._previous[2]) if self._previous else 0
            self._previous = (before,after,active)
            return dict(continuous_ns=after,active_ns=active,wall_ns=time.time_ns(),
                        sample_width_ns=after-before,suspend_gap_lower_bound_ns=gap,
                        clock_id=self.domain)

    def now_ns(self) -> int:
        return self.sample()['continuous_ns']


_clock = None


def get_clock() -> SuspendClock:
    global _clock
    if _clock is None:
        try:
            _clock = SuspendClock()
        except ClockError:
            raise
        except Exception as exc:
            raise ClockError('Suspend-inclusive clock initialization failed') from exc
    return _clock


def now_ns() -> int:
    return get_clock().now_ns()


def clock_domain() -> str:
    return get_clock().domain
