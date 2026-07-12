# Testing

## Testing Strategy

Our platform has two CVRPTW solver pipelines in `api/MVPv2.2/`, and we test both:

- **PyVRP pipeline** (`PyVRP/script.py` + `PyVRP/loaders.py`). `script.py` builds
  the vehicle routes with PyVRP. A greedy algorithm in `loaders.py` then assigns
  the loaders to the orders that need them. `script.py` runs the full pipeline
  and writes `output.json`.
- **CP-SAT pipeline** (`CP-SAT/main.py` + `CP-SAT/vehicle_routes.py` +
  `CP-SAT/loader_routes.py`). `main.py` runs a two-step pipeline. First it
  generates a pool of feasible vehicle routes. Then a CP-SAT set-partitioning model
  picks the best subset of routes. The same idea is used for the loaders:
  chains of loader slots are built with an insertion heuristic, and a second
  CP-SAT model picks the best chains.

Both pipelines share modules across the `MVPv2.2` tree:

- `Web/validator.py` - validates `input.json` before any solver runs.
- `Shared/verifier.py` - checks the solution (capacity, time windows, shift) on
  `output.json`.
- `tester.py` - calculates the total cost of a solution and compares it with
  the baseline. It also writes an Excel report (`comparison.xlsx`).
- `Shared/models.py` - data classes used by both pipelines.
- `Web/app.py` - Flask REST API exposing both pipelines.
- `Shared/history.py` - SQLite persistence for calculation history
  (`GET /history`, `GET /history/{id}`).
- `CP-SAT/common_functions.py` - shared distance helper used by the CP-SAT
  route generators.

We focus our testing on the following areas, because a bug in any of them breaks the
result or the baseline comparison:

- **Input validity:** `Web/validator.py` must reject broken input before any
  solver runs.
- **Feasibility:** every route must respect capacity, time windows and the
  shift limit. `Shared/verifier.py` checks this for every solution.
- **Correct data:** arrival times and the loader task list must be calculated
  correctly, because the loader step and the verifier use them.
- **Cost calculation:** `tester.py` must compute the total cost correctly,
  so the comparison with the baseline is trustworthy.
- **API contract:** `Web/app.py` must respond to /health and /solve under 2s and
  reject requests without a valid API key (QRT-001, QRT-002).
- **Critical module testability:** each critical module must have at least
  30% automated line coverage (QRT-003, QR-003).
- **Solver completion time:** the CP-SAT solver must complete within 15 minutes
  on a realistic test instance (QRT-004, QR-004).
- **Docs availability:** the hosted documentation site must be reachable and
  serve the entry page (QRT-005, QR-005).
- **Solver optimality:** the solver must beat the baseline `total_cost` (computed by `tester.calc_cost()`) on at
  least 7 out of 10 standard test instances (QRT-006, QR-006).

PyVRP and CP-SAT can both give different results on every run. So we only run them in integration tests, with a short runtime and a small instance. Each integration test runs in its own temporary folder, because the
code writes files with fixed names.

## Critical Modules and Coverage

| Critical module | Path in `api/MVPv2.2/` | Why critical | Required line coverage | Current line coverage | Evidence |
|---|---|---|---:|---:|---|
| `script.py` | `PyVRP/script.py` | Pipeline orchestration, input validation entry point, and data transforms that feed the loader step and the output. | 30% | 90% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `loaders.py` | `PyVRP/loaders.py` | Greedy loader assignment. Core logic for minimizing loaders. | 30% | 89% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `main.py` | `CP-SAT/main.py` | Two-step pipeline: route pool generation (Clarke-Wright and insertion) and CP-SAT set partitioning for vehicles and loaders. | 30% | 87% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `verifier.py` | `Shared/verifier.py` | Feasibility check (capacity, time windows, shift). Guards the correctness of every solution. | 30% | 90% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `validator.py` | `Web/validator.py` | Input schema and value validation. Stops the solvers from running on broken input. | 30% | 82% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `tester.py` | `tester.py` | Calculates the total cost of a solution and exports the baseline comparison report. | 30% | 92% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `app.py` | `Web/app.py` | REST API entrypoint (Flask) exposing `/solve`, `/solution`, `/history`, and `/validate`. | 30% | 75% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `history.py` | `Shared/history.py` | SQLite persistence for calculation history. Powers `GET /history` and `GET /history/{id}`. | 30% | - | Tested through integration tests in `conftest.py` (app fixture). |

**Global repository coverage:** 85% (source limited to `api/MVPv2.2` per `coveragerc`)

## Automated Test Status

| Test type | Scope | Command or CI check | Latest result | Evidence |
|---|---|---|---|---|
| Unit tests | `verifier.py` (shift, time window, capacity checks; route segmentation) | `pytest tests/test_verifier.py` | 11 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests | `validator.py` (schema, value ranges, time window order, duplicate ids, invalid JSON) | `pytest tests/test_validator.py` | 26 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests | `tester.py` (Euclidean distance, coord lookup, cost components, optional penalty, missing required orders, Excel export) | `pytest tests/test_tester.py` | 8 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests (solution A) | `script.py` (`find_distance`, `compute_times`, `create_loaders_task_list`, `build_output`, input validation) | `pytest tests/test_script.py` | 8 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests (solution A) | `loaders.py` (Point fields, sorting, distance matrix, `calculate`, `reset_state`) | `pytest tests/test_loaders.py` | 5 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests (solution B) | `vehicle_routes.py`, `loader_routes.py` | `pytest tests/test_main.py` | 22 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Integration tests (solution A) | Full `script.py` pipeline on a small instance (5 orders, 2-second PyVRP runtime), checked by `verifier.py` | `pytest tests/test_integration.py` | 6 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Integration tests (solution B) | Full `main.py` pipeline on a small instance (5 orders, reduced restarts), checked by `verifier.py` | `pytest tests/test_integration_cpsat.py` | 6 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Automated QRTs (CI) | QR-001 (responsiveness), QR-002 (confidentiality), QR-003 (coverage), QR-005 (docs availability) | `pytest tests/test_qrt_001_api_responsiveness.py tests/test_qrt_002_api_confidentiality.py tests/test_qrt_003_critical_module_coverage.py tests/test_qrt_005_docs_availability.py` | 4 QRT suites | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689676) |
| Automated QRT (manual) | QR-004 (solver timing) - runs outside CI due to solver runtime | `pytest tests/test_qrt_004_solver_completion_time.py -v --timeout=950` | N/A | N/A |
| Automated QRT (manual) | QR-006 (solver optimality against baseline via `tester.calc_cost()`) | `pytest tests/test_qrt_006_solver_optimality.py -v` (not in CI) | N/A | N/A |
| Linting & formatting (`flake8`) | PEP8 style, syntax, spacing, line length | `flake8 api/` | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689663) |
| Additional QA check (`bandit`) | Static analysis for security issues | `bandit -r api/ -ll` | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689663) |
| Link checking | All Markdown files (`lychee`) | `lychee --cache --verbose --no-progress --exclude "http://139.100.207.201:5000" './**/*.md' './reports/**/*.md'` (via `lycheeverse/lychee-action@v2` in CI) | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689663) |

## CI and QA Check Status

| Gate or check | Required for Done? | Latest protected-branch status | Evidence |
|---|---|---|---|
| Linting & formatting (`flake8`) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689663) |
| Unit tests (shared modules) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests (solution A) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests (solution B) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Integration tests (solution A) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Integration tests (solution B) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Line coverage (≥30% per critical module) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Additional QA check (`bandit` security audit) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689663) |

## Additional QA Check Rationale

| QA objective or risk | Additional QA check | Scope | Latest result | Evidence | Limitations or follow-up |
|---|---|---|---|---|---|
| Common security issues in Python code (hardcoded credentials, SQL injection, shell injection, unsafe imports) | `bandit` static analysis | All `api/` source code | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689663) | Uses `-ll` (low-confidence skip); may miss some patterns. Covers source-code risks, not dependency CVEs. |

`bandit` runs as the additional automated QA check in `ci-file-checks.yml`. It satisfies the Assignment 4 requirement for an extra automated check beyond linting, formatting, tests, coverage, QRTs, and link checking. As a static-analysis security tool, it is distinct from the `flake8` linting + formatting job and the `pytest` test jobs.

## Manual Evidence That Does Not Count as QRT

| Evidence | Scope | Result | Follow-up PBI or issue |
|---|---|---|---|
| Manual run of `Shared/verifier.py` on full `input.json` (113 orders) for both pipelines | Feasibility of the full solution | ALL CHECKS PASSED | - |
| Manual run of `tester.py` on `i1`–`i10` comparing solver output against baseline | Cost comparison, Excel report `comparison.xlsx` | Solver beats baseline on 9/10 instances | - |

## CI and Branch Protection

- **CI pipeline:** [CI workflow](https://github.com/iu-students/route-optimization-platform/actions)
- **Latest protected-default-branch run:** [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637)
- **Branch protection / rules evidence:** ![Branch protection](../img/branch-protection.png)

## Continuation of Quality Gates

- Unit and integration tests for **both** pipelines must keep passing on
  every merge to `main`.
- Line coverage for critical modules must stay above 30%.
- QRT-001, QRT-002, QRT-003, QRT-005 run in CI on every PR and push to `main`.
- QRT-004 (solver completion time) runs outside CI. Execute manually:
  `pytest tests/test_qrt_004_solver_completion_time.py -v --timeout=950`.
- QRT-006 (solver optimality against baseline) runs outside CI. Execute manually:
  `pytest tests/test_qrt_006_solver_optimality.py -v`.
  Both baseline scores and solver output are compared using `tester.calc_cost()`.
- Linting & formatting (`flake8`) must pass on every merge to `main`.
- Additional QA check (`bandit` static analysis) must pass on every merge to `main`.
- Link checking (`lychee`) must pass on every merge to `main`.
- If any gate is replaced, the replacement must be documented and provide
  equal or stronger coverage.
- If one of the two pipelines is dropped, its critical-module rows and its
  tests may be removed, but the remaining pipeline must still meet all the
  gates above.