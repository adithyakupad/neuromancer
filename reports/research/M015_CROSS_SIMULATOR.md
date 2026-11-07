# M015 reduced independent simulator qualification

**QUALIFIED** for the three-cell numerical fixture. Brian2 2.10.1 was
compared with a new standalone scalar Python LIF time-stepper and explicit
event queue. The scalar integration uses no Brian code or state. The
comparison shares equations, numerical conventions and external drives,
and exercises independent implementations. Its scope is a reduced
verification benchmark. The 1,000-cell task, biological dynamics and
stochastic-generator portability are outside that scope.

## Frozen matched model

The exact [protocol](../../docs/research/M015_CAUSAL_MEMORY_PROTOCOL.md)
specifies 20 ms membrane tau, 200 pF capacitance, −65 mV rest and reset,
−50 mV threshold, 2 ms refractory, 100 µs step and 170 pA background.
The three directed synapses are 0→1 at +120 pA / 1 ms, 0→2 at +70 pA /
1.5 ms and 1→2 at −90 pA / 2 ms. Currents decay with 5 ms E and 10 ms I
time constants. Each step updates voltage with the exponential leak
solution holding currents constant, decays synaptic currents, thresholds,
delivers due events and resets. An event affects voltage on the next
integration step. This convention follows the documented Brian schedule.
[Brian2 2.10.1 Network API](https://brian2.readthedocs.io/en/2.10.1/reference/brian2.core.network.Network.html)

Each 200 ms drive has a matched sham and a +100 pA pulse into cell 0
from 40 to 100 ms. This reduced pulse uses fixture timing outside the V1
actuator interface. Deterministic drive and three separate 5 ms OU drives
use 20 ms half-open observation bins. OU arrays are generated externally
with seeds 15500–15502 and passed identically to both engines. This
controls the realization to test integration, event delivery and observation.

## Results

| Drive | Sham cell rates (Hz) | Stimulated cell rates (Hz) | Largest ISI error |
|---|---|---|---:|
| Deterministic | 20 / 25 / 15 | 30 / 25 / 15 | 0 ticks |
| OU 15500 | 20 / 30 / 15 | 30 / 30 / 15 | 0 ticks |
| OU 15501 | 20 / 20 / 15 | 30 / 25 / 15 | 0 ticks |
| OU 15502 | 25 / 25 / 15 | 30 / 25 / 15 | 0 ticks |

All eight comparisons matched per-cell firing rates and 20 ms bin counts.
Paired evoked population count traces and binned covariance matched.
The largest recorded current deviation was 7.11e−14 pA against the
frozen 1e−8 pA tolerance. The recovered E/I decay constants were 5/10 ms.
The scalar first-spike test reproduced the analytic tick 428, and the
1 ms synaptic event arrived at tick 438. Independent archive analysis
rebinned raw spikes and checked matched input contrasts and current arrays.
Small circuit size, few spikes, shared drives and shared integration
conventions limit what this verifies. No decoding experiment was run in
the independent implementation.
[Evoked response comparison](evidence/m015/cross_simulator.png)

Supervisor wall time was 1.448 s with clean completion under the 120 s
cap. Simulated duration was 1.6 s per engine. Reduced-worker peak RSS
was not instrumented. Source, original drive arrays, spikes, current
traces and summaries are archived with the provenance manifest.

```sh
PYTHONPATH=src python scripts/m014_supervise.py /tmp/m015-cross 120 python scripts/m015_cross_simulator.py /tmp/m015-cross
MPLCONFIGDIR=/tmp/m015-mpl python scripts/m015_verify.py reports/research/evidence/m015
```
