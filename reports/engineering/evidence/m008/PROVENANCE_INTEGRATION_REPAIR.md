Full attempt16602cb4:215passed,1failed,25warnings,40.67s. All supervisor tests passed.
The historical M002.3 preservation gate expected .github/workflows/ci.yml SHA256
19d7133d22a800d812bfe3f0c3858e072a050366da52cb9e34be86529f2396e5.
CI artifact-retention edits correctly changed the live workflow, so the assertion rejected it.

Repair:archive exact ce147866 Git bytes as docs/history/CI_M002_3_SNAPSHOT.yml and map only
that historical path to the snapshot. The old expected digest and all other hash assertions
remain unchanged. New CI is independently qualified against its own source revision.
No scientific result/protocol/dependency, numerical source or deadline assertion changes.
Failed attempt retained; full suite is rerun on the explicit repair, not silently relabelled.
