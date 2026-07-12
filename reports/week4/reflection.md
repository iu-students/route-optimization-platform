## Learning Points

- **Customer Feedback:**
    - Customer actively participates in refining requirements and suggests business-value improvements (optional orders, input validation).
    - Customer values progress visibility during long computations - "processing" without ETA causes frustration (led to #71).

- **Defining Quality Requirements:**
    - We translated requirements into measurable scenarios using ISO/IEC 25010 (QR-001: API response <2s for 99% requests; QR-003: 30% coverage threshold).
    - We linked each QR to an automated QRT that runs in CI.

- **Automating Quality Tests:**
    - We adopted pytest for integration tests verifying non-functional requirements (responsiveness, confidentiality).
    - We used pytest-cov with per-module thresholds to enforce testability in CI.

- **Configuring CI:**
    - We set up GitHub Actions pipelines with linting, unit tests, integration tests, coverage checks, and pip-audit.

- **UAT (User Acceptance Testing):**
    - Real-world usage revealed that users need progress feedback during long solver runs.
    - UAT-003 passed all validation checks but surfaced UX issue (no ETA/progress), which tests didn't catch.

- **Release & Sprint Review:**
    - The team prepared and published SemVer release v0.2.0, tagged on the protected main branch. The root CHANGELOG.md was updated with all user-visible changes, including PyVRP integration, API endpoints, and deployment setup. The release includes deployment instructions, a public IP access link for the running MVP, and a sanitized video demonstration showcasing the working system.
    - Customer feedback on Sprint Review was positive - the system works as expected, but he emphasized the need for progress indicators during long calculations, which we've already logged as #71 for the next sprint.

---

## Validated Assumptions

### Confirmed
- [Using PyVRP + CP-SAT in parallel]: We assumed that running two solver pipelines (PyVRP and CP-SAT) would increase solution reliability. Both passed all integration tests and verification checks on UAT. Confirmed.
- [API key authentication is sufficient]: We assumed that an API key would be enough to protect route data. QRT-002 passed all confidentiality tests - unauthorized requests are rejected. Confirmed.

### Rejected
- [Polling with "processing" status is acceptable]: We assumed that returning "processing" would be enough for users. On UAT-003, the customer reported that lack of progress feedback is frustrating. This assumption was rejected - we now need to implement ETA/progress indicator (#71).
- [All business rules were captured upfront]: We assumed the initial requirements were complete. However, customer feedback during the sprint led to new stories: optional orders (US-015) and manager statistics (US-016). These were not in the original scope. Partially rejected.

---

## Friction and Gaps

- **Unresolved Requirements / Backlog:**
    - [US-016 - Manager statistics]: The customer requested a story for viewing calculation metrics and objective function (#58). Not planned for this sprint - deferred to focus on algorithm improvements and CI/CD setup. Will be implemented in subsequent sprints.
    - [US-002, US-003, US-012, US-006]: Several "Should Have" and "Could Have" stories remain in backlog (fast startup, large client management, optimal routing for resource savings, one vehicle per client). Not started due to prioritization of core functionality.

- **Technical Risks & Quality Gaps:**
    - [Progress indicator missing]: No ETA/progress feedback for long-running solver calculations. This creates poor UX and was identified as a gap during UAT-003. Logged as #71 for next sprint.
    - [No UI layer] : The MVP is API-only. Frontend/UI testing was never implemented. The customer requested UI improvements during the review (progress indicators), but no frontend code exists yet. This is a gap to be addressed in future sprints.

- **Blocked Work / Process Friction:**
    - [No blockers reported] : There is no blocked work
    - [Code review process] : No data on whether PR reviews were slow or required many iterations.

- **Follow-up Questions & Uncertainties:**
    - [Customer priorities]: Should we prioritize US-016 (manager statistics) or UI/progress indicators in the next sprint?
    - [Two solvers]: Do we continue maintaining both PyVRP and CP-SAT in parallel, or should we drop one to reduce maintenance overhead?

---

## Planned Response

- **Backlog Adjustments:**
    - Move US-016 - Manager statistics into the next sprint as a top priority.
    - сCreate new PBI for progress indicator / ETA - implement a progress tracking endpoint and update /solution response with estimated completion time.

- **CI / Tests Improvements:**
    - Increase coverage threshold from 30% to 50% for critical modules (verifier.py, validator.py, tester.py) in the next sprint.
    - Add performance regression tests for /solve endpoint to ensure API responsiveness (<2s) under load.

- **UAT & Release Strategy:**
    - Update UAT scenarios to include progress feedback verification - UAT-004: "User receives ETA and progress updates during calculation."
    - Keep rollback strategy as is, deployment via GitHub Actions with tagged releases (v0.2.0, v0.3.0)

- **Process / Communication:**
    - Conduct internal knowledge-sharing session on PyVRP and CP-SAT performance tuning to better understand solver behavior and improve future optimizations.

---
