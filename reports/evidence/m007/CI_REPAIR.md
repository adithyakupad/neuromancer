# CI configuration repair

The first M007 push3fb6f2ba5e4ae706f06e6cd3d51469bf7395c36b produced workflow-parser failure41344138785 with no jobs. The audit introduced runner.temp at jobs.qualification.env. GitHub context availability excludes runner at job env scope: https://docs.github.com/en/actions/reference/workflows-and-actions/contexts . The original V1 used github.workspace, which is allowed.

Replace the introduced expression with a literal /tmp directory supported by both Linux/macOS jobs. No dependency, numerical source, test, stimulus, seed, endpoint or threshold changes. Preserve initial failure and rerun dedicated-branch CI.
