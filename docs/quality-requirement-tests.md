# Quality Requirement Tests

This document defines the automated quality requirement tests (QRTs) that directly verify the measurable quality requirement scenarios defined in [quality-requirements.md](quality-requirements.md).

## QRT-001: API responsiveness

**Linked quality requirement:** [QR-001](quality-requirements.md#qr-001-api-responsiveness)

**Verification method:** Automated integration test using Flask test client with timing measurement.

**Test data, setup, or environment:** Flask application (`api/MVPv1/app.py`) configured in testing mode with a temporary data directory and a known API key (`test-api-key-123`). Each test simulates a realistic request scenario (health check, solve submission, solution polling) and measures wall-clock response time.

**Automated command or CI check:**

```bash
python -m pytest tests/test_qrt_001_api_responsiveness.py -v
```

**Expected measurable result:** Each endpoint (`GET /health`, `POST /solve`, `GET /solution`) returns an HTTP response within 2.0 seconds for 100% of test requests.

**Evidence link:** `tests/test_qrt_001_api_responsiveness.py`

---

## QRT-002: API confidentiality

**Linked quality requirement:** [QR-002](quality-requirements.md#qr-002-route-data-confidentiality)

**Verification method:** Automated integration test using Flask test client.

**Test data, setup, or environment:** Flask application (`api/MVPv1/app.py`) configured in testing mode with a temporary data directory and a known API key (`test-api-key-123`). Tests exercise all protected endpoints with missing, invalid, and valid credentials.

**Automated command or CI check:**

```bash
python -m pytest tests/test_qrt_002_api_confidentiality.py -v
```

**Expected measurable result:** Every protected endpoint (`POST /solve`, `GET /solution`) returns HTTP 401 when called without a valid `X-API-Key` header. The `/health` endpoint remains accessible without authentication. No error response leaks the API key value.

**Evidence link:** `tests/test_qrt_002_api_confidentiality.py`

---

## QRT-003: Critical module unit coverage

**Linked quality requirement:** [QR-003](quality-requirements.md#qr-003-critical-module-testability)

**Verification method:** Automated CI coverage check using `pytest-cov` with per-module threshold enforcement.

**Test data, setup, or environment:** Standard CI environment for pull requests and protected default-branch updates. Coverage is measured against the critical modules listed in `docs/testing.md`.

**Automated command or CI check:**

```bash
python -m pytest tests/ --cov-config=coveragerc --cov --cov-report=term-missing
```

**Expected measurable result:** Every critical module listed in `docs/testing.md` has at least 30% line coverage. The CI coverage job fails if any critical module falls below the threshold.

**Evidence link:** `tests/test_qrt_003_critical_module_coverage.py`

---

---

## QRT-004: Solver completion time

**Linked quality requirement:** [QR-004](quality-requirements.md#qr-004-solver-completion-time)

**Verification method:** Automated integration test that runs the CP-SAT solver on a small test instance with a 15-minute wall-clock timeout.

**Test data, setup, or environment:** Standard CI environment. Uses a realistic test instance (5 orders, standard weights) loaded from `api/data/input.json`. The solver runs in-process via `api/MVPv2/script.py`.

**Automated command or CI check:**

```bash
python -m pytest tests/test_qrt_004_solver_completion_time.py -v --timeout=950
```

**Expected measurable result:** The solver completes within 900 seconds and the output JSON contains a valid solution with status `done`.

**Evidence link:** `tests/test_qrt_004_solver_completion_time.py`

---

## QRT-005: Hosted documentation availability

**Linked quality requirement:** [QR-005](quality-requirements.md#qr-005-hosted-documentation-availability)

**Verification method:** Automated HTTP health check against the hosted documentation site.

**Test data, setup, or environment:** CI environment with network access. Checks the GitHub Pages URL directly.

**Automated command or CI check:**

```bash
python -m pytest tests/test_qrt_005_docs_availability.py -v
```

**Expected measurable result:** The URL `https://iu-students.github.io/route-optimization-platform/` returns HTTP 200 and the response body contains `Route Optimization Platform`.

**Evidence link:** `tests/test_qrt_005_docs_availability.py`

---

## QRT-006: Solver optimality against baseline

**Linked quality requirement:** [QR-006](quality-requirements.md#qr-006-solver-optimality-against-baseline)

**Verification method:** Standalone test script that runs the CP-SAT solver pipeline (`api/MVPv2.2/CP-SAT/main.py`) on all 10 test instances, computes each output's `total_cost` using `api/MVPv2.2/tester.py` `calc_cost()`, and compares against the pre-computed baseline scores (also derived from `instances/baseline_iN.json` via `calc_cost()`).

**Test data, setup, or environment:** Local development environment with the standard dependencies installed. Requires `instances/i1.json`–`i10.json` (test inputs), `instances/baseline_i1.json`–`baseline_i10.json` (baseline solutions), and `instances/baseline_scores.json` (pre-computed baseline scores).

**Automated command or CI check:** Not run in CI (runs the full solver pipeline on 10 instances, which exceeds normal CI time budgets). Execute manually:

```bash
python -m pytest tests/test_qrt_006_solver_optimality.py -v
```

**Expected measurable result:** The solver produces solutions whose `calc_cost()` `total_cost` is lower than the baseline on at least 7 out of 10 instances.

**Evidence link:** `tests/test_qrt_006_solver_optimality.py`

---

## Test Execution

Run all automated quality requirement tests together:

```bash
python -m pytest tests/test_qrt_001_api_responsiveness.py tests/test_qrt_002_api_confidentiality.py tests/test_qrt_003_critical_module_coverage.py tests/test_qrt_004_solver_completion_time.py tests/test_qrt_005_docs_availability.py -v
```

QRT-004 (solver completion time) may require a longer timeout:

```bash
python -m pytest tests/test_qrt_004_solver_completion_time.py -v --timeout=950
```

QRT-005 (hosted docs availability) requires network access:

```bash
python -m pytest tests/test_qrt_005_docs_availability.py -v
```

QRT-006 (solver optimality) runs outside CI:

```bash
python -m pytest tests/test_qrt_006_solver_optimality.py -v
```

Or run the entire test suite:

```bash
python -m pytest tests/ -v
```
