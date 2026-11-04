# V1.1 P0 preregistration

Baseline scientific implementation: `abd811a053e10ad7ee5126efbc95fefd73e55c8d`.
No production code changed in P0. Fixed manifest: `benchmarks/v1_1_manifest.json`.
Run with pinned Python 3.12 stack and `PYTHONPATH=src python benchmarks/v1_1.py --output FRESH`.
900-second suspend-inclusive shared supervisor deadline per stage, 4 GiB per-worker RSS gate,
maximum three variants; no reserved or locked networks. Measurements and profile attribution
precede changes. Targets: 2x workflow and neural throughput; 30% planner p95 reduction.
Exact numerical equivalence is mandatory; unattained speed targets remain failures.
OS cache is not flushed: first subprocess import is process-cold, not disk-cold.
Profiler/tracemalloc runs include instrumentation overhead; comparisons use identical harness.

## Executed P0

Both initial instrumented and corrected independent uninstrumented timings retained. The latter is the comparison baseline. No production changes.

```json
{
  "planner_ms": {
    "p50": 4.409791500000001,
    "p95": 4.711419049999999,
    "p99": 5.0823924100000015,
    "max": 5.438833
  },
  "bank_ms": {
    "p50": 0.577375,
    "p95": 0.6132452,
    "p99": 0.6434703300000002,
    "max": 0.685875
  },
  "rls_ms": {
    "p50": 0.025583,
    "p95": 0.0322122,
    "p99": 0.16845833000000007,
    "max": 0.176708
  },
  "fir_ms": {
    "p50": 0.0082915,
    "p95": 0.01264795,
    "p99": 0.015270240000000032,
    "max": 0.021333
  },
  "block_s": 0.729837334,
  "chunked_s": 1.832073833,
  "noise_s": 0.13153575,
  "noise_peak_traced_bytes": 480002508,
  "neural_peak_rss_bytes": 1013923840,
  "signature": "15f9eb952e0ad2e6168795a7100dc868389a4bb9dc729121024697f497551137",
  "neural_signatures": [
    "2bade996742bf0a9ef548c8a16fa44ae7b2121d0f41bf203684e0d29a176bcebd16f5764fc2e1cf4b0e9eb1739400b26058a334433f8ac35231c5f26e97b7052",
    "2bade996742bf0a9ef548c8a16fa44ae7b2121d0f41bf203684e0d29a176bcebd16f5764fc2e1cf4b0e9eb1739400b26058a334433f8ac35231c5f26e97b7052",
    "2bade996742bf0a9ef548c8a16fa44ae7b2121d0f41bf203684e0d29a176bcebd16f5764fc2e1cf4b0e9eb1739400b26058a334433f8ac35231c5f26e97b7052",
    "2bade996742bf0a9ef548c8a16fa44ae7b2121d0f41bf203684e0d29a176bcebd16f5764fc2e1cf4b0e9eb1739400b26058a334433f8ac35231c5f26e97b7052",
    "2bade996742bf0a9ef548c8a16fa44ae7b2121d0f41bf203684e0d29a176bcebd16f5764fc2e1cf4b0e9eb1739400b26058a334433f8ac35231c5f26e97b7052",
    "2bade996742bf0a9ef548c8a16fa44ae7b2121d0f41bf203684e0d29a176bcebd16f5764fc2e1cf4b0e9eb1739400b26058a334433f8ac35231c5f26e97b7052"
  ],
  "noise_hashes": [
    [
      "bba301b6ea56d0454a4258c5ab76c6878e08340a9b500c6c3440e22a8dd581ad",
      "f5424a5e6a0dedb2c4db9c7028e4102196597095cea9baf0d0cafbbc7b753173"
    ],
    [
      "11349292eec3582039346439554341df0f3f5aa791490744b764925998d3a2e9",
      "d5699e8340aac7e4821171933085b959e18137ca11d582b07e128c94124523d1"
    ],
    [
      "c2583bf8940921b0f353765ed8bee4fccc001ddeafb01e6e532057287d326fe5",
      "6d206dc2cd3884cd29dd9c7d35080544a28c011bde62fe035db2d32f7bf2df8a"
    ]
  ],
  "workers": {
    "1": {
      "wall_s": 6.48336458299309,
      "total_simulated_s": 2
    },
    "2": {
      "wall_s": 3.8040297500556335,
      "total_simulated_s": 2
    }
  },
  "storage": {
    "False": {
      "write": {
        "wall_s": 0.000475875,
        "cpu_s": 0.000476
      },
      "read": {
        "wall_s": 0.000718125,
        "cpu_s": 0.000574
      },
      "bytes": 1600266
    },
    "True": {
      "write": {
        "wall_s": 0.064993625,
        "cpu_s": 0.064767
      },
      "read": {
        "wall_s": 0.001163833,
        "cpu_s": 0.001164
      },
      "bytes": 302991
    }
  },
  "startup_s": [
    0.503286959,
    0.631811,
    0.513368833
  ],
  "workflow_s": 28.36023899999998
}
```

Profiled 20ms path: 2.592 s total; Brian before_run0.965s (37.2%), explicit gc.collect0.667s (25.7%), code-object execution0.584s (22.5%), innovations0.132s (5.1%). Categories nest; do not sum overlapping Brian internals. Planner profile and code-object breakdown are separate artifacts.

| Priority | Component | Measured cost/share | Opportunity | Complexity/risk | Memory tradeoff |
|---|---|---|---|---|---|
| 1, deferred | repeated Brian setup/GC | 37.2% +25.7% of profiled stepped fixture | supported backend/lifecycle investigation | high; do not patch Brian internals | unknown |
| 2, accept experiment | noise hashing/temporaries | innovations5.1% stepped, larger in blocks | buffer hashing/in-place coarse arithmetic | low; exact hash/spike gates | lower allocation |
| 3, accept experiment | candidate bank | see micro profile; ~0.7ms per bank | skip projection after fixed hold reached | low; all625 score/action equality | same output allocation |
| 4, retain | process scheduling | one-vs-two-worker measured above | no unrestricted worker increase | memory/scheduler risk | nested-worker RSS limitation |
| 5, defer | evidence compression | paired synthetic write/read above | compression trades write CPU for size | archival migration not authorized | keep all historical evidence |

No Numba/C++ backend qualified here. Original engine explicitly uses NumpyCodeObject; changing it requires new trajectory qualification. Block stepping is already available and cannot replace observation-dependent decisions. IPC measurements include separate neural-child CPU/RSS not charged to parent getrusage; nested peak memory is NOT established by parent RSS. CPU timings cover process CPU, not aggregate descendants. Storage fixture is synthetic monotonic integers, not representative compressibility of arbitrary spikes. Thread requests are not verified BLAS thread counts. These small fixtures do not benchmark the full scientific study.
