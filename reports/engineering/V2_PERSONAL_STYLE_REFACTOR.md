# V2 personal style review

**Numerical equivalence PASS. Performance HOLD.** The style code stays
on `refactor/v2-m017-personal-style`. Its implementation revision is
`a9e7ee788cc2036a0a642254fbd00d2298ef110d`. Integrated baseline
`4ec262486ab953591b90c860dd3515ce531789b7` is evaluated independently.

The [style guide](../../docs/development/CODING_STYLE_V2.md) records
observations from retained renders of sweetCombo, getCar, exitStrategy
and boxInventory. The source PDF was absent at its original path.
The earlier unqualified branch was consulted as a reference. No source
commits from it were imported and generated code is not attributed
to the student.

## Readability changes

Audited 84 tracked Python files across package, runners and tests.
Formatted 18 files, with exact AST equality at the formatting checkpoint.
On those files, maximum line length dropped from 566 to 100, statements
joined by semicolon from 201 to zero, and lines above 100 from 172 to zero.
These proxies do not measure understanding.

- V1 control and inference. `control.py`, `identify.py`,
  `online_identify.py`, `predictive.py`, `predictive_planner.py`.
- V2 computation and SDK. `plasticity.py`, `functional_learning.py`,
  `reservoir.py`, `causal_memory.py`, `neural_io.py`, `cl_adapter.py`,
  `cl_response_source.py`.
- Active research runners. M013 and M014 pilot and analysis scripts,
  M015 memory runner and M016 SDK runner.

Manual changes named the RLS residual, PI proposed integral and
proportional action, and expanded SDK proposal and channel selection
branches. Public signatures, operation order for numerical updates,
arrays and protocol bounds remain as checked in the exact probe.
The review retains original hash-protected M002 paths, Brian equations,
supervisor and clocks, historical acquisition and evidence scripts outside
the review scope, and test assertions. Already clear or high-risk code
was left in place. Remaining complexity includes predictive receipt
state transitions, scientific branch bookkeeping and process ownership.

Before, the residual was embedded in the coefficient update.

```python
theta = self.theta + np.outer(gain, v - z @ self.theta)
```

The candidate names the residual before publication of the update.

```python
prediction_residual = v - z @ self.theta
theta = self.theta + np.outer(gain, prediction_residual)
```

PI separates its proposed integral, proportional term and saturation
decision. SDK proposal generation uses explicit controller versus
open-loop branches, then names a late rejection fixture and selects
the requested channel. FIR/ARX lag assembly, candidate scoring and
STDP vectorization retain the same operations.

## Verification and disposition

Both full suites passed 228 tests. The 102 arrays matched dtype,
shape and bytes, and deterministic records matched exactly. The
probe covers continuous/chunked spikes, recorded observations,
noise and realization identity through replay, FIR/ARX predictions,
RLS state, PI state and actions, all MPC candidate arrays, eligibility,
reward update, graph, schedules, reservoir feature and decoder arrays
and frame/bin conversions. Historical tests independently check noise
stream identity. The SDK matrix passed again with exact semantic ledgers
and callbacks across 144 windows. Timing and HDF5 metadata are separate.
M013/M014 archive summaries also reproduced exactly.

The planner p95 ratio 1.373 and PI p95 ratio 3.118 exceeded the
frozen 1.20 ceiling. Median ratios 1.103 and 1.917 also exceeded 1.10.
Peak RSS passed. This is one process pair, so the results do not
identify cause. Neither a favorable rerun nor a changed gate was
used. A formatting-only gate and passing tests do not override
measured performance failure.
[Performance measurements](../V2_PERFORMANCE.md)
