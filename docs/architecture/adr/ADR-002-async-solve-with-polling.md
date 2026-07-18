# ADR-002: Asynchronous /solve with Background Thread and Polling

**Status:** Accepted

**Quality requirements addressed:** QR-001, QR-004

## Context

Solver computation can take minutes: `CP-SAT/main.py` runs a multi-start loop of independent full solve attempts (pool generation, CP-SAT selection, consolidation, local search, loader assignment, an optional feedback iteration) followed by an LNS polishing phase, all bounded by a shared overall deadline (see [ADR-005](ADR-005-solver-time-limits.md) and [ADR-008](ADR-008-multistart-lns-search.md)). A synchronous HTTP request held open for the full duration risks client-side timeouts and holds the connection resource for an unpredictable time. The team needed the API to stay responsive regardless of solver runtime.

## Decision

`POST /solve` validates the request, records a new `calculation_history` row (status `processing`) to obtain a `calculation_id`, persists the input to `input.json` (and a per-calculation snapshot under `data/inputs/`), starts a background `threading.Thread` running `solve_pipeline`, and immediately returns `202 Accepted` with the `calculation_id`. Solve progress and results are retrieved separately via `GET /solution`, which reports `computing` (with the current stage), `done`, or `error` based on in-memory `solver_state`, guarded by `solver_lock`.

## Rationale

- Flask's synchronous request model works naturally with Python's `threading` module - no need to introduce an async framework or a task queue for a small API.
- `solver_lock` + `solver_state` is enough to prevent concurrent solves and to expose *live* solve status without querying a database on every poll. Persisted history (see [ADR-007](ADR-007-sqlite-calculation-history.md)) is a separate, coarser-grained concern - it records that a calculation started and how it ended, not its live in-progress stage.
- Polling is simpler to implement and consume than WebSockets or webhooks, matching the current single-client, low-concurrency usage.

## Consequences

### Positive

- API response time is decoupled from solver runtime - the client is never blocked waiting for computation.
- `POST /solve` reliably returns within QR-001's target regardless of problem size.

### Negative

- `solver_state` is process-local memory: a second API replica would not share solve status with the first, and the `409 Already solving` guard only protects a single instance. This constrains horizontal scaling.
- The client must poll rather than receive a push notification; no webhook or WebSocket mechanism exists.
- If the process crashes mid-solve, live `solver_state` (including the current stage) is lost. A `calculation_history` row for that calculation does persist with status `processing`, but nothing updates it to `error` after a crash - a client checking `GET /history/{calculation_id}` after a crash sees a calculation stuck at `processing` indefinitely, not an accurate error state.

### Tradeoffs

- A task queue (e.g., Celery + Redis) was not adopted: it would solve the multi-replica limitation but adds infrastructure the current single-container deployment does not need.

## Links

- [QR-001: API responsiveness](../../quality-requirements.md#qr-001-api-responsiveness)
- [QR-004: Solver completion time](../../quality-requirements.md#qr-004-solver-completion-time)
- [Sequence Diagram](../dynamic-view/sequence-diagram.puml)
- [Deployment Diagram](../deployment-view/deployment-diagram.puml)
- [ADR-007: SQLite calculation history](ADR-007-sqlite-calculation-history.md)
