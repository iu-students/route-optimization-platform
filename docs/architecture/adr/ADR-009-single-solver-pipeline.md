# ADR-009: Consolidate to a Single CP-SAT Solver Pipeline

**Status:** Accepted. Supersedes [ADR-001: Maintain Two Independent Solver Pipelines](ADR-001-dual-solver-pipelines.md) (Declined as of MVPv3).

**Quality requirements addressed:** QR-003

## Context

Through MVPv2.2, the system solved the same CVRPTW problem with two independent implementations:

- **Pipeline A** (`CP-SAT/main.py`, `CP-SAT/vehicle_routes.py`, `CP-SAT/loader_routes.py`) - generated a route pool via Clarke-Wright and insertion heuristics, then selected the optimal subset with OR-Tools CP-SAT. Wired to the Flask API.
- **Pipeline B** (`PyVRP/script.py`, `PyVRP/loaders.py`) - used the PyVRP library for vehicle routing and a greedy chain-building heuristic for loader assignment. Invoked manually via CLI, used by `tester.py` to produce an independent baseline solution for comparing Pipeline A's output cost.

As of MVPv3, Pipeline B has been removed: there is no `PyVRP/` directory under `api/MVPv3/`, and `tester.py`'s baseline comparison reads a static, pre-computed file (`instances/output_{task}.json`) rather than invoking a live second solver. The team needed to decide whether to keep maintaining Pipeline B as CP-SAT's production pipeline matured.

## Decision

Remove Pipeline B (PyVRP) from `api/MVPv3/`. The CP-SAT pipeline is now the only solver pipeline in this version. Offline baseline comparison (`tester.py`) continues to work against previously-generated static baseline output files rather than a live independently-implemented solver.

## Rationale

- Pipeline B's main value was as a genuine, independently-implemented baseline for solution-quality comparison. Now that the CP-SAT pipeline has its own internal cross-check (multi-start with best-of selection, see [ADR-008](ADR-008-multistart-lns-search.md)) and a maturing test suite, a second live implementation adds less marginal confidence than it costs to maintain.
- `tester.py` already compared against a *file* (`BASELINE_FILE`), not a live PyVRP invocation - so dropping Pipeline B does not remove the offline comparison workflow, it only removes the ability to regenerate a fresh PyVRP baseline on demand.
- Maintaining two independent route-generation implementations meant every constraint change had to be ported to both, or the two would silently drift apart in behavior. This maintenance cost is fully paid down by removing one of them.

## Consequences

### Positive

- Route-generation logic now lives in exactly one place - a constraint change only needs to be implemented once.
- Automated test coverage effort is no longer split across two independent solver implementations.
- `requirements.txt` for MVPv3 still lists `pyvrp` as a dependency even though nothing under `api/MVPv3/` imports it; this is a leftover from copying MVPv2.2's requirements file and should be cleaned up, but does not affect runtime behavior.

### Negative

- There is no longer an independently-implemented live solver to catch bugs or systematic bias shared between the pool-generation heuristics and the CP-SAT selection step - both now live in the same codebase and could share a blind spot that a genuinely different implementation (PyVRP) might have caught.
- Existing baseline files (`instances/output_{task}.json`) can no longer be refreshed by re-running Pipeline B; they are now a frozen snapshot from whenever they were last generated under MVPv2.2 or earlier.

### Tradeoffs

- Keeping Pipeline B around unused (dead code) was considered and rejected: an unmaintained second pipeline that nothing exercises is worse than no pipeline at all, since it looks maintained but silently drifts from the current data model and constraints.

## Links

- [QR-003: Critical module testability](../../quality-requirements.md#qr-003-critical-module-testability)
- [Component Diagram](../static-view/component-diagram.puml)
- [ADR-008: Multi-start search with LNS polishing](ADR-008-multistart-lns-search.md)
