# Quality Requirements

This document defines the measurable quality requirements for the Route Optimization Platform.
Requirements are structured using the ISO/IEC 25010 quality model and follow the measurable scenario format.

## QR-001: API responsiveness

**ISO/IEC 25010 sub-characteristic:** Time behaviour

**Scenario:** When a dispatcher sends a `POST /solve` request or polls `GET /solution` under normal production-like load, the API shall return an HTTP response (202, 200, or appropriate 4xx/5xx) within 2 seconds for 99% of requests, regardless of whether the solver computation has completed.

**Why this matters:** The solver may run for minutes on large problems, but the user should never be left waiting for a TCP timeout or a hanging connection. Immediate acknowledgement (HTTP 202 Accepted) and instantly available status polling are essential for a responsive user experience. This requirement targets API responsiveness, not solver completion speed.

**Linked quality requirement tests:** [QRT-001](quality-requirement-tests.md#qrt-001-api-responsiveness)

**Related ADRs:** [ADR-002](architecture/adr/ADR-002-async-solve-with-polling.md)

---

## QR-002: Route data confidentiality

**ISO/IEC 25010 sub-characteristic:** Confidentiality

**Scenario:** When an unauthenticated client sends a request to any protected endpoint (`POST /solve`, `GET /solution`) without a valid `X-API-Key` header, the API shall reject the request with HTTP 401 Unauthorized and return no data about input, solution, or system state beyond an error message.

**Why this matters:** Route data (order locations, time windows, volumes) is commercially sensitive for logistics companies. Leaking this data to unauthorized parties could expose delivery patterns, customer lists, or operational capacity. The API key mechanism is the only authentication boundary and must be enforced consistently.

**Linked quality requirement tests:** [QRT-002](quality-requirement-tests.md#qrt-002-api-confidentiality)

**Related ADRs:** [ADR-004](architecture/adr/ADR-004-api-key-authentication.md)

---

## QR-003: Critical module testability

**ISO/IEC 25010 sub-characteristic:** Testability

**Scenario:** When a developer changes a critical product module under the standard CI environment, the module shall have automated unit tests that achieve at least 30% line coverage for that module.

**Why this matters:** Critical product logic must be directly verifiable so defects can be detected before merge. Without measurable coverage expectations, untested code paths can introduce regressions in core solver, validation, or verification logic.

**Linked quality requirement tests:** [QRT-003](quality-requirement-tests.md#qrt-003-critical-module-unit-coverage)

**Related ADRs:** [ADR-001](architecture/adr/ADR-001-dual-solver-pipelines.md), [ADR-003](architecture/adr/ADR-003-shared-verifier.md)

---

## QR-004: Solver completion time

**ISO/IEC 25010 sub-characteristic:** Time behaviour

**Scenario:** When a dispatcher submits a solve request via `POST /solve` with a realistic test instance (up to 20 orders), the solver shall complete computation and transition to `"status": "done"` within 15 minutes (900 seconds) under the standard CI environment.

**Why this matters:** If the solver runs indefinitely, the client never receives a solution and the API thread blocks. A 15-minute upper bound ensures the solver terminates within a predictable window, enabling timeout-based error handling and preventing resource exhaustion on the production server.

**Linked quality requirement tests:** [QRT-004](quality-requirement-tests.md#qrt-004-solver-completion-time)

**Related ADRs:** [ADR-002](architecture/adr/ADR-002-async-solve-with-polling.md), [ADR-005](architecture/adr/ADR-005-solver-time-limits.md)

---

## QR-005: Hosted documentation availability

**ISO/IEC 25010 sub-characteristic:** Availability

**Scenario:** When a reviewer or team member opens the hosted documentation site URL (`https://iu-students.github.io/route-optimization-platform/`), the site shall return HTTP 200 and serve the `index.html` entry point within 10 seconds, 99% of the time during standard business hours.

**Why this matters:** Assignment 5 requires hosted documentation as a maintained asset. If the site is unreachable, reviewers cannot inspect architecture, process, quality, or testing documentation. A measurable availability target ensures the documentation is reliably publishable and the team notices when it breaks.

**Linked quality requirement tests:** [QRT-005](quality-requirement-tests.md#qrt-005-hosted-documentation-availability)

**Related ADRs:** [ADR-006](architecture/adr/ADR-006-hosted-documentation.md)

---

## QR-006: Solver optimality against baseline

**ISO/IEC 25010 sub-characteristic:** Time behaviour / Efficiency

**Scenario:** When a dispatcher submits a solve request on any of the 10 standard test instances (`instances/i1.json`–`i10.json`), the solver shall produce a solution whose `total_cost` is lower than the baseline score defined in `instances/baseline_scores.json` for at least 7 out of 10 instances.

**Why this matters:** The purpose of the platform is to produce cost-effective routes. If the solver cannot beat the baseline on the majority of test instances, it does not provide value over the existing manual or heuristic planning method. A 70% pass rate ensures meaningful improvement while acknowledging that some instances are inherently harder.

**Linked quality requirement tests:** [QRT-006](quality-requirement-tests.md#qrt-006-solver-optimality-against-baseline)

**Related ADRs:** [ADR-001](architecture/adr/ADR-001-dual-solver-pipelines.md), [ADR-005](architecture/adr/ADR-005-solver-time-limits.md)
