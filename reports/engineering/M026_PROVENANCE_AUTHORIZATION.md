# M026 v1 exact-file provenance authorization

The M017 historical baseline manifest remains byte-identical.
Its SHA-256 is
`f88c41d51355e115863fd1a12dee6901aa4034ac7bf68f86c0c64e622e1719b1`.
The release verifier first authenticates those bytes, then verifies all
38,721 entries. M026 authorizes precisely these active-file replacements.

| Path | Historical SHA-256 | Authorized active SHA-256 |
|---|---|---|
| `scripts/m016_run.py` | `781893b0e301d2b858b185b19db4b322451c0d8ed58255a356dda5ad4a826a1b` | `03661773740d1b0fcb83fa8eddc1496f06c5fd432f72119670e84f6ebae3dad6` |
| `scripts/m016_verify.py` | `9d2e26072c913e47695cdf54146a73d670bde94d6c162e329120273d978c41f2` | `46cb116e269c25a0ec89c60db12c69c519ca756ee28a2e835dc8fb57fb91ee3d` |
| `tests/supervisor_worker.py` | `c19982062ba119b1a86db187d62c2ee9b1f25725398a526a36e60072250b2fef` | `2e9a482da8a7819926531119fc9c73b2c4106f9e44f8368858bbddd3ac722471` |

- The runner is the byte-identical M021 final-yield recording repair
  from `35f338dc52adc3ea19c2268dd019c05ce51ca05a`.
- The SDK verifier is the exact previously integrated M017 file already
  present at `70e976c1e990db2fbbc88f786b5d7c06a691aa70`. M026 did not
  edit it. This entry replaces the earlier path-only exception.
- The synthetic worker is the byte-identical correction from
  `c91cd4d5e2884a6f03333118762ffe30573e7228`. Its diff contains a
  single changed block. It writes the same four values to a sibling
  staging path and renames it into place after the write returns.
  Publication is atomic for readers on the same filesystem. The
  change makes no crash-durability claim. Deadline handling, process
  lifecycle and assertions remain unchanged.

The verifier authenticates the historical digest for each entry before
using the authorized active digest. It rejects any third digest and
requires an ordinary file for each replacement. The old path-only
style exceptions are removed on this release branch. Every other
manifest entry retains its original digest. No scope or historical
experiment is reclassified. The regression simulates a further edit
to the authorized fixture and requires preservation failure. An
interruption test terminates the actual synthetic worker after a
partial staging write and verifies that no published PID marker exists.
