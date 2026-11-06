# V2 performance and style gate

**Style performance HOLD.** The baseline and style runs used Python 3.12.15 and NumPy 2.5.4 on the same macOS arm64 host, with identical requested one-thread BLAS settings. Nine samples per kernel are retained, with wall and CPU distributions. This is one sequential process pair with uncontrolled OS scheduling.

The first baseline export failed on a legitimate pre-update PI NaN. The typed-array correction preserved that state. The completed pre-style run is the fixed reference. The candidate run was retained once measured. Gates were median ratio ≤ 1.10, p95 ≤ 1.20 and peak RSS ≤ 1.10.

| Workload | Baseline p50 / p95 / p99 / max (ms) | Style p50 / p95 / p99 / max (ms) | Median ratio | p95 ratio | Gate |
|---|---:|---:|---:|---:|---|
| fir_1000_predictions | 4.993 / 5.081 / 5.102 / 5.108 | 5.042 / 5.070 / 5.076 / 5.078 | 1.010 | 0.998 | PASS |
| rls_100_updates | 2.391 / 2.489 / 2.521 / 2.529 | 2.079 / 2.147 / 2.181 / 2.189 | 0.870 | 0.863 | PASS |
| planner_625_candidates | 4.371 / 4.588 / 4.619 / 4.627 | 4.821 / 6.302 / 6.944 / 7.105 | 1.103 | 1.373 | FAIL |
| pi_1000_observations | 2.913 / 2.955 / 2.966 / 2.969 | 5.584 / 9.213 / 9.260 / 9.271 | 1.917 | 3.118 | FAIL |
| arx_fit | 1.973 / 2.112 / 2.140 / 2.147 | 1.925 / 2.388 / 2.451 / 2.467 | 0.976 | 1.131 | PASS |
| plasticity_100_updates | 0.704 / 0.727 / 0.735 / 0.737 | 0.716 / 0.745 / 0.750 / 0.751 | 1.018 | 1.025 | PASS |
| mea_100_bins | 1.984 / 2.032 / 2.046 / 2.050 | 2.017 / 2.126 / 2.134 / 2.136 | 1.017 | 1.046 | PASS |
| reservoir_100_features | 0.334 / 0.367 / 0.373 / 0.374 | 0.338 / 0.361 / 0.369 / 0.371 | 1.012 | 0.983 | PASS |

Planner and PI failed the frozen gates. A single pair cannot distinguish source effects from scheduling and process noise. The V1.1 speedup goals remain unqualified.

| Brian2 engineering workload | Baseline ms | Style ms |
|---|---:|---:|
| construction_dag_ns | 14.985 | 14.933 |
| original_construction_ns | 19.297 | 28.322 |
| neural_ns | 553.782 | 530.702 |
| observation_ns | 2.161 | 2.055 |
| feedback_and_replay_ns | 1210.780 | 1225.187 |

Process peak RSS was 986,169,344 and 986,742,784 bytes. Brian2 timings are single observations. Feedback/replay wall time includes startup and IPC.

* m017 SDK wall 5.577s. Tree RSS 266,387,456 bytes. Recording storage 15,272,148 bytes.
  * application_processing, 144 samples. p50 0.0529, p95 0.1500, p99 0.2288, max 0.2955 ms.
  * submit_to_observed_commit, 28 samples. p50 0.1906, p95 0.3523, p99 0.4159, max 0.4342 ms.
  * inter_tick_median_deviation, 135 samples. p50 0.0303, p95 0.1888, p99 0.2528, max 0.2891 ms.
* m017_style SDK wall 5.100s. Tree RSS 266,567,680 bytes. Recording storage 15,272,148 bytes.
  * application_processing, 144 samples. p50 0.0411, p95 0.1232, p99 0.2121, max 0.2476 ms.
  * submit_to_observed_commit, 28 samples. p50 0.1283, p95 0.3843, p99 0.4204, max 0.4213 ms.
  * inter_tick_median_deviation, 135 samples. p50 0.0158, p95 0.1601, p99 0.3355, max 1.9599 ms.

## Forecast-only coverage

Baseline ARX 50-step forecast p50/p95/p99/max over nine samples was 0.3180 / 0.3348 / 0.3374 / 0.3380 ms. Process peak RSS 39,043,072 bytes.
Style ARX 50-step forecast p50/p95/p99/max over nine samples was 0.3071 / 0.3286 / 0.3373 / 0.3395 ms. Process peak RSS 39,141,376 bytes.

Both forecast hashes match the exact ARX4 golden array. This supplement leaves the prior style performance HOLD in force.

## Prospective M018 performance qualification design

This design is deferred until the pre-style SDK gate qualifies. The
original M017 timing failures stand. No new performance samples were
acquired for style selection in M018.

For each coherent edit, freeze the baseline and candidate SHA, build
separate same-version environments from the same dependencies, and
check source hashes and exact fixture arrays before timing. Use 12
consecutive process pairs in one session, six baseline-first and six
candidate-first, alternating order. Use the unchanged nine-sample
kernel workloads and warm-up from the M017 probe for both processes.
Measure wall and CPU for every kernel, process RSS, thread settings,
host and process order. Avoid parallel build/test tasks during the
session. Preserve adverse samples and failures. Cap the session at
30 minutes and 2 GiB per observed worker process. A missed resource or
equivalence gate ends that edit's qualification.

For each kernel, report pooled median and p95 ratios and process-pair
bootstrap intervals by resampling complete pairs with a fixed seed
`18017`, using 10,000 draws and percentile 95% intervals. Report each
pair's result and the per-order summaries. Use the existing ceilings
median ≤ 1.10, p95 ≤ 1.20 and peak RSS ratio ≤ 1.10. Ratios above the
ceilings fail. If ratios meet the ceilings but uncertainty spans a
ceiling, retain HOLD and report the precision limit. This additional
precision rule cannot erase the original failed M017 measurements.
The previous V1.1 throughput and latency targets remain unqualified.
