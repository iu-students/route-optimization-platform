# ADR-001: Maintain Two Independent Solver Pipelines

**Status:** Declined / Superseded as of MVPv3 by [ADR-009: Consolidate to a Single CP-SAT Solver Pipeline](ADR-009-single-solver-pipeline.md). This record is kept for historical context; do not treat it as the current architecture.

**Quality requirements addressed:** QR-003

## Context

The system solves the same CVRPTW problem with two independent implementations:

- **Pipeline A** (`main.py`, `vehicle_routes.py`, `loader_routes.py`) - generates a
  route pool via Clarke-Wright and insertion heuristics, then selects the optimal
  subset with OR-Tools CP-SAT.
- **Pipeline B** (`script.py`, `loaders.py`) - uses the PyVRP library for vehicle
  routing and a greedy chain-building heuristic for loader assignment.

Only Pipeline A is wired to the Flask API (`app.py`). Pipeline B is invoked
manually via CLI and used by `tester.py` to produce an independent baseline
solution for comparing Pipeline A's output cost.

The team needed to decide whether to keep both pipelines or consolidate into one.

## Decision

Keep both pipelines. Pipeline A remains the only one wired to the API; Pipeline B
is retained purely as an independent, manually-invoked baseline for offline
comparison via `tester.py`.

## Rationale

- Pipeline B provides a genuinely independent cross-check on solution quality: a
  bug or systematic bias in Pipeline A's heuristics is unlikely to also exist in
  PyVRP's differently-implemented solver.
- `tester.py` already depends on Pipeline B's output as its baseline; removing it
  would require sourcing a baseline some other way.
- The two pipelines are cleanly separated (different files, no shared solver
  code beyond `Shared/models.py` and `Shared/verifier.py`), so maintaining both
  does not require constant synchronization of internals - only of the shared
  data contracts.

## Consequences

### Positive

- An independent implementation exists to validate Pipeline A's solution quality
  and catch bugs that share a common blind spot with Pipeline A's own heuristics.
- `tester.py`'s comparison workflow has a live, regenerable baseline rather than a
  static frozen file.

### Negative

- Every routing-constraint change has to be considered for, and potentially
  implemented in, both pipelines, or the two silently drift apart in behavior.
- Test coverage effort is split across two independent solver implementations.

### Tradeoffs

- Consolidating to a single pipeline was considered and rejected at this point:
  Pipeline A's own heuristics were not yet mature enough to provide an internal
  cross-check on solution quality, so an external independent baseline (Pipeline B)
  was still needed.

## Links

- [QR-003: Critical module testability](../../quality-requirements.md#qr-003-critical-module-testability)
- [Component Diagram](../static-view/component-diagram.puml)
- [Superseded by: ADR-009 (MVPv3) - Single CP-SAT solver pipeline](ADR-009-single-solver-pipeline.md)
