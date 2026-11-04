"""Half-open spike bins and the V0 causal population-rate filter."""
from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True, slots=True)
class Observation:
    trial_id: str
    start_us: int
    stop_us: int
    available_us: int
    counts: tuple[int, ...]
    rates_hz: tuple[float, ...]
    coverage_us: tuple[int, ...]
    valid: tuple[bool, ...]
    event_time_us: tuple[int, ...]
    channel_id: tuple[int, ...]
    sector_rate_hz: tuple[float, ...]
    filtered_sector_rate_hz: tuple[float, ...]
    filter_initialized: bool
    schema_version: int = 1


def bin_events(times_us, channels, start_us: int, stop_us: int, valid):
    """Do not move right-edge spikes backwards or replace missing data by zero."""
    times = np.asarray(times_us, dtype=np.int64)
    channel = np.asarray(channels, dtype=np.int64)
    mask = np.asarray(valid)
    if times.shape != channel.shape or times.ndim != 1:
        raise ValueError("Event vectors must have equal one-dimensional shape")
    if mask.shape != (20,) or mask.dtype != np.bool_:
        raise ValueError("valid must contain 20 booleans")
    if stop_us - start_us != 20_000:
        raise ValueError("Observation bin must be 20000 us")
    if np.any(channel < 0) or np.any(channel >= 20):
        raise ValueError("Unknown recording channel")
    select = (times >= start_us) & (times < stop_us) & mask[channel]
    times, channel = times[select], channel[select]
    order = np.lexsort((channel, times))
    counts = np.bincount(channel, minlength=20).astype(np.int64)
    counts[~mask] = -1
    rates = np.where(mask, counts / (5 * .02), np.nan)
    coverage = np.where(mask, 20_000, 0)
    return counts, rates, coverage, times[order], channel[order]


class RateFilter:
    """Initialize once from the completed baseline's last eight seconds."""
    def __init__(self):
        self.value = np.full(4, np.nan)
        self.baseline_counts = np.zeros(4, dtype=np.int64)
        self.baseline_bins = 0
        self.initialized = False

    def update(self, counts, stop_us: int):
        grouped = np.asarray(counts).reshape(4, 5)[:, :4]
        complete = np.all(grouped >= 0, axis=1)
        sector = np.where(complete, grouped.sum(axis=1) / (20 * .02), np.nan)
        # Burn-in ends at 5 s, baseline at 15 s; average baseline [7,15) s.
        if 7_000_000 < stop_us <= 15_000_000 and np.all(complete):
            self.baseline_counts += grouped.sum(axis=1)
            self.baseline_bins += 1
        if stop_us == 15_000_000 and self.baseline_bins == 400:
            self.value = self.baseline_counts / (20 * 8.0)
            self.initialized = True
        elif self.initialized:
            alpha = math.exp(-.02 / .1)
            self.value[complete] = (alpha * self.value[complete]
                                    + (1 - alpha) * sector[complete])
        filtered = np.where(complete, self.value, np.nan)
        return tuple(sector), tuple(filtered)
