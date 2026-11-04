"""Typed, process-isolated Brian2 trial interface. Boundary currents are pA."""
from dataclasses import dataclass
import multiprocessing as mp
import math
import copy
from .observation import Observation


@dataclass(frozen=True, slots=True)
class Config:
    network_id: int = 0
    replicate_id: int = 0
    root_seed: int = 20261018
    trial_id: str = "trial"
    dt_us: int = 100
    efficacy: float = 1.0
    retain_spikes: bool = False

    def __post_init__(self):
        for name in ("network_id", "replicate_id", "root_seed"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if not isinstance(self.trial_id, str) or not self.trial_id:
            raise ValueError("trial_id must be nonempty")
        if type(self.dt_us) is not int or self.dt_us not in (50, 100):
            raise ValueError("dt_us must be 100, or 50 for convergence qualification")
        if type(self.efficacy) not in (int, float) or not math.isfinite(self.efficacy) or self.efficacy < 0:
            raise ValueError("efficacy must be finite and nonnegative")
        if type(self.retain_spikes) is not bool:
            raise ValueError("retain_spikes must be boolean")


@dataclass(frozen=True, slots=True)
class Command:
    trial_id: str
    command_id: str
    start_us: int
    current_pA: tuple[float, float, float, float]
    duration_us: int = 20_000
    channels: tuple[int, ...] = (0, 1, 2, 3)
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class Receipt:
    trial_id: str
    command_id: str
    requested_start_us: int
    delivered_start_us: int
    delivered_stop_us: int
    requested_current_pA: tuple[float, ...] | None
    delivered_current_pA: tuple[float, ...]
    status: str
    reason: str
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class StepResult:
    observation: Observation
    receipt: Receipt
    neural_wall_ns: int
    observation_wall_ns: int
    schema_version: int = 1


def _worker(connection, config):
    from ._brian import BrianEngine
    engine = None
    try:
        engine = BrianEngine(config)
        connection.send((True, engine.public_metadata()))
        while True:
            operation, args = connection.recv()
            try:
                if operation == "advance":
                    result = engine.advance(*args)
                elif operation == "reset":
                    engine.reset()
                    result = None
                elif operation == "close":
                    connection.send((True, None))
                    break
                else:
                    raise ValueError("Unknown operation")
                connection.send((True, result))
            except ValueError as error:
                connection.send((False, ("validation", str(error))))
            except Exception as error:
                connection.send((False, ("fatal", f"{type(error).__name__}: {error}")))
                break
    except Exception as error:
        connection.send((False, ("fatal", f"{type(error).__name__}: {error}")))
    finally:
        if engine is not None:
            engine.close()
        connection.close()


class Trial:
    """One spawned process per trial; no Brian objects/state cross this boundary.

    Invalid commands raise ValueError without advancing. A missing command ramps
    toward zero within the same slew bound. reset() restores the fresh episode.
    """
    __slots__ = ("_connection", "_process", "_time_us", "_metadata", "_closed")

    def __init__(self, config: Config = Config()):
        if not isinstance(config, Config):
            raise ValueError("Expected Config")
        context = mp.get_context("spawn")
        self._connection, child = context.Pipe()
        self._process = context.Process(target=_worker, args=(child, config))
        self._closed = False
        self._time_us = 0
        self._process.start()
        child.close()
        try:
            self._metadata = self._receive()
        except Exception:
            self._process.join(timeout=5)
            if self._process.is_alive():
                self._process.terminate()
                self._process.join()
            self._connection.close()
            self._closed = True
            raise

    def _receive(self):
        if not self._connection.poll(120):
            raise RuntimeError("Trial worker response timed out")
        try:
            ok, payload = self._connection.recv()
        except EOFError as error:
            raise RuntimeError("Trial worker terminated unexpectedly") from error
        if not ok:
            kind, message = payload
            if kind == "validation":
                raise ValueError(message)
            raise RuntimeError(message)
        return payload

    @property
    def time_us(self) -> int:
        return self._time_us

    @property
    def metadata(self) -> dict:
        return copy.deepcopy(self._metadata)

    def advance(self, command: Command | None, stop_us: int) -> StepResult:
        if self._closed:
            raise RuntimeError("Trial is closed")
        self._connection.send(("advance", (command, stop_us)))
        result = self._receive()
        self._time_us = result.observation.stop_us
        return result

    def reset(self) -> None:
        if self._closed:
            raise RuntimeError("Trial is closed")
        self._connection.send(("reset", ()))
        self._receive()
        self._time_us = 0

    def close(self) -> None:
        if self._closed:
            return
        try:
            if self._process.is_alive():
                self._connection.send(("close", ()))
                self._receive()
        except (BrokenPipeError, EOFError, RuntimeError, OSError):
            pass
        finally:
            self._connection.close()
            self._process.join(timeout=5)
            if self._process.is_alive():
                self._process.terminate()
                self._process.join()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
