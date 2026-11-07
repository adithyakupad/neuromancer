# NEUROMANCER V2 Core Research Candidate

NEUROMANCER is a reproducible in-silico platform for stimulation-response
identification, causal feedback, spiking plasticity and reservoir experiments.
This branch packages the cumulative V1 and M013–M016 implementation as
`2.0.0rc1`.

**Supported release boundary:** The independently qualified core covers in-silico Brian2 dynamics, simulation-based identification and control, supervision, reproducible evidence and its installable CLI. The **Cortical Labs CL SDK 1.0.0 accelerated simulator adapter is experimental and NOT reliability-qualified**. In particular, macOS Intel has shown intermittent frame-producer stalls after a published request and before the source callback. A passing SDK matrix does not resolve this failure. There has been **no living-neuron or physical hardware execution** and there are **no hard-real-time guarantees**. See the [approved core support boundary](docs/V2_CORE_RELEASE_SCOPE_REVIEW.md), [release notes](docs/V2_CORE_RELEASE_NOTES_DRAFT.md), and [open SDK reliability issue](https://github.com/adithyakupad/neuromancer/issues/7).

| Path | Evidence |
|---|---|
| Brian2 E/I LIF, FIR/ARX/RLS and PI/MPC | V1 numerical evidence and a short engineering feedback replay |
| Optional reward STDP and temporal decoding | M013 pilot, superiority inconclusive |
| Frozen reservoirs and causal access controls | M014 inconclusive, M015 retention held after the cue gate |
| CL SDK simulator and MEA adapter | M016 software loop qualified, tracking improvement failed |
| Physical hardware and biological validation | Hardware unvalidated, biological experiment not run |

The V1 tracking errors remain PI 11.46875, adaptive RLS-MPC 13.12921875
and fixed MPC 18.9778125 Hz·s. The SDK fixture PI likewise had higher
tracking MAE than its frozen no-pulse control.

- [Installation and three demonstrations](docs/V2_QUICKSTART.md)
- [Architecture and units](docs/ARCHITECTURE_V2.md)
- [Reproducibility and provenance](docs/V2_REPRODUCIBILITY.md)
- [Scientific limitations](docs/V2_SCIENTIFIC_LIMITATIONS.md)
- [Evidence ledger](reports/V2_EVIDENCE_LEDGER.md)
- [Qualification report](reports/V2_FINAL_QUALIFICATION.md)
- [Technical defense guide](docs/INTERVIEW_TECHNICAL_DEFENSE.md)

The source is MIT licensed. Experimental archives are retained in Git
and excluded from the installable wheel.
