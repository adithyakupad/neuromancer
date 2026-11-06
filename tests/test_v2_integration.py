"""Core installation and isolated SDK boundary integration."""
import subprocess
import sys

from neuromancer.cl_adapter import FIXTURE_MAP
from neuromancer.neural_io import BIN_FRAMES, FrameClock
from neuromancer.substrate import Command


def test_core_public_imports_leave_optional_sdk_unloaded():
    subprocess.run([sys.executable, "-c", """
import sys
from neuromancer import Trial, Command
from neuromancer.cl_adapter import SimulatorSession
from neuromancer.causal_memory import build_condition
assert 'cl' not in sys.modules
assert SimulatorSession().state.value == 'closed'
"""], check=True, timeout=20)


def test_v2_bin_time_aligns_without_aliasing_units():
    clock = FrameClock("session", 100)
    assert clock.relative_us(100 + BIN_FRAMES) == Command("trial", "id", 0, (0.,)*4).duration_us
    assert not set(FIXTURE_MAP.stimulation).intersection(FIXTURE_MAP.recording)
