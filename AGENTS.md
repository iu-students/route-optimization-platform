# AGENTS.md

Route Optimization Platform — CVRPTW solver API (vehicle + loader routing). Five MVP versions coexist in `api/` (`MVPv0`, `MVPv1`, `MVPv1.2`, `MVPv2`, `MVPv2.2`); `MVPv2.2` is the current active version. See [README.md](README.md) for product description, team, and full run instructions.

## Setup

Run the full stack via Docker Compose:
```bash
cp .env.example .env
docker compose up --build -d
curl http://localhost:5002/health
```

For local test/lint work without Docker, install the packages CI uses (no dedicated dev-requirements file; installed inline in CI):
```bash
pip install flask flask-cors numpy pyvrp ortools openpyxl pytest pytest-cov coverage flake8 bandit
```

## Test

Full suite:
```bash
python -m pytest tests/ -v
```

MVPv1/MVPv1.2 subset (default `TEST_TARGET`, per `conftest.py`):
```bash
python -m pytest tests/ \
  --ignore=tests/test_qrt_001_api_responsiveness.py \
  --ignore=tests/test_qrt_002_api_confidentiality.py \
  --ignore=tests/test_qrt_003_critical_module_coverage.py -v
```

MVPv2 subset:
```bash
TEST_TARGET=v2 python -m pytest tests/ \
  --ignore=tests/test_main.py \
  --ignore=tests/test_integration_cpsat.py \
  --ignore=tests/test_tester.py \
  --ignore=tests/test_qrt_001_api_responsiveness.py \
  --ignore=tests/test_qrt_002_api_confidentiality.py \
  --ignore=tests/test_qrt_003_critical_module_coverage.py -v
```

Quality requirement tests (QRT):
```bash
python -m pytest tests/test_qrt_001_api_responsiveness.py \
  tests/test_qrt_002_api_confidentiality.py \
  tests/test_qrt_003_critical_module_coverage.py \
  tests/test_qrt_004_solver_completion_time.py \
  tests/test_qrt_005_docs_availability.py -v
```
Note: `test_qrt_001`/`test_qrt_002` use the `client`/`app` fixtures from `conftest.py`, which target `api/MVPv2.2/Web/app.py` when `TEST_TARGET=v2` (the default).

Coverage (config: `coveragerc`, source `api/MVPv2.2`):
```bash
python -m pytest tests/ --cov-config=coveragerc --cov --cov-report=term-missing --cov-report=xml
```

## Lint & security

```bash
flake8 api/
bandit -r api/ -ll
```

## Workflow

- Branches follow `<issue-number>-<short-slug>` (e.g. `94-course-task-documentation-week-6`), tied to a GitHub issue.
- Open a PR against `main`. Approval from any other team member is required before merge.
- CI runs on every PR (open/sync/reopen) and on push to `main`, and must pass before merge:
  - `ci-file-checks.yml` — flake8 + bandit
  - `ci-tests.yml` — unit/integration tests (MVPv1 and MVPv2 subsets) + coverage
  - `ci-qrt.yml` — quality requirement tests
  - `ci-link-check.yml` — markdown link check (lychee)

## Safety & data

- Protected endpoints require the `X-API-Key` header (see [QR-002](docs/quality-requirements.md#qr-002-route-data-confidentiality)).
- Never commit a real `.env`, API keys, or customer route/order data. Copy `.env.example` to `.env` and set `API_KEY` locally only.
- Do not log or print full request payloads containing route data in application code.

## Further reading

- [README.md](README.md)
- [docs/architecture/README.md](docs/architecture/README.md)
- [docs/quality-requirements.md](docs/quality-requirements.md)
- [docs/quality-requirement-tests.md](docs/quality-requirement-tests.md)