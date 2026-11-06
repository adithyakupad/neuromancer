# V2 scientific limitations

- V1 supports a specific frozen simulation and control comparison.
  PI had lower cumulative error than adaptive RLS-MPC. Neither
  broader validation nor locked cohorts were opened.
- M013 and M014 each used two networks. Their positive point
  estimates were accompanied by wide network-level intervals.
  Trial count does not create independent networks.
- In M014, disconnection removes cue access because the stimulated
  and recorded cells are disjoint. M015 restored graph reachability
  with a DAG, but cue accuracy and activity matching failed. The
  retention experiment remains not run.
- The independent scalar implementation qualifies a matched
  three-cell integration fixture with explicit drives and timing.
  It does not establish cross-engine transfer of reservoir results.
- M016 validates timestamped simulator I/O and a designed response.
  PI worsened the fixture tracking MAE. Its FIR/RLS shadow replay
  used saved receipts, without control authority.
- Device frame time, host deadlines and simulation time have
  different epochs. Accelerated simulator timings characterize
  this software workload. Physical hardware and biological
  validation remain outside the evidence.

## SDK reliability across hosts

The local M016 result and the exact simulator response offsets
remain qualified for the archived fixture. Hosted macOS Intel runs
have also failed within the SDK's accelerated frame wait. The
[M018 trace](../reports/engineering/M018_SDK_FRAME_STALL.md)
records the last confirmed source and consumer boundaries.
These observations give no device timing or real-time performance
guarantee.
