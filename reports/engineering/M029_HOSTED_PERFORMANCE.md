# M029 hosted numerical performance

M028 completed 40 branches in 54.78 s on local arm64 and 148.73 s on Linux x86-64. Intel reached 29 complete branches and 93,000 retained updates before the 240-second deadline. Its 329.6 s estimate for all 40 was an extrapolation from a partial run. [M028 baseline](M028_FINAL_CLOSURE.md).

The M029 times include launcher, isolated processes, shared supervisor, cleanup and integrity-checked aggregation. Each component contains the same first eight archived branches. CPU is total observed child CPU from the launcher, in seconds. RSS is the largest one-second sample of the launcher, coordinator and registered worker groups in MiB. RSS sampling provides a lower bound on the true simultaneous peak. Full per-worker startup, CPU, RSS and scheduling records are retained.

| Source and platform | Eight branches, 1 worker | Eight branches, 2 workers | Eight branches, 4 workers | Complete stage |
| --- | ---: | ---: | ---: | ---: |
| M028 proof, local arm64 | 11.533 s | 6.309 s | 3.576 s | 40/40 at 17.549 s, 4 workers |
| M028 proof, hosted Linux | 33.135 s | 16.951 s | 15.260 s | 40/40 at 73.715 s, 4 workers |
| M028 proof, hosted Intel | 54.551 s | 26.625 s | NOT RUN | NOT RUN |
| Ordered proof, local arm64 | 11.717 s | 7.175 s | 6.138 s | 40/40 at 22.945 s, 4 workers |
| Ordered proof, hosted Linux | 33.026 s | 17.201 s | 14.816 s | 40/40 at 73.597 s, 4 workers |
| Ordered proof, hosted Intel | 89.348 s | 39.546 s | NOT RUN | NOT RUN |

The Intel components completed within their 180-second component budgets. Both runs stopped at the equality gate before a complete Intel stage. The observed two-worker scaling was 2.05× with the original arithmetic and 2.26× with the ordered fallback. Five times the final two-worker component wall time is 197.7 s. It is an extrapolation from unqualified component throughput. Intel runs used separate hosted instances, so differences between attempts do not isolate a kernel speed change.

| Ordered proof execution | CPU, 1 / 2 / 4 workers | RSS, 1 / 2 / 4 workers | Full-stage CPU / RSS |
| --- | --- | --- | --- |
| Local arm64 | 11.721 / 13.171 / 18.559 s | 128.7 / 177.9 / 309.5 MiB | 83.467 s / 312.4 MiB |
| Hosted Linux | 33.063 / 33.731 / 57.405 s | 154.7 / 222.8 / 358.6 MiB | 285.924 s / 367.6 MiB |
| Hosted Intel | 90.003 / 78.884 / — s | 108.2 / 157.3 / — MiB | NOT RUN |

Linux and Intel both reported four available CPUs and at least 14 GiB of memory. The fixed selection allowed up to four workers and requested one BLAS thread per worker. The NumPy runtime reports identify OpenBLAS on Linux and Accelerate on Intel. Direct BLAS pool counts were unavailable because the runtime introspection package was absent. The CPU totals and wall times expose contention. For example, ordered Linux four-worker component CPU rose from 33.731 s at two workers to 57.405 s, while wall time fell by 2.385 s.

Intel's final two-worker component had 0.200 s median worker startup and 55.9 MiB maximum per-worker peak RSS. Timed operations summed across its eight branches included 19.565 s for state residuals, 14.237 s for information recurrence, 13.320 s for native planning, 10.152 s for native updates, 8.637 s for planner certificates and 1.495 s for progress persistence. These overlapping worker durations identify computational costs. They are not contributions that can be added to obtain stage wall time. Further speed optimization would not address the observed equality failure.

The full ordered Linux run completed 128,000 updates and 2,560 exact planner decisions with four workers. Its measured end-to-end wall time was about 2.02× faster than the original M028 Linux worker time. The local ordered run was about 2.39× faster than the M028 local worker time. The comparison includes different scheduling and verification arrangements. Per-branch outcomes, stage profiles, initial failed attempts and both Intel fingerprint differences are in the retained evidence.

[Original parallel CI](https://github.com/adithyakupad/neuromancer/actions/runs/42537331495) · [Ordered fallback CI](https://github.com/adithyakupad/neuromancer/actions/runs/42538164882)
