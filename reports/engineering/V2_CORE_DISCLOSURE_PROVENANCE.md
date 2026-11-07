# V2 Core release-facing documentation qualification

## Rationale
The earlier candidate README and quickstart did not prominently disclose the unresolved CL SDK 1.0.0 accelerated macOS Intel producer stall. The approved core-only release must distinguish tested Brian2/core functionality from experimental SDK integration at the repository landing page and demonstration command.

## Exact-file provenance
The historical M017 manifest is unchanged. The release verifier authorizes only the following additional exact active-file transitions:

| File | Historical SHA256 | Candidate SHA256 |
|---|---|---|
| README.md | `edcff65561b74ddcac4694b2d3909557b3950d3b894dd7c54aad5a161dc5ac3c` | `ce57d5ab99905c794d6a7af83688b03ad8d0d9da62b1c4cb4f83c33b2f90ca50` |
| docs/V2_QUICKSTART.md | `38fa9de5ca93fc97a4785c9d6c8f42dc1c1c8f14ae99064ab08c3c5a2eb678f9` | `6f4399ef57e1daa207f2734cb15e10a3dfc2e1dff56a47422c68cf16feb6ce17` |

The SHA256 values are fixed before CI and verified by `scripts/m017_reproduce.py`. All other protected files and the existing M026 and supervisor fixture exact-file authorizations remain unchanged. These are text-only changes to clarify the already-approved release scope. There are no numerical, hardware, controller, timeout, diagnostic or SDK behavior changes.

## Acceptance
Reverify source preservation, Linux/macOS core qualification, exact archived scientific checks and wheel/CLI smoke on the prospective publication commit. The full SDK producer-stall qualification remains HOLD independently of passing SDK smoke/matrix runs. Keep the public release labeled core-only and experimental SDK.
