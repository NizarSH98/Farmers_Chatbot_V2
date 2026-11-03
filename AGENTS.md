# Agent instructions

<!-- projectgraph:begin -->
## ProjectGraph

This repository is ProjectGraph-enabled. Its project map, state and
verification evidence live in `.projectgraph/`.

Before starting work in a new session:

1. `projectgraph validate` - confirm the graph is trustworthy.
2. `projectgraph status` - read current state instead of re-reading the repo.
3. `projectgraph next` - pick a node that is legally workable.
4. `projectgraph inspect <NODE>` and `projectgraph begin <NODE>` before edits.
5. `projectgraph verify <NODE>` after implementation.

`VERIFIED` is computed from verification evidence. Never claim it directly;
run `projectgraph verify` and report its result.
Full procedure: the globally installed `projectgraph` Agent Skill.
<!-- projectgraph:end -->
