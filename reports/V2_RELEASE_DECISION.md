# V2 release options

## Full V2 with mandatory SDK reliability

**HOLD.** The recording extent repair addresses the extra batch
that the SDK may request after the final consumed yield. It does
not address the intermittent macOS Intel frame wait. M019 observed
a published request and a stationary write head before the source
callback. M020 producer traces on completed sessions did not
identify the failed producer request load or scheduler boundary.
A passing matrix qualifies its executed cases and cannot satisfy
the unresolved scheduling requirement.
[M019 failure and boundary](https://github.com/adithyakupad/neuromancer/blob/engineering/m019-producer-boundary/reports/engineering/M019_PRODUCER_BOUNDARY.md) ·
[M020 producer investigation](https://github.com/adithyakupad/neuromancer/blob/engineering/recover-sdk/reports/engineering/M020_SDK_PRODUCER_DIAGNOSIS.md)

## Separately scoped core V2 research release

**Proposal for maintainer review. Publication HOLD pending explicit
scope approval and any required exact-head core qualification.**
Define the supported boundary as the pinned Brian2 research wheel,
causal simulator interfaces, model and controller tooling, and
archived in silico reproduction. Its acceptance evidence should
include clean Linux/macOS installs, complete core regression and
supervisor checks, installed CLI smoke, exact numerical fixtures,
preserved V1 and V2 archive reconstruction, and explicit negative
findings.

The SDK adapter would be identified separately as an experimental,
simulator-only integration, installed in its own pinned environment.
Keep the hardware interlock and existing SDK CI, label the observed
macOS Intel scheduling limitation in user-facing release materials,
and make no claim of biological validation or real-time guarantees.
The release scope and the role of SDK CI would require a prospective
maintainer decision. M026 changes neither the current mandatory
checks nor the package metadata. No merge, tag or publication is
authorized by this proposal.

The optional personal-style branch remains HOLD under its own
performance gates. Historical results and the baseline package
version `2.0.0rc1` remain unchanged.

## M026 final assessment

Integration revision `27872242ef2885fec8a04a7c6061584b6cb68c76` passed
the complete local regression and all exact-head hosted jobs. Both
hosted core platforms passed 231 tests and clean wheel/CLI checks.
Both hosted SDK matrices passed the original recording and
stimulation checks. Canonical V1 and M013–M016 archive evidence and
102 golden arrays verified. This qualifies the engineering changes
and demonstrates core technical readiness for scope review. The
full V2 decision remains **HOLD** for the unresolved SDK producer
stall. The separately scoped core proposal remains **HOLD for
publication** until explicit maintainer approval of the revised scope.
No workflow was removed, and no release ref was merged, tagged or
published.
[Executed integration report](engineering/M026_INTEGRATION.md)
