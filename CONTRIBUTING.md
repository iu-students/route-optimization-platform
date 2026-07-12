# Contributing

This guide covers how to contribute changes to the Route Optimization Platform. For project description, team, and run instructions, see [README.md](README.md).

## Setup

```bash
cp .env.example .env
docker compose up --build -d
curl http://localhost:5002/health
```

Set `API_KEY` inside `.env` before starting.

For local development without Docker (running tests, linting):

```bash
pip install flask flask-cors numpy pyvrp ortools openpyxl pytest pytest-cov coverage flake8 bandit
```

## Before submitting a change

Run the same test jobs CI runs.

MVPv1 / MVPv1.2 logic tests:

```bash
python -m pytest tests/ --ignore=tests/test_qrt_001_api_responsiveness.py --ignore=tests/test_qrt_002_api_confidentiality.py --ignore=tests/test_qrt_003_critical_module_coverage.py -v
```

MVPv2 logic tests:

```bash
TEST_TARGET=v2 python -m pytest tests/ --ignore=tests/test_main.py --ignore=tests/test_integration_cpsat.py --ignore=tests/test_tester.py --ignore=tests/test_qrt_001_api_responsiveness.py --ignore=tests/test_qrt_002_api_confidentiality.py --ignore=tests/test_qrt_003_critical_module_coverage.py -v
```

Coverage:

```bash
python -m pytest tests/ --cov-config=coveragerc --cov --cov-report=term-missing -v
```

Quality requirement tests (QRT):

```bash
python -m pytest tests/test_qrt_001_api_responsiveness.py \
  tests/test_qrt_002_api_confidentiality.py \
  tests/test_qrt_003_critical_module_coverage.py \
  tests/test_qrt_004_solver_completion_time.py \
  tests/test_qrt_005_docs_availability.py -v
```

Lint and security checks:

```bash
flake8 api/
bandit -r api/ -ll
```

## Branch and PR workflow

1. Create a branch named `<issue-number>-<short-slug>` (e.g. `94-course-task-documentation-week-6`), tied to a GitHub issue.
2. Commit your changes and open a PR against `main`.
3. CI runs automatically on every PR and on push to `main`: linting and security audit, unit/integration tests with coverage, quality requirement tests, markdown link check.

## Review and merge requirements

- All CI checks must pass before merge (see workflow list above).
- At least one other team member must approve the PR.
- Both requirements are enforced by branch protection rules on `main`.

## Further reading

- [README.md](README.md)
- [AGENTS.md](AGENTS.md) - command reference for coding agents working in this repo
- [docs/architecture/README.md](docs/architecture/README.md)
- [docs/quality-requirements.md](docs/quality-requirements.md)
- [docs/quality-requirement-tests.md](docs/quality-requirement-tests.md)