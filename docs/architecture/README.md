# Architecture

This document is the canonical index for the maintained architecture of the Route Optimization Platform. It covers three views - static, dynamic, and deployment - and links the Architecture Decision Records (ADRs) that justify key structural choices.

As of MVPv3, the platform runs a **single production solver pipeline** in `api/MVPv3/`:
- **CP-SAT pipeline** - `CP-SAT/main.py`, `CP-SAT/vehicle_routes.py`, `CP-SAT/loader_routes.py`, `CP-SAT/common_functions.py`. Wired to the Flask API (`Web/app.py`). `vehicle_routes.py` builds a candidate route pool via Clarke-Wright savings and randomized insertion heuristics (optionally seeded once by a one-time OR-Tools routing run, reused across all attempts), then OR-Tools CP-SAT selects the optimal subset by set-partitioning. Selected routes then go through `consolidate_routes`, `reduce_vehicles_by_merge`, `inter_route_local_search`, and `merge_multi_trip_routes` before loader assignment. `main.py` runs this as a **multi-start** loop - independent full solve attempts, each with a fresh random pool, keeping whichever attempt has the lowest real `total_cost` - followed by a **Large Neighborhood Search (LNS) polish** phase that perturbs and re-improves the best solution with whatever time budget remains. A feedback iteration drops optional orders that are unprofitable on *both* the vehicle side (exact marginal fuel/salary savings from removing the order) and the loader side, then re-selects from the already-built pool for the reduced scenario. See [ADR-009](adr/ADR-009-single-solver-pipeline.md), [ADR-005](adr/ADR-005-solver-time-limits.md), and [ADR-008](adr/ADR-008-multistart-lns-search.md).
- A second pipeline based on the PyVRP library (`Pipeline B`) existed through MVPv2.2 for offline baseline comparison but has been **removed** as of MVPv3 - see [ADR-009](adr/ADR-009-single-solver-pipeline.md) for why.

`Shared/verifier.py` runs after the CP-SAT pipeline produces a solution (`run_verification()`). `Shared/models.py` defines the data classes the pipeline parses into. `Shared/history.py` wraps a SQLite database (`data/history.db`) that records one row per `/solve` call - see [ADR-007](adr/ADR-007-sqlite-calculation-history.md). `Web/validator.py` has two independent roles: the `validate_input`/`ValidationError` functions used by the Flask API for request-schema validation, and (further down in the same file) a standalone `Validator` class with its own CLI (`python validator.py --dir ...`) for validating a solution file against routing constraints and comparing it to a baseline with an Excel report - unrelated to the Flask app and not code-shared with `Shared/verifier.py` or `tester.py`.

Diagram sources and rendered views live in [static-view/](static-view/), [dynamic-view/](dynamic-view/), and [deployment-view/](deployment-view/).

## Static View

![Component Diagram](static-view/component-diagram.svg)

Source: [component-diagram.puml](static-view/component-diagram.puml)

**What the diagram shows:** the system's internal components grouped by responsibility (API layer, CP-SAT pipeline, shared models/verifier/history/storage, offline comparison tool), and the two actors that trigger work (API Client via HTTP, Developer via CLI for the offline tools).

**Coupling and cohesion:** the CP-SAT pipeline is internally cohesive - `vehicle_routes.py` and `loader_routes.py` share `common_functions.py`. `common_functions.py` and `Shared/models.py` are the only cross-cutting dependencies for route generation. `Shared/history.py` is a cross-cutting dependency for the API layer only.

**Maintainability implications:** with Pipeline B removed, route-generation logic now lives in exactly one place, eliminating the dual-implementation maintenance cost described in [ADR-009](adr/ADR-009-single-solver-pipeline.md). The tradeoff is the loss of an independently-implemented baseline for solution-quality comparison; offline comparison now relies on static pre-computed baseline files (`instances/output_{task}.json`) rather than a live second solver. The Validator-before-Orchestrator structure in the API layer keeps invalid input from reaching solver code, limiting the blast radius of malformed requests. `Web/validator.py`'s second, unrelated `Validator` class (solution-vs-baseline checking with Excel export) duplicates some constraint-checking logic already present in `Shared/verifier.py`, since the two were not written to share code.

**Related decisions:** the single-pipeline structure is formalized in [ADR-009](adr/ADR-009-single-solver-pipeline.md); the verification step is formalized in [ADR-010](adr/ADR-010-independent-verifier.md); the multi-start/LNS search strategy is formalized in [ADR-008](adr/ADR-008-multistart-lns-search.md); the calculation history is formalized in [ADR-007](adr/ADR-007-sqlite-calculation-history.md).

**Quality requirements supported/constrained:** the Validator-before-Orchestrator structure directly supports [QR-002](../quality-requirements.md#qr-002-route-data-confidentiality) by rejecting invalid/malicious input before it is persisted or processed. Removing Pipeline B improves QR-003 (testability) by halving the number of independent route-generation code paths needing coverage, at the cost of losing an independent implementation to cross-check solution quality against.

## Dynamic View

![Sequence Diagram](dynamic-view/sequence-diagram.svg)

Source: [sequence-diagram.puml](dynamic-view/sequence-diagram.puml)

The diagram keeps message labels short and omits explicit activate/deactivate bars on solver-internal calls to stay well under the 4096px single-dimension limit some renderers impose. `POST /validate` and `GET /metrics` exist in the API (see the Static View and [ADR-004](adr/ADR-004-api-key-authentication.md)) but are intentionally left out of this diagram - `/validate` is a synchronous, standalone call to the same `validate_input()` shown inline within `POST /solve`, and `/metrics` follows the exact same computing/done/error/idle polling shape as `GET /solution` shown here, just returning a `statistics` projection instead of the full solution.

**Scenario:** a client submits a routing problem (`POST /solve`), the API validates the input, records a new `calculation_id` in the history database, and acknowledges immediately; solving runs asynchronously in a background thread that repeatedly runs full solve attempts (multi-start), then polishes the best one (LNS), reporting its current stage throughout. The client polls `GET /solution` until the result is ready. `GET /history` / `GET /history/{calculation_id}` expose past calculations independently of the live solve in progress.

**Why this scenario matters:** it is the only path by which the product delivers value to a customer. It also encodes the API's core non-functional contract - the client is never blocked on solver runtime, which can range from seconds up to the pipeline's overall time budget.

**What it helps reason about:** the integration boundary between the stateless HTTP layer and the stateful in-process solver thread (`solver_state`, protected by `solver_lock`); the failure surface (validation errors returned synchronously, solver errors surfaced only on the next poll, but also durably recorded as `status="error"` in `calculation_history`); and the async design's direct link to [QR-001](../quality-requirements.md#qr-001-api-responsiveness) - HTTP response time is decoupled from solver completion time.

**Related decisions:** the asynchronous `/solve` design is formalized in [ADR-002](adr/ADR-002-async-solve-with-polling.md); the verification step in [ADR-010](adr/ADR-010-independent-verifier.md); the multi-start/LNS loop in [ADR-008](adr/ADR-008-multistart-lns-search.md); the calculation-history persistence in [ADR-007](adr/ADR-007-sqlite-calculation-history.md).

**What the diagram shows:** message flow from `POST /solve` through validation, history-record creation, thread spawn, and pipeline execution - parsing, then a multi-start loop (each attempt: solving vehicles, consolidating/merging/local-search on vehicles, solving loaders, an optional feedback iteration on unprofitable optional orders) keeping the best attempt, then an LNS polish loop over the remaining time budget, then persisted output, verification, and a history record updated to `success`/`error`. It also shows the polling exchange on `GET /solution` (`computing`/`stage`, `done`, `error`, `idle` states) and the `GET /history` / `GET /history/{calculation_id}` exchanges that read directly from the database rather than from `solver_state`.

## Deployment View

![Deployment Diagram](deployment-view/deployment-diagram.svg)

Source: [deployment-diagram.puml](deployment-view/deployment-diagram.puml)

**What the diagram shows:** a single Docker container (`python:3.12-slim`) running the Flask API process (`Web/app.py`) on port 5003, with the solver pipeline (`CP-SAT/main.py` + `CP-SAT/vehicle_routes.py` + `CP-SAT/loader_routes.py`) executing in-process (background thread, not a separate service), a SQLite database file (`data/history.db`) holding the `calculation_history` table, and a `data/` directory holding the live `input.json`/`output.json` scratch files plus per-calculation snapshots under `data/inputs/{calculation_id}.json` and `data/outputs/{calculation_id}.json`.

**Why this deployment model was chosen:** the workload is single-tenant and low-concurrency (one dispatcher, sequential solves via the `solver_lock` guard), so a single-process, single-container deployment avoids the operational cost of a multi-service architecture without sacrificing the current use case. SQLite was chosen over a separate database service for the same reason.

**How it supports/constrains the product:** it supports fast, simple deployment (`docker build` + `docker run`). It constrains horizontal scaling - `solver_state` is in-process memory, so a second replica would not share solve status with the first, and the `409 Already solving` guard only protects a single instance. SQLite's single-writer model reinforces the same constraint.

**Operational considerations:** `data/` is `COPY`'d into the image at build time. `docker-compose.yml` also mounts `./data:/MVPv3/data` as a volume, but the Flask process actually resolves `DATA_DIR` to `/ROP/data` (matching the Dockerfile's `WORKDIR /ROP`) - the mounted path and the path the process writes to do not match, so `history.db`, `output.json`, and the per-calculation snapshots do **not** currently persist across container rebuilds; this mismatch pre-dates MVPv3 and is worth fixing independently. There is no reverse proxy or TLS termination in front of the Flask process; `X-API-Key` is currently the only access control, transmitted over whatever transport fronts port 5003. `MVPv0`, `MVPv1`, `MVPv1.2`, `MVPv2`, and `MVPv2.2` still run as separate legacy containers alongside MVPv3 in `docker-compose.yml`, each on its own port; this document covers MVPv3 only.

## Architecture Decision Records

See [docs/architecture/adr/](adr/) for the full ADR set.

| ADR | Decision | Related QR |
|---|---|---|
| [ADR-009](adr/ADR-009-single-solver-pipeline.md) | Consolidate to a single CP-SAT solver pipeline, removing the PyVRP-based Pipeline B | QR-003 |
| ~~ADR-001 (declined)~~ | ~~[Maintain two independent solver pipelines](adr/ADR-001-dual-solver-pipelines.md)~~ - kept for historical context only | QR-003 |
| [ADR-002](adr/ADR-002-async-solve-with-polling.md) | Run `/solve` asynchronously via background thread with `/solution` polling instead of a synchronous request | QR-001, QR-004 |
| ~~[ADR-003](adr/ADR-003-shared-verifier.md)~~ | ~~Keep `verifier.py` as an independent module invoked after solving, rather than inlined into the orchestrator~~ - kept for historical context only | QR-003 |
| [ADR-004](adr/ADR-004-api-key-authentication.md) | Enforce access control via a shared API key checked at every protected endpoint | QR-002 |
| [ADR-005](adr/ADR-005-solver-time-limits.md) | Bound total solver runtime with a single overall deadline, distributed across pipeline stages and scaled by instance size | QR-004 |
| [ADR-006](adr/ADR-006-hosted-documentation.md) | Publish maintained documentation via GitHub Pages from `docs/` | QR-005 |
| [ADR-007](adr/ADR-007-sqlite-calculation-history.md) | Persist calculation metadata and input/output snapshots in an embedded SQLite database | QR-002, QR-004 |
| [ADR-008](adr/ADR-008-multistart-lns-search.md) | Use multi-start with best-of selection plus LNS polishing instead of a single solve attempt | QR-004 |
| [ADR-010](adr/ADR-010-independent-verifier.md) | Keep `verifier.py` as an independent module invoked after solving, rather than inlined into the orchestrator | QR-003 |
