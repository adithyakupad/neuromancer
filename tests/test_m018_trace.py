from types import SimpleNamespace

import pytest

from scripts.m016_run import m018_observed_ticks


class TickSource:
    def __init__(self, count):
        self.count = count
        self.exhausted = False

    def loop(self, frequency, *, stop_after_ticks):
        assert (frequency, stop_after_ticks) == (50, 16)
        for index in range(self.count):
            start = 500 * index
            analysis = SimpleNamespace(start_timestamp=start, stop_timestamp=start + 500)
            yield SimpleNamespace(analysis=analysis, frames=range(500))
        self.exhausted = True


def test_trace_preserves_iterator_exhaustion_and_frames():
    source = TickSource(16)
    events = []
    ticks = list(m018_observed_ticks(source, lambda kind, **fields: events.append((kind, fields))))
    assert source.exhausted
    assert [tick.analysis.stop_timestamp for tick in ticks] == list(range(500, 8001, 500))
    assert events[-1] == ('m018_iterator_exhausted', {'ticks': 16})
    assert sum(kind == 'm018_next_end' for kind, _ in events) == 16


@pytest.mark.parametrize('count', (15, 17))
def test_trace_rejects_wrong_tick_count(count):
    with pytest.raises(RuntimeError, match='sixteen'):
        list(m018_observed_ticks(TickSource(count), lambda *args, **kwargs: None))
