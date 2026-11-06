"""Deterministic M023 and M025 mechanism fixtures. No historical outcomes read."""
from itertools import combinations
import json
from math import exp
from pathlib import Path
import sys


def plasticity():
    eligibility = [4, 2, -1, -1]
    rows = []
    for positive in combinations(range(4), 2):
        rewards = [1 if i in positive else -1 for i in range(4)]
        signed_mean = sum(reward * trace for reward, trace in zip(rewards, eligibility)) / 4
        rows.append(dict(rewards=rewards, signed_mean=signed_mean))
    return dict(eligibility=eligibility, unmodulated_mean=sum(eligibility)/4,
                assignments=rows, attenuation=[1, exp(-1), exp(-2)])


def controller(target, gain, lag, policy):
    actions = []
    trace = []
    integral = 0
    for tick in range(24):
        prior = actions[tick-lag] if tick >= lag else 0
        rate = 1 + gain * prior
        error = target - rate
        pulse = False
        if tick < 23:
            if policy == 'pi':
                pulse = error + .2 * integral > .5
            elif policy == 'predictive':
                pulse = abs(target - 4) + .1 < abs(target - 1)
        # With the fixed one-bin hardware receipt contract, successful
        # pulse action is resolved before the next decision. Plant lag
        # can change independently of the command acknowledgement.
        if policy == 'pi' and (tick < 23):
            integral = max(-2, min(2, integral + error))
        actions.append(int(pulse))
        trace.append(dict(count=rate, error=error, pulse=pulse, integral=integral))
    return dict(mae=sum(abs(row['error']) for row in trace)/24,
                pulses=sum(actions), trace=trace)


def main(path):
    result = dict(plasticity=plasticity(), control={
        f'target-{target}_gain-{gain}_lag-{lag}': {
            p: controller(target, gain, lag, p) for p in ('no_pulse', 'pi', 'predictive')
        } for target in (2, 3) for gain, lag in ((3, 1), (1, 1), (3, 2))
    })
    path.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
