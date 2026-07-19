# ADR-003: Share verifier.py Between Both Solver Pipelines

**Status:** Declined / Superseded as of MVPv3 by [ADR-010: Keep Verification as an Independent Module](ADR-010-independent-verifier.md). This record is kept for historical context; do not treat it as the current architecture.

**Quality requirements addressed:** QR-003

## Context

`verifier.py` checks a produced solution against shift-time, time-window, and
vehicle-capacity constraints (`verify_shift_times`, `verify_time_windows`,
`verify_truck_capacity`). It was originally called only from Pipeline B
(`script.py`). Pipeline A (`main.py`), the only pipeline wired to the API,
produced no post-solve verification report - meaning the production path had
no automated check that its own solver output respected the constraints it
was supposed to satisfy.

## Decision

Call `run_verification()` from `main.py` after building and persisting the
solution, using the same `verifier.py` module already used by Pipeline B.
No verification logic is duplicated; both pipelines call the same functions.

This required aligning `vehicle_routes.py::build_solution` to output the `id`
key (previously `vehicle_id`) expected by `verifier.py`, and adjusting
`solve_pipeline` in `main.py` to write `output.json` twice: once before
verification (so `run_verification` can read it from disk) and once after,
with the `verification` field attached.

## Rationale

- `verifier.py` operates on the same solution shape (`vehicles` with `route`
  and `time`) produced by both pipelines - no pipeline-specific logic needed.
- Reusing it avoids writing a second verification implementation for Pipeline A,
  which would duplicate constraint-checking logic that already exists and is
  tested for Pipeline B.
- Closes a coverage gap: the production API path previously shipped solutions
  with no automated verification.

## Consequences

### Positive

- Production API responses now include a `verification` field, giving
  visibility into whether the returned solution respects shift, time-window,
  and capacity constraints.
- Verification logic is tested once and used by both pipelines, instead of
  being duplicated or left unimplemented for Pipeline A.

### Negative

- `run_verification` reads `input.json`/`output.json` from disk rather than
  operating on in-memory objects, requiring an extra file write in `main.py`
  before verification can run.
- The `id` key rename in `vehicle_routes.py::build_solution` is a breaking
  change to that function's output shape; any other caller relying on
  `vehicle_id` would need updating (none currently exist).

### Tradeoffs

- Passing the solution object directly to a refactored verifier (in-memory,
  no file I/O) was considered but rejected: it would require changing
  `verifier.py`'s signature and touch code used by Pipeline B, increasing the
  scope of this change beyond closing the coverage gap in Pipeline A.

## Links

- [QR-003: Critical module testability](../../quality-requirements.md#qr-003-critical-module-testability)
- [Sequence Diagram](../dynamic-view/sequence-diagram.puml)
- [Component Diagram](../static-view/component-diagram.puml)
- [ADR-010](ADR-010-independent-verifier.md)
