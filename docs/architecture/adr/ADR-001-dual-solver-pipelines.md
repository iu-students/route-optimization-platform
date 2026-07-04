# ADR-001: Maintain Two Independent Solver Pipelines (CP-SAT and PyVRP)

**Status:** Accepted

**Quality requirements addressed:** QR-003

## Context

The system solves the same CVRPTW problem with two independent implementations:

- **Pipeline A** (`main.py`, `vehicle_routes.py`, `loader_routes.py`) — generates a
  route pool via Clarke-Wright and insertion heuristics, then selects the optimal
  subset with OR-Tools CP-SAT.
- **Pipeline B** (`script.py`, `loaders.py`) — uses the PyVRP library for vehicle
  routing and a greedy chain-building heuristic for loader assignment.

Only Pipeline A is wired to the Flask API (`app.py`). Pipeline B is invoked
manually via CLI and used by `tester.py` to produce an independent baseline
solution for comparing Pipeline A's output cost.

The team needed to decide whether to keep both pipelines or consolidate into one.

## Decision

Keep both pipelines as separate, non-unified code paths. Do not merge them into a
shared solver abstraction. Pipeline A remains the only one wired to the API.

## Rationale

- An independently implemented algorithm (PyVRP + greedy heuristic) gives a
  genuine baseline for solution-quality comparison. A shared abstraction between
  the two would defeat this purpose — bugs or bias in one implementation could
  propagate into the other.
- Pipeline A can evolve (different heuristics, different constraints) without
  needing to keep the comparison baseline synchronized.
- Unifying them now would require redesigning both around a common interface,
  a cost not currently justified by the product's needs.

## Consequences

### Positive

- Solution quality can be independently verified by comparing Pipeline A against
  Pipeline B on the same test cases (`tester.py` → `comparison.xlsx`).
- Each pipeline can be modified without risk of breaking the other.

### Negative

- Route-generation logic (constraints, cost calculation) must be changed in two
  places if both pipelines are to stay behaviorally consistent.
- Automated test coverage effort is duplicated across two independent solver
  implementations.

### Tradeoffs

- A shared solver abstraction was considered but rejected: it would eliminate the
  independence needed for baseline comparison and add coupling between code paths
  that currently serve different purposes (production vs. offline validation).

## Links

- [QR-003: Critical module testability](../../quality-requirements.md#qr-003-critical-module-testability)
- [Component Diagram](../static-view/component-diagram.puml)