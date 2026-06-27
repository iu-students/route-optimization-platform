# Quality Requirements

This document defines the measurable quality requirements for the Route Optimization Platform.
Requirements are structured using the ISO/IEC 25010 quality model and follow the measurable scenario format.

## QR-001: Отзывчивость API при отправке запроса на оптимизацию

**ISO/IEC 25010 sub-characteristic:** Time behaviour (временная эффективность)

**Scenario:** When a dispatcher sends a `POST /solve` request or polls `GET /solution` under normal production-like load, the API shall return an HTTP response (202, 200, or appropriate 4xx/5xx) within 2 seconds for 99% of requests, regardless of whether the solver computation has completed.

**Why this matters:** The solver may run for minutes on large problems, but the user should never be left waiting for a TCP timeout or a hanging connection. Immediate acknowledgement (HTTP 202 Accepted) and instantly available status polling are essential for a responsive user experience. This requirement targets API responsiveness, not solver completion speed.

**Linked quality requirement tests:** [QRT-001](quality-requirement-tests.md#qrt-001-api-responsiveness)

---

## QR-002: Конфиденциальность данных маршрутов

**ISO/IEC 25010 sub-characteristic:** Confidentiality (конфиденциальность)

**Scenario:** When an unauthenticated client sends a request to any protected endpoint (`POST /solve`, `GET /solution`) without a valid `X-API-Key` header, the API shall reject the request with HTTP 401 Unauthorized and return no data about input, solution, or system state beyond an error message.

**Why this matters:** Route data (order locations, time windows, volumes) is commercially sensitive for logistics companies. Leaking this data to unauthorized parties could expose delivery patterns, customer lists, or operational capacity. The API key mechanism is the only authentication boundary and must be enforced consistently.

**Linked quality requirement tests:** [QRT-002](quality-requirement-tests.md#qrt-002-api-confidentiality)

---

## QR-003: Отказоустойчивость при некорректном вводе

**ISO/IEC 25010 sub-characteristic:** Fault tolerance (отказоустойчивость)

**Scenario:** When a client sends a request with missing, invalid, or out-of-range fields to the `POST /solve` endpoint under any load condition, the API shall reject the request with an appropriate 4xx HTTP status code and a descriptive error message without crashing the application or corrupting the solver state.

**Why this matters:** The platform is consumed by external systems and users who may send malformed data. Unhandled invalid input can crash the solver, corrupt the input file, or leave the system in an inconsistent state. Graceful validation with clear error messages protects system integrity and helps API consumers fix their requests quickly.

**Linked quality requirement tests:** [QRT-003](quality-requirement-tests.md#qrt-003-fault-tolerance)
