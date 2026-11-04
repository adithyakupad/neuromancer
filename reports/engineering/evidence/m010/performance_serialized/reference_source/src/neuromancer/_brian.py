"""Private Brian implementation and evaluator access. Never pass this to controllers."""
from dataclasses import asdict
import copy
import hashlib
import math
import time
import brian2 as b
from brian2.codegen.runtime.numpy_rt import NumpyCodeObject
import numpy as np
from .observation import Observation, RateFilter, bin_events
from .substrate import Command, Config, Receipt, StepResult

N = 1000
E_COUNT = 800
BIN_US = 20_000
EQUATIONS = '''
dv/dt = (rest-v)/tau_m + (I_E+I_I+background+eta+gain*I_stim)/capacitance : volt (unless refractory)
dI_E/dt = -I_E/(5*ms) : amp
dI_I/dt = -I_I/(10*ms) : amp
eta : amp
I_stim : amp
tau_m : second (constant)
stim_slot : integer (constant)
gain : 1 (shared)
'''


def stream(config: Config, role: int, *, block: int | None = None):
    replicate = 0 if role in (0, 1, 2, 3) else config.replicate_id
    key = (config.network_id, role, replicate)
    if block is not None:
        key += (block,)
    return np.random.default_rng(np.random.SeedSequence(config.root_seed, spawn_key=key))


def digest(array) -> str:
    value = np.ascontiguousarray(array)
    return hashlib.sha256(str(value.dtype).encode() + str(value.shape).encode()
                          + value.tobytes()).hexdigest()


def realization(config: Config):
    membrane = stream(config, 0)
    tau_ms = membrane.uniform(18, 22, N)
    initial_mV = membrane.uniform(-65, -50, N)
    connectivity = stream(config, 1).random((N, N)) < .05
    np.fill_diagonal(connectivity, False)
    pre, post = np.nonzero(connectivity)
    parameters = stream(config, 2)
    exc = pre < E_COUNT
    weights = np.empty(len(pre))
    weights[exc] = parameters.uniform(12, 18, int(exc.sum()))
    weights[~exc] = parameters.uniform(-72, -48, int((~exc).sum()))
    delay_us = parameters.integers(10, 21, len(pre)) * 100
    channel_rng = stream(config, 3)
    stimulation = []
    recording = []
    for sector in range(4):
        exc_ids = np.arange(sector * 200, (sector + 1) * 200)
        stim = channel_rng.choice(exc_ids, 50, replace=False)
        available = np.setdiff1d(exc_ids, stim)
        recorded_e = channel_rng.choice(available, 20, replace=False).reshape(4, 5)
        recorded_i = channel_rng.choice(np.arange(800 + sector * 50, 850 + sector * 50),
                                         5, replace=False)
        stimulation.append(stim)
        recording.extend(recorded_e)
        recording.append(recorded_i)
    return dict(tau_ms=tau_ms, initial_mV=initial_mV, pre=pre, post=post,
                weight_pA=weights, delay_us=delay_us,
                stimulation=np.asarray(stimulation), recording=np.asarray(recording))


def innovations(config: Config, block: int):
    """Fixed 1 s blocks, fine OU innovations shared by 50 and 100 us integration."""
    fine = stream(config, 4, block=block).standard_normal((20_000, N))
    fine_hash = digest(fine)
    if config.dt_us == 50:
        return fine, fine_hash
    a = math.exp(-.05 / 5)
    coarse = (a * fine[::2] + fine[1::2]) / math.sqrt(1 + a*a)
    return coarse, fine_hash


class BrianEngine:
    def __init__(self, config: Config):
        started = time.perf_counter_ns()
        self.config = config
        self.parameters = realization(config)
        self.time_us = 0
        self.previous = np.zeros(4)
        self.command_ids = set()
        self.rate_filter = RateFilter()
        self._noise_block = -1
        self.noise_hashes = {}
        self._cursor = 0
        self._closed = False
        self._snapshots = {}
        self.clock = b.Clock(dt=(config.dt_us / 1_000_000) * b.second)
        # All random draws are explicit; role 7 is reserved for Brian RNG.
        self.group = b.NeuronGroup(N, EQUATIONS, threshold='v >= threshold_v',
            reset='v = rest', refractory=2*b.ms, method='exponential_euler',
            clock=self.clock, codeobj_class=NumpyCodeObject,
            namespace={'rest': -65*b.mV, 'threshold_v': -50*b.mV,
                       'capacitance': 200*b.pF, 'background': 180*b.pA,
                       'noise_a': math.exp(-config.dt_us / 5000),
                       'noise_sigma': 40*b.pA * math.sqrt(1-math.exp(-2*config.dt_us/5000)),
                       'noise_origin': 0*b.us,
                       'innovation': b.TimedArray(np.zeros((1, N)), dt=(config.dt_us / 1_000_000)*b.second),
                       'stim_origin': 0*b.us,
                       'stim_table': b.TimedArray(np.zeros((1, 5))*b.pA, dt=.02*b.second)})
        self.group.v = self.parameters['initial_mV'] * b.mV
        self.group.tau_m = self.parameters['tau_ms'] * b.ms
        slots = np.zeros(N, dtype=int)
        for channel, members in enumerate(self.parameters['stimulation']):
            slots[members] = channel + 1
        self.group.stim_slot = slots
        self.group.gain = config.efficacy
        self.stim_runner = self.group.run_regularly(
            'I_stim = stim_table(t-stim_origin, stim_slot)', dt=.02*b.second,
            when='start', order=-2, codeobj_class=NumpyCodeObject)
        self.ou_runner = self.group.run_regularly(
            'eta = noise_a*eta + noise_sigma*innovation(t-noise_origin, i)',
            when='start', order=-1, codeobj_class=NumpyCodeObject)
        self.synapses = []
        for excitatory, variable in [(True, 'I_E'), (False, 'I_I')]:
            select = (self.parameters['pre'] < E_COUNT) == excitatory
            syn = b.Synapses(self.group, self.group, 'weight : amp',
                on_pre=f'{variable}_post += weight', clock=self.clock,
                codeobj_class=NumpyCodeObject)
            syn.connect(i=self.parameters['pre'][select], j=self.parameters['post'][select])
            syn.weight = self.parameters['weight_pA'][select] * b.pA
            syn.delay = self.parameters['delay_us'][select] * b.us
            self.synapses.append(syn)
        self.monitor = b.SpikeMonitor(self.group, codeobj_class=NumpyCodeObject)
        self.net = b.Network(self.group, *self.synapses, self.monitor)
        self.lookup = np.full(N, -1, dtype=int)
        self.lookup[self.parameters['recording'].ravel()] = np.repeat(np.arange(20), 5)
        self.initialization_ns = time.perf_counter_ns() - started
        self.save('initial')

    def public_metadata(self):
        return dict(schema_version=1, experiment_kind='simulation',
            trial_id=self.config.trial_id, network_id=self.config.network_id,
            replicate_id=self.config.replicate_id, engine='brian2', engine_version=b.__version__,
            dt_us=self.config.dt_us, control_us=BIN_US, recording_channels=20,
            neurons_per_recording_channel=5, current_unit='pA', time_unit='us',
            parameter_hashes={key: digest(value) for key, value in self.parameters.items()})

    def provenance(self):
        return dict(config=asdict(self.config), metadata=self.public_metadata(),
            numpy_version=np.__version__, generator='PCG64 / SeedSequence',
            role_key='(network_id,role_id,replicate_id[,block_index])',
            parameter_replicate=0, ou_fine_dt_us=50, noise_block_us=1_000_000,
            noise_hashes=dict(self.noise_hashes),
            brian_rng='role 7 reserved; no Brian random expressions or stochastic solver',
            schedule=str(self.net.scheduling_summary()),
            initialization_ns=self.initialization_ns)

    def _validate(self, command, start_us, previous, ids):
        if command is None:
            return np.maximum(previous - 30, 0)
        if not isinstance(command, Command):
            raise ValueError('Expected a Command or None')
        if type(command.schema_version) is not int or command.schema_version != 1 or command.trial_id != self.config.trial_id:
            raise ValueError('Wrong schema or trial identity')
        if not isinstance(command.command_id, str) or not command.command_id or command.command_id in ids:
            raise ValueError('Empty or duplicate command identity')
        if type(command.start_us) is not int or command.start_us != start_us:
            raise ValueError('Command must start at the current integer-us boundary')
        if type(command.duration_us) is not int or command.duration_us != BIN_US:
            raise ValueError('Command duration must be 20000 us')
        if command.channels != (0, 1, 2, 3):
            raise ValueError('All four ordered channels must be explicit')
        if not isinstance(command.current_pA, tuple) or len(command.current_pA) != 4:
            raise ValueError('Expected four numerical currents in pA')
        if any(type(v) not in (int, float) for v in command.current_pA):
            raise ValueError('Currents must be plain finite numbers in pA')
        currents = np.asarray(command.current_pA, dtype=float)
        if not np.all(np.isfinite(currents)) or np.any(currents < 0) or np.any(currents > 120):
            raise ValueError('Current outside finite [0,120] pA bounds')
        if currents.sum() > 240 or np.any(np.abs(currents-previous) > 30):
            raise ValueError('Total-current or per-tick slew bound exceeded')
        return currents

    def advance(self, command: Command | None, stop_us: int) -> StepResult:
        if type(stop_us) is not int or stop_us != self.time_us + BIN_US:
            raise ValueError('stop_us must be the next 20000 us boundary')
        return self.run_commands([command])[0]

    def run_commands(self, commands, *, chunked=False, valid=None):
        """Evaluator-only predeclared open-loop batch; same scheduler as advance()."""
        if self._closed:
            raise RuntimeError('Engine is closed')
        if not commands:
            raise ValueError('Empty schedule')
        mask = np.ones(20, dtype=bool) if valid is None else np.asarray(valid)
        if mask.shape != (20,) or mask.dtype != np.bool_:
            raise ValueError('valid must contain 20 booleans')
        previous = self.previous.copy()
        ids = self.command_ids.copy()
        rows, receipts = [], []
        start = self.time_us
        for index, command in enumerate(commands):
            timestamp = start + index*BIN_US
            currents = self._validate(command, timestamp, previous, ids)
            missing = command is None
            identity = f'missing:{timestamp}' if missing else command.command_id
            receipts.append(Receipt(self.config.trial_id, identity, timestamp, timestamp,
                timestamp+BIN_US, None if missing else tuple(command.current_pA),
                tuple(currents), 'fallback' if missing else 'delivered',
                'missing command: bounded ramp to zero' if missing else ''))
            rows.append(currents)
            previous = currents
            if not missing:
                ids.add(identity)
        self.group.namespace['stim_origin'] = start*b.us
        self.group.namespace['stim_table'] = b.TimedArray(
            np.column_stack((np.zeros(len(rows)), rows))*b.pA, dt=.02*b.second)
        end = start + len(rows)*BIN_US
        times, neurons = [], []
        neural_ns = 0
        while self.time_us < end:
            block = self.time_us // 1_000_000
            if block != self._noise_block:
                noise, fine_hash = innovations(self.config, block)
                self.noise_hashes[str(block)] = dict(fine=fine_hash, effective=digest(noise))
                self.group.namespace['innovation'] = b.TimedArray(noise, dt=(self.config.dt_us / 1_000_000)*b.second)
                self.group.namespace['noise_origin'] = (block*1_000_000)*b.us
                self._noise_block = block
            next_stop = min(end, (block+1)*1_000_000)
            if chunked:
                next_stop = min(next_stop, self.time_us+BIN_US)
            t0 = time.perf_counter_ns()
            self.net.run((next_stop-self.time_us)*b.us, namespace={})
            neural_ns += time.perf_counter_ns()-t0
            # Brian timestamps identify the integration grid's threshold slot.
            times.append(np.rint(np.asarray(self.monitor.t[self._cursor:]/b.us)).astype(np.int64))
            neurons.append(np.asarray(self.monitor.i[self._cursor:], dtype=np.int64).copy())
            if self.config.retain_spikes:
                self._cursor = len(self.monitor.i)
            else:
                self.monitor.resize(0)
                self.monitor.variables['N'].set_value(0)
                self._cursor = 0
            self.time_us = next_stop
            for field in ('v', 'I_E', 'I_I', 'eta'):
                if not np.all(np.isfinite(np.asarray(getattr(self.group, field)))):
                    raise RuntimeError(f'Nonfinite neural state: {field}')
        if int(round(float(self.net.t/b.us))) != end:
            raise RuntimeError('Neural clock disagrees with command clock')
        all_times = np.concatenate(times)
        all_neurons = np.concatenate(neurons)
        channels = self.lookup[all_neurons]
        recorded = channels >= 0
        results = []
        t0 = time.perf_counter_ns()
        for index, receipt in enumerate(receipts):
            bin_start = start+index*BIN_US
            counts, rates, coverage, event_times, event_channels = bin_events(
                all_times[recorded], channels[recorded], bin_start, bin_start+BIN_US, mask)
            sector, filtered = self.rate_filter.update(counts, bin_start+BIN_US)
            observation = Observation(self.config.trial_id, bin_start, bin_start+BIN_US,
                bin_start+BIN_US, tuple(map(int, counts)), tuple(rates),
                tuple(map(int, coverage)), tuple(map(bool, mask)),
                tuple(map(int, event_times)), tuple(map(int, event_channels)),
                sector, filtered, self.rate_filter.initialized)
            results.append(StepResult(observation, receipt, neural_ns//len(rows), 0))
        observation_ns = time.perf_counter_ns()-t0
        results = [StepResult(r.observation, r.receipt, r.neural_wall_ns,
                              observation_ns//len(rows)) for r in results]
        self.previous = previous
        self.command_ids = ids
        return results

    def save(self, name: str):
        self.net.store(name)
        self._snapshots[name] = copy.deepcopy((self.time_us, self.previous,
            self.command_ids, self.rate_filter, self._cursor, self.noise_hashes))

    def restore(self, name: str):
        self.net.restore(name, restore_random_state=False)
        (self.time_us, self.previous, self.command_ids, self.rate_filter,
         self._cursor, self.noise_hashes) = copy.deepcopy(self._snapshots[name])
        self._noise_block = -1

    def reset(self):
        self.restore('initial')

    def close(self):
        self._closed = True
