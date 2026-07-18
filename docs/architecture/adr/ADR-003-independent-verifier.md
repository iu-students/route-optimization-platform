# ADR-003: Keep Verification as an Independent Module

**Status:** Accepted (rationale updated for MVPv3; originally framed around sharing between two pipelines)

**Quality requirements addressed:** QR-003

## Context

`Shared/verifier.py` checks a produced solution against shift-time, time-window, and vehicle-capacity constraints (`verify_shift_times`, `verify_time_windows`, `verify_truck_capacity`). Through MVPv2.2, this ADR's rationale was that the module was shared between Pipeline A and Pipeline B, avoiding duplicated verification logic across two solver implementations. As of MVPv3 (see [ADR-001](ADR-001-single-solver-pipeline.md)), Pipeline B has been removed, so `Shared/verifier.py` now has exactly one caller: `CP-SAT/main.py`'s `solve_pipeline()`.

Separately, `Web/validator.py` has grown a second, unrelated `Validator` class with its own CLI, which independently re-implements similar constraint checks (route sequencing, capacity, time windows) plus baseline comparison and Excel export - without importing or reusing `Shared/verifier.py`.

## Decision

Keep `Shared/verifier.py` as a standalone module invoked via `run_verification()` from `CP-SAT/main.py` after building and persisting the solution, rather than inlining verification logic directly into the orchestrator. Do not consolidate it with `Web/validator.py`'s separate `Validator` class in this version.

## Rationale

- Even with a single caller, keeping verification in its own module preserves single-responsibility separation and testability: `verifier.py` can be unit-tested against solution JSON fixtures without needing to run the solver at all.
- `run_verification` operates on the same solution shape (`vehicles` with `route` and `time`) that the CP-SAT pipeline produces, so no pipeline-specific branching is needed inside it.
- Consolidating `Shared/verifier.py` and `Web/validator.py`'s `Validator` class was considered but deferred: they currently serve different purposes (the former runs inline as part of every `/solve`; the latter is an offline CLI tool with Excel reporting) and unifying them was out of scope for the CP-SAT optimization work this version focused on.

## Consequences

### Positive

- Production API responses continue to include a `verification` field, giving visibility into whether the returned solution respects shift, time-window, and capacity constraints.
- Verification logic remains independently testable and does not need to change shape just because Pipeline B was removed.

### Negative

- The original justification for this ADR ("shared between two pipelines") no longer applies now that there is only one pipeline; the module is retained for separation-of-concerns reasons instead. A future reader should not be confused into thinking Pipeline B still exists because this ADR mentions sharing.
- `Web/validator.py`'s separate `Validator` class duplicates constraint-checking logic that already exists in `Shared/verifier.py`, just implemented independently (pandas-based, with its own violation-counting and Excel export) - a change to a constraint's definition now has to be considered in two places if both are meant to agree.
- `run_verification` still reads `input.json`/`output.json` from disk rather than operating on in-memory objects, requiring an extra file write in `main.py` before verification can run.

### Tradeoffs

- Merging `Web/validator.py`'s `Validator` class into `Shared/verifier.py` (or vice versa) was considered but rejected for this version: it would require reconciling two different constraint-checking implementations and their respective consumers (live API vs. offline Excel reporting), a larger refactor than the CP-SAT optimization work this version targeted.

## Links

- [QR-003: Critical module testability](../../quality-requirements.md#qr-003-critical-module-testability)
- [Sequence Diagram](../dynamic-view/sequence-diagram.puml)
- [Component Diagram](../static-view/component-diagram.puml)
- [ADR-001: Single CP-SAT solver pipeline](ADR-001-single-solver-pipeline.md)
