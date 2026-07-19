# AGENTS.md

Route Optimization Platform - CVRPTW solver API (vehicle + loader routing). There are six MVP versions in `api/` (`MVPv0`, `MVPv1`, `MVPv1.2`, `MVPv2`, `MVPv2.2`, `MVPv3`). `MVPv2.2` is the version we use now. `MVPv3` is still in development. See [README.md](README.md) for the product description, the team, and full run instructions.

## Setup

Run the full stack via Docker Compose:
```bash
cp .env.example .env
docker compose up --build -d
curl http://localhost:5002/health
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

Run manually only: `test_qrt_004_solver_completion_time.py`, `test_qrt_006_solver_optimality.py`, `test_integration.py`, `test_loaders.py`, `test_script.py`

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

## Lint & security

```bash
flake8 api/
bandit -r api/ -ll
```

## Workflow

- Branch names follow `<issue-number>-<short-slug>` (example: `94-course-task-documentation-week-6`) and must be linked to a GitHub issue.
- Open a PR against `main`. You need approval from at least one other team member before you can merge.
- CI runs on every PR (open/sync/reopen) and on every push to `main`. It must pass before merge:
  - `ci-file-checks.yml` - flake8 + bandit
  - `ci-tests.yml` - unit/integration tests (MVPv3) + coverage
  - `ci-qrt.yml` - quality requirement tests
  - `ci-link-check.yml` - markdown link check (lychee)

## Safety & data

- Protected endpoints need the `X-API-Key` header (see [QR-002](docs/quality-requirements.md#qr-002-route-data-confidentiality)).
- Never commit a real `.env` file. Copy `.env.example` to `.env` and set `API_KEY` only on your own machine.
- Do not log or print full request payloads that have route data, anywhere in the app code.

## Further reading

- [README.md](README.md)
- [docs/architecture/README.md](docs/architecture/README.md)
- [docs/quality-requirements.md](docs/quality-requirements.md)
- [docs/quality-requirement-tests.md](docs/quality-requirement-tests.md)