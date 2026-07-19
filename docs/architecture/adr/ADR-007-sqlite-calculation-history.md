# ADR-007: Persist Calculation Metadata and Snapshots in an Embedded SQLite Database

**Status:** Accepted

**Quality requirements addressed:** QR-002, QR-004

## Context

The API keeps only the *current* calculation's input/output as `data/input.json`/`data/output.json`, overwritten on every `POST /solve`. There was no way for a client to list past calculations, inspect a previous run's cost breakdown, or distinguish a calculation that failed from one that never ran. The team needed a way to durably record calculation metadata (when it ran, how long it took, its objective cost, whether it succeeded) and to expose it via `GET /history` and `GET /history/{calculation_id}` endpoints, without introducing a separate database service into a single-container deployment.

Options considered:
- An embedded SQLite database file (`data/history.db`) alongside the existing JSON files
- A separate database service (PostgreSQL/MySQL) added to `docker-compose.yml`
- Append-only JSON Lines log file, parsed on each `GET /history` request
- No persistence - keep only the current calculation in memory (status quo)

## Decision

`Shared/history.py`, a thin wrapper around Python's built-in `sqlite3` module, is backed by a single file at `data/history.db`. On API startup, `init_db()` creates the `calculation_history` table if it does not exist and ensures `data/inputs/` and `data/outputs/` directories exist. `POST /solve` calls `start_calculation()` to insert a `processing` row and obtain a `calculation_id`, and writes the input JSON to `data/inputs/{calculation_id}.json`. On completion, `run_solve()` calls `finish_success()` (writing `data/outputs/{calculation_id}.json` and updating `execution_time`, `objective_function_cost`, `status="success"`) or `finish_error()` (`status="error"`, with the error message written to the output file). `GET /history` calls `get_all()` for summary metadata; `GET /history/{calculation_id}` calls `get_by_id()`, which also reads back the stored input/output JSON files.

The `calculation_history` schema:

```sql
CREATE TABLE calculation_history (
    calculation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    execution_time REAL,
    objective_function_cost REAL,
    status TEXT NOT NULL,
    input_json_path TEXT NOT NULL,
    output_json_path TEXT
)
```

## Rationale

- SQLite needs no additional container, network hop, or credentials - consistent with the existing single-process, single-container deployment model (see the [Deployment View](../deployment-view/deployment-diagram.puml)).
- `sqlite3` is part of the Python standard library, so no new dependency was added to `requirements.txt`.
- Storing `input_json_path`/`output_json_path` rather than the JSON blobs themselves keeps the database small and reuses the existing pattern of JSON files on disk, while giving each calculation its own permanent snapshot (unlike the single, overwritten `data/input.json`/`data/output.json` pair used for the *live* in-progress calculation).
- A JSON Lines log was rejected: it would require a full-file scan for every `GET /history` call and offers no indexed lookup for `GET /history/{calculation_id}`.

## Consequences

### Positive

- Clients can list and inspect past calculations (`GET /history`, `GET /history/{calculation_id}`) instead of only ever seeing the most recent one.
- A calculation's outcome (`success`/`error`) and cost are durably recorded even after the API process restarts, as long as `data/history.db` itself persists.
- Each calculation's exact input and output are preserved as immutable per-ID snapshots, independent of whatever the next `POST /solve` overwrites in `data/input.json`/`data/output.json`.

### Negative

- SQLite's single-writer model means a second API replica writing to the same `history.db` file risks lock contention - this reinforces the existing single-instance constraint noted in [ADR-002](ADR-002-async-solve-with-polling.md), it does not introduce a new one.
- A `calculation_history` row is inserted with status `processing` before the solver thread starts, but nothing updates that row if the process crashes mid-solve - such a calculation remains stuck at `processing` in `GET /history` indefinitely.
- `data/inputs/` and `data/outputs/` grow unbounded - there is no retention policy or cleanup for old per-calculation snapshots.
- As noted in the Deployment View, the current `docker-compose.yml` volume mount does not actually match the path the Flask process writes to, so in practice `history.db` and the snapshot directories do not yet survive a container rebuild.

### Tradeoffs

- A full external database service was rejected as disproportionate to a single-tenant, low-concurrency deployment; it would add operational cost (a second container, connection configuration, credential management) without a corresponding need for concurrent multi-writer access.

## Links

- [QR-002: Route data confidentiality](../../quality-requirements.md#qr-002-route-data-confidentiality)
- [QR-004: Solver completion time](../../quality-requirements.md#qr-004-solver-completion-time)
- [Component Diagram](../static-view/component-diagram.puml)
- [Sequence Diagram](../dynamic-view/sequence-diagram.puml)
- [Deployment Diagram](../deployment-view/deployment-diagram.puml)
- [ADR-002: Asynchronous /solve with background thread and polling](ADR-002-async-solve-with-polling.md)
