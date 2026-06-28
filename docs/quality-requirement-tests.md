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

## Test Execution

Run all automated quality requirement tests together:

```bash
python -m pytest tests/test_qrt_001_api_responsiveness.py tests/test_qrt_002_api_confidentiality.py tests/test_qrt_003_critical_module_coverage.py -v
```

Or run the entire test suite:

```bash
python -m pytest tests/ -v
```
