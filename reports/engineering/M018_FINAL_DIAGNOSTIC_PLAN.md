# M018 final diagnostic extension

The investigation starts from the verified M018 tip
`bcaa941020fbed00f1afe30d2dce57ea6a556c9a`. Review all existing hosted
attempts, including automatic push and pull-request duplicates. Stop
adding repetitions if the probes below do not localize the failure.

1. Exercise trace iterator exhaustion with deterministic tests. Make
   traces opt-in and keep scientific and diagnostic streams separate.
   Verify this on one traced local SDK matrix. Use the original 120-second
   watchdog and full nine-session, 144-window verifier.
2. Run one new macOS Intel hosted diagnostic matrix with corrected
   instrumentation. Linux uses the normal matrix as a control. Neither
   job changes frame counts, simulator timing, SDK version or deadlines.
3. Run one independent macOS Intel stock SDK probe in the diagnostic
   workflow, even if its full matrix fails. A local arm64 run serves as
   a portability check. The stock probe has nine sessions and sixteen
   500-frame ticks per session, no recording, no stimulation, and no
   NEUROMANCER custom source or consumer code. Use the same 120-second
   watchdog. Record full SDK dependency resolution, worker exit status,
   trace and observed descendants. A stock failure demonstrates that
   application components are unnecessary for that failure. A stock
   pass cannot identify which removed component, if any, contributes.
4. Associate each SDK timeout with the affected case and tick. Compare
   source begin/end frame ranges with consumer begin/end and processing,
   session/recording boundaries, callback and recording evidence. A
   source callback returning a batch does not prove ring publication.
   Missing evidence remains unknown. Timestamp distances compare host
   monotonic records only. The SDK frame counter has a separate domain.
5. Evaluate the original release and optional refactor independently.
   No style integration is eligible while the mandatory pre-style SDK
   gate remains failed. No SDK workaround is eligible without evidence
   that it addresses the observed mechanism and preserves all fixtures.
