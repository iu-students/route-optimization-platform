# Contributing

This guide explains how to contribute changes to the Route Optimization Platform. For the project description, the team, and run instructions, see [README.md](README.md).

## Setup

```bash
cp .env.example .env
docker compose up --build -d
curl http://localhost:5003/health
```

Set `API_KEY` inside `.env` before you start the app.

If you develop without Docker (for tests and linting), install these:

```bash
pip install flask flask-cors numpy ortools openpyxl pytest pytest-cov coverage flake8 bandit
```

## Before submitting a change

Run the same test jobs that CI runs. All CI test jobs are for MVPv3 (`TEST_TARGET=v3`, which is the default in `conftest.py`).

Logic tests (same as `ci-tests.yml`):

```bash
python -m pytest tests/ \
  --ignore=tests/test_qrt_004_solver_completion_time.py \
  --ignore=tests/test_qrt_006_solver_optimality.py \
  --ignore=tests/test_integration.py \
  --ignore=tests/test_loaders.py \
  --ignore=tests/test_script.py \
  -v
```

Coverage:

```bash
python -m pytest tests/ \
  --ignore=tests/test_qrt_004_solver_completion_time.py \
  --ignore=tests/test_qrt_006_solver_optimality.py \
  --ignore=tests/test_integration.py \
  --ignore=tests/test_loaders.py \
  --ignore=tests/test_script.py \
  --cov-config=coveragerc --cov --cov-report=term-missing -v
```

Quality requirement tests (QRT) - CI only runs these four:

```bash
python -m pytest tests/test_qrt_001_api_responsiveness.py \
  tests/test_qrt_002_api_confidentiality.py \
  tests/test_qrt_003_critical_module_coverage.py \
  tests/test_qrt_005_docs_availability.py -v
```

`test_qrt_004_solver_completion_time.py` and `test_qrt_006_solver_optimality.py` are only for manual runs. CI does not run them.

Lint and security checks:

```bash
flake8 api/
bandit -r api/ -ll
```

## Branch and PR workflow

1. Create a branch named `<issue-number>-<short-slug>` (example: `94-course-task-documentation-week-6`) and link it to a GitHub issue.
2. Commit your changes and open a PR against `main`.
3. CI runs automatically on every PR and on every push to `main`. It checks: linting and security, unit/integration tests with coverage, quality requirement tests, and the markdown link check.

## Review and merge requirements

- All CI checks must pass before you can merge (see the list above).
- At least one other team member must approve your PR.
- Both rules are enforced by branch protection on `main`.

## Further reading

- [README.md](README.md)
- [AGENTS.md](AGENTS.md)
- [docs/architecture/README.md](docs/architecture/README.md)
- [docs/quality-requirements.md](docs/quality-requirements.md)
- [docs/quality-requirement-tests.md](docs/quality-requirement-tests.md)