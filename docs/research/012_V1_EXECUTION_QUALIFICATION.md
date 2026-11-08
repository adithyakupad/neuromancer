# Operation V1 Finish — execution qualification scope

Starting scientific history at fa8f0a71c29b15678bc6cb872d88eda49ab5c81a; review branch codex/v1-finish. The M005B.2 readiness HOLD remains preserved. Protocol011, all scientific values/controller code and neural equations remain unchanged.

Stage1 restores the original pinned Python3.12 stack. Preserve the incompatible old .venv at venv/m001-python314-preserved. SciPy had no project pin; verification-only SciPy1.18.0 matches the pre-existing Anaconda installation and satisfies its recorded Python/NumPy metadata. No original dependency version is upgraded.

Stage2 is a scheduling-only optimization. A start-of-bin Brian NetworkOperation completes the preceding20ms recording, updates the unchanged controller, then validates/delivers the next command. Brian prepares one1s run at a time; OU blocks and physical integration remain identical. Numerical/model failures and missing observations still affect the next20ms command. Controllers receive no engine/private state. Exact-equivalence fixtures compare all public counts/events/timestamps/currents, controller states and terminal neural state where captured, including faults and an engineering gain step. Nonreserved network0/noise60 only; no scientific tracking scores.

Engineering profiling/qualification is bounded by one1,200s stage deadline, inherited for additional checks. Profiles include original versus optimized execution, all predictive families/PI/faults/numerical failure, and at most three simultaneous benchmark workers. No physical sleep. A source-level driver change is not qualified merely by a speedup: exact equality is mandatory. Any failure is preserved and repaired prospectively before scientific acquisition; no endpoint/seed replacement.

Scientific resource readiness must use the new measured workload and original caps: development10,800s including secondary faults; validation5,400s; <=3workers, <2GiB/worker; evidence750MiB combinedM005A/B1.2GiB. If evidence does not support those caps, stop with a prospective resource-only amendment for separate authorization, as protocol011 requires. This document does not enlarge scientific budgets.

No scientific acquisition until environment, exact equivalence, resource projection, complete seed/config/source manifest and full-regression gates pass and acquisition code is committed. The original development-to-validation gate remains authoritative. Locked100–119 stay closed.
