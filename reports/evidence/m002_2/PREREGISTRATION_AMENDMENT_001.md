# M002.2 amendment 001 — pre-execution charge arithmetic correction

Committed before any scientific simulation, after schedule-only unit tests caught an arithmetic error. Original preregistration 19307f9 is retained unchanged. No measured neural outcome motivated this correction.

The prescribed PULSE shape sums per active channel to30+60+90+120+120+90+60+30=600 pA-ticks per cycle, not720. At20 ms/tick, two channels, six cycles its total exposure is **144 pA*s**, not172.8. Preserve the pulse amplitude, duration, slew and recovery exactly as preregistered. Replace the intended charge-matched constant D7.2 with **D6=[6,6,6,6] pA**, delivering144 pA*s over6 s. Action name D6 replaces D7.2 everywhere in executable manifests/analysis. The paired dynamic comparison is PULSE−D6. No other action, duration, cohort, seed, outcome, threshold, resource budget or analysis rule changes.

Both this amendment and the original preregistration are source-hashed by the runner. Schedule constraints and all three exact-charge matches must pass before neural execution.
