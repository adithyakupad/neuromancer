"""Deterministic M003.2 figures from frozen evaluator archives."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['svg.hashsalt'] = 'neuromancer-m003-2'
import matplotlib.pyplot as plt


def save(fig, folder, name):
    fig.tight_layout()
    fig.savefig(folder/f'{name}.png', dpi=150, metadata={'Software': 'NEUROMANCER M003.2'})
    fig.savefig(folder/f'{name}.svg', metadata={'Date': None, 'Creator': 'NEUROMANCER M003.2'})
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--analysis', type=Path, required=True); p.add_argument('--raw', type=Path, required=True)
    p.add_argument('--models', type=Path, required=True); a = p.parse_args(); d = np.load(a.analysis/'data.npz'); network = d['network']
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for m, name in enumerate(('FIR', 'STATE', 'STATE shuffled', 'Input shuffled', 'ARX')):
        axes[0].plot(range(10), network[:, m, 2], marker='o', label=name)
    axes[0].set(xlabel='Development network', ylabel='1 s effect MSE (Hz²)'); axes[0].legend(fontsize=8)
    improvement = network[:, 0, 2]-network[:, 1, 2]
    axes[1].bar(range(10), improvement); axes[1].axhline(.04, color='red', ls='--', label='Absolute gate .04 Hz²')
    axes[1].axhline(0, color='black', lw=.6); axes[1].set(xlabel='Development network', ylabel='FIR − STATE MSE (Hz²)'); axes[1].legend(fontsize=8)
    save(fig, a.analysis, 'primary_comparison')
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    origins = list(csv.DictReader((a.analysis/'origins.csv').open()))
    for s, color in (('LOW', 'blue'), ('HIGH', 'orange')):
        rows = [r for r in origins if r['stratum'] == s and int(r['replicate']) in (29, 30)]
        axes[0].scatter([int(r['network']) for r in rows], [float(r['rate_hz']) for r in rows], label=s, color=color, alpha=.7)
    axes[0].set(xlabel='Network', ylabel='Causal origin rate (Hz)'); axes[0].legend()
    for sector in range(4): axes[1].plot(range(10), d['interaction'][:, 2, sector], marker='o', label=f'Sector {sector}')
    axes[1].axhline(0, color='black', lw=.6); axes[1].set(xlabel='Network', ylabel='HIGH − LOW paired effect (Hz), 1 s'); axes[1].legend(fontsize=8)
    save(fig, a.analysis, 'state_and_interaction')
    fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharex=True)
    forecast = np.load(a.models/'n0_r29.npz')['delta']; time = np.arange(1, 101)*.02
    for row, s in enumerate(('LOW', 'HIGH')):
        sham = np.load(a.raw/'n0_r29'/s/'S.npz')['rates']
        for col, action in enumerate(('C0', 'P')):
            j = ('S', 'C0', 'C1', 'C2', 'C3', 'P', 'R').index(action)
            actual = np.load(a.raw/'n0_r29'/s/f'{action}.npz')['rates']-sham
            ax = axes[row, col]; ax.plot(time, actual.mean(axis=1), label='Measured paired effect', color='black')
            for m, name in ((0, 'FIR'), (1, 'STATE')): ax.plot(time, forecast[m, row, j].mean(axis=1), label=name)
            ax.set(title=f'Network0 / noise29 / {s} / {action}', ylabel='Mean sector effect (Hz)', xlabel='Time after origin (s)')
    axes[0, 0].legend(fontsize=8); save(fig, a.analysis, 'reserved_response_example')


if __name__ == '__main__': main()
