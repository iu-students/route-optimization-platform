# AGENTS.md

Route Optimization Platform - CVRPTW solver API (vehicle + loader routing). There are six MVP versions in `api/` (`MVPv0`, `MVPv1`, `MVPv1.2`, `MVPv2`, `MVPv2.2`, `MVPv3`). `MVPv3` is the version we use now. See [README.md](README.md) for the product description, the team, and full run instructions. See [CONTRIBUTING.md](CONTRIBUTING.md) for the human contribution guide (branching, PR, review).

## Setup

Run the full stack via Docker Compose:
```bash
cp .env.example .env
docker compose up --build -d
curl http://localhost:5003/health
```

If you want to test/lint without Docker, install the same packages CI uses (there is no separate dev-requirements file; CI installs them directly):
```bash
pip install flask flask-cors numpy ortools openpyxl pytest pytest-cov coverage flake8 bandit
```

## Test

All tests are for MVPv3 (CP-SAT solver). In `conftest.py`, `TEST_TARGET` is `v3` by default.

Full suite (matches `ci-tests.yml`):
```bash
python -m pytest tests/ \
  --ignore=tests/test_qrt_004_solver_completion_time.py \
  --ignore=tests/test_qrt_006_solver_optimality.py \
  --ignore=tests/test_integration.py \
  --ignore=tests/test_loaders.py \
  --ignore=tests/test_script.py \
  -v
```

Quality requirement tests (QRT):
```bash
python -m pytest tests/test_qrt_001_api_responsiveness.py \
  tests/test_qrt_002_api_confidentiality.py \
  tests/test_qrt_003_critical_module_coverage.py \
  tests/test_qrt_005_docs_availability.py -v
```
Note: `test_qrt_001` and `test_qrt_002` use the `client`/`app` fixtures from `conftest.py`. These fixtures point to `api/MVPv3/Web/app.py`.

Run manually only (not part of CI): `test_qrt_004_solver_completion_time.py`, `test_qrt_006_solver_optimality.py`, `test_integration.py`, `test_loaders.py`, `test_script.py`

Coverage (config file: `coveragerc`, source folder: `api/MVPv3`):
```bash
python -m pytest tests/ \
  --ignore=tests/test_qrt_004_solver_completion_time.py \
  --ignore=tests/test_qrt_006_solver_optimality.py \
  --ignore=tests/test_integration.py \
  --ignore=tests/test_loaders.py \
  --ignore=tests/test_script.py \
  --cov-config=coveragerc --cov --cov-report=term-missing --cov-report=xml
```

Run these lint/test/coverage commands, and make sure they pass, before finishing any task that touches code.

## Lint & security

```bash
flake8 api/
bandit -r api/ -ll
```

## Agent operating notes

- Branch names must follow `<issue-number>-<short-slug>` (example: `94-course-task-documentation-week-6`) and be linked to a GitHub issue.
- A PR needs approval from at least one other team member before merge, on top of passing CI. Full PR/review workflow is in [CONTRIBUTING.md](CONTRIBUTING.md).
- CI (`ci-file-checks.yml`, `ci-tests.yml`, `ci-qrt.yml`, `ci-link-check.yml`) must pass before merge - run the matching commands above locally first, don't rely on CI to catch failures.
- Don't add or change dependencies outside what CI installs (see Setup above) without calling it out - CI has no separate dev-requirements file, so a new import can silently break CI.

## Safety & data

- Protected endpoints need the `X-API-Key` header (see [QR-002](docs/quality-requirements.md#qr-002-route-data-confidentiality)).
- Never commit a real `.env` file, API keys, or customer route/order data. Copy `.env.example` to `.env` and set `API_KEY` only on your own machine.
- Do not log or print full request payloads that have route data, anywhere in the app code.

## Further reading

- [README.md](README.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [docs/architecture/README.md](docs/architecture/README.md)
- [docs/quality-requirements.md](docs/quality-requirements.md)
- [docs/quality-requirement-tests.md](docs/quality-requirement-tests.md)