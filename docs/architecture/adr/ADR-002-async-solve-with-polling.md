# ADR-002: Asynchronous /solve with Background Thread and Polling

**Status:** Accepted

**Quality requirements addressed:** QR-001

## Context

Solver computation for large problems can take minutes (`vehicle_routes.py`
and `loader_routes.py` run CP-SAT with time limits up to 240s each, plus a
feedback iteration). A synchronous HTTP request held open for the full
duration risks client-side timeouts and holds the connection resource for an
unpredictable time. The team needed the API to stay responsive regardless of
solver runtime.

## Decision

`POST /solve` validates the request, persists the input to `input.json`,
starts a background `threading.Thread` running `solve_pipeline`, and
immediately returns `202 Accepted`. Solve progress and results are retrieved
separately via `GET /solution`, which reports `computing`, `done`, or `error`
based on in-memory `solver_state`, guarded by `solver_lock`.

## Rationale

- Flask's synchronous request model works naturally with Python's `threading`
  module — no need to introduce an async framework or a task queue for a
  3-endpoint API.
- `solver_lock` + `solver_state` is enough to prevent concurrent solves and to
  expose solve status without a database.
- Polling is simpler to implement and consume than WebSockets or webhooks,
  matching the current single-client, low-concurrency usage.

## Consequences

### Positive

- API response time is decoupled from solver runtime — the client is never
  blocked waiting for computation.
- `POST /solve` reliably returns within QR-001's 2-second target regardless of
  problem size.

### Negative

- `solver_state` is process-local memory: a second API replica would not share
  solve status with the first, and the `409 Already solving` guard only
  protects a single instance. This constrains horizontal scaling.
- The client must poll rather than receive a push notification; no webhook or
  WebSocket mechanism exists.
- If the process crashes mid-solve, `solver_state` is lost with no persisted
  record of an in-progress computation.

### Tradeoffs

- A task queue (e.g., Celery + Redis) was not adopted: it would solve the
  multi-replica limitation but adds infrastructure the current single-container
  deployment does not need.

## Links

- [QR-001: API responsiveness](../../quality-requirements.md#qr-001-api-responsiveness)
- [Sequence Diagram](../dynamic-view/sequence-diagram.puml)
- [Deployment Diagram](../deployment-view/deployment-diagram.puml)