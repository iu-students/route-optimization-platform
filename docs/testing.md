# Testing

## Testing Strategy

Our platform has two CVRPTW solutions, and we test both.

- **Solution A (PyVRP).** `script.py` builds the vehicle routes with PyVRP.
  A greedy algorithm in `loaders.py` then assigns the loaders to the orders
  that need them. `script.py` runs the full pipeline and writes `output.json`.
- **Solution B (CP-SAT).** `main.py` runs a two-step pipeline. First it
  generates a pool of feasible vehicle routes. Then a CP-SAT set-partitioning model
  picks the best subset of routes. The same idea is used for the loaders:
  chains of loader slots are built with an insertion heuristic, and a second
  CP-SAT model picks the best chains.

Both solutions share five modules:

- `validator.py` — validates `input.json` before any solver runs. Used by
  both pipelines.
- `verifier.py` — checks the solution (capacity, time windows, shift) on
  `output.json`.
- `tester.py` — calculates the total cost of a solution and compares it with
  the baseline. It also writes an Excel report (`comparison.xlsx`).
- `models.py` — data classes used by both pipelines.
- `app.py` — Flask REST API exposing both pipelines.

We focus our testing on five things, because a bug in any of them breaks the
result or the baseline comparison:

- **Input validity:** `validator.py` must reject broken input before any
  solver runs.
- **Feasibility:** every route must respect capacity, time windows and the
  shift limit. `verifier.py` checks this for every solution.
- **Correct data:** arrival times and the loader task list must be calculated
  correctly, because the loader step and the verifier use them.
- **Cost calculation:** `tester.py` must compute the total cost correctly,
  so the comparison with the baseline is trustworthy.
- **API contract:** `app.py` must respond to /health and /solve under 2s and
  reject requests without a valid API key (QRT-001, QRT-002).
- **Critical module testability:** each critical module must have at least
  30% automated line coverage (QRT-003, QR-003).

PyVRP and CP-SAT can both give different results on every run. So we only run them in integration tests, with a short runtime and a small instance. Each integration test runs in its own temporary folder, because the
code writes files with fixed names.

## Critical Modules and Coverage

| Critical module | Solution | Why critical | Required line coverage | Current line coverage | Evidence |
|---|---|---|---:|---:|---|
| `script.py` | A | Pipeline orchestration, input validation entry point, and data transforms that feed the loader step and the output. | 30% | 90% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `loaders.py` | A | Greedy loader assignment. Core logic for minimizing loaders (US-006). | 30% | 89% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `main.py` | B | Two-step pipeline: route pool generation (Clarke-Wright and insertion) and CP-SAT set partitioning for vehicles and loaders. | 30% | 87% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `verifier.py` | shared | Feasibility check (capacity, time windows, shift). Guards the correctness of every solution. | 30% | 90% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `validator.py` | shared | Input schema and value validation. Stops the solvers from running on broken input. | 30% | 82% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `tester.py` | shared | Calculates the total cost of a solution and exports the baseline comparison report. | 30% | 92% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |
| `app.py` | shared | REST API entrypoint (Flask) exposing `/solve` and `/solution` over both pipelines. | 30% | 75% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637/job/83840364456?pr=68) |

**Global repository coverage:** 88%

## Automated Test Status

| Test type | Scope | Command or CI check | Latest result | Evidence |
|---|---|---|---|---|
| Unit tests | `verifier.py` (shift, time window, capacity checks; route segmentation) | `pytest tests/test_verifier.py` | 11 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests | `validator.py` (schema, value ranges, time window order, duplicate ids, invalid JSON) | `pytest tests/test_validator.py` | 26 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests | `tester.py` (Euclidean distance, coord lookup, cost components, optional penalty, missing required orders, print and Excel export) | `pytest tests/test_tester.py` | 13 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests (solution A) | `script.py` (`find_distance`, `compute_times`, `create_loaders_task_list`, `build_output`, input validation) | `pytest tests/test_script.py` | 8 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests (solution A) | `loaders.py` (Point fields, sorting, distance matrix, `calculate`, `reset_state`) | `pytest tests/test_loaders.py` | 5 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests (solution B) | `main.py` (`find_distance`, `eval_route`, `best_insertion_pos`, `insertion_construct`, `clarke_wright`, `build_slots`, `eval_chain`, `chains_insertion_construct`) | `pytest tests/test_main.py` | 22 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Integration tests (solution A) | Full `script.py` pipeline on a small instance (5 orders, 2-second PyVRP runtime), checked by `verifier.py` | `pytest tests/test_integration.py` | 6 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Integration tests (solution B) | Full `main.py` pipeline on a small instance (5 orders, reduced restarts), checked by `verifier.py` | `pytest tests/test_integration_cpsat.py` | 6 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Automated QRTs | `app.py` (API responsiveness, confidentiality), critical module coverage | `pytest tests/test_qrt_001_api_responsiveness.py tests/test_qrt_002_api_confidentiality.py tests/test_qrt_003_critical_module_coverage.py` | 11 QRTs + coverage check | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689676) |

## CI and QA Check Status

| Gate or check | Required for Done? | Latest protected-branch status | Evidence |
|---|---|---|---|
| Linting (`flake8`) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689663) |
| Unit tests (shared modules) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests (solution A) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Unit tests (solution B) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Integration tests (solution A) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Integration tests (solution B) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Line coverage (≥30% per critical module) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637) |
| Additional QA check (`pip-audit`) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689663) |

## Additional QA Check Rationale

| QA objective or risk | Additional QA check | Scope | Latest result | Evidence | Limitations or follow-up |
|---|---|---|---|---|---|
| Known vulnerabilities in dependencies (pyvrp, ortools, numpy, openpyxl) could cause incorrect results or security issues | `pip-audit` | All Python dependencies | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689663) | Only checks known CVEs; does not cover zero-day vulnerabilities or supply-chain attacks. |

`pip-audit` scans the resolved dependency tree for known CVEs.

Other options considered:

- **`bandit`.** Useful, but our
  code is not exposed to untrusted input the way a web service is. `pip-audit`
  covers a more realistic risk for this project (third-party packages with
  known CVEs).
- **`mypy`.** Already partly covered by editor tooling
  and would mostly catch issues that unit tests already catch.

## Manual Evidence That Does Not Count as QRT

| Evidence | Scope | Result | Follow-up PBI or issue |
|---|---|---|---|
| Manual run of `verifier.py` on full `input.json` (113 orders) for both solutions | Feasibility of the full solution | ALL CHECKS PASSED | — |
| Manual run of `tester.py` on `t1`, `t2`, `t3` comparing solution A, solution B and the baseline | Cost comparison, Excel report `comparison.xlsx` | Both solutions feasible, baseline comparison recorded | — |

## CI and Branch Protection

- **CI pipeline:** [CI workflow](https://github.com/iu-students/route-optimization-platform/actions)
- **Latest protected-default-branch run:** [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28297689637)
- **Branch protection / rules evidence:** ![Branch protection](../img/branch-protection.png)

## Continuation of Quality Gates

- Unit and integration tests for **both** solutions must keep passing on
  every merge to `main`.
- Line coverage for critical modules must stay above 30%.
- QRT-001, QRT-002, QRT-003 run in CI on every PR and push to `main`.
- `pip-audit` must keep running in CI.
- If any gate is replaced, the replacement must be documented and provide
  equal or stronger coverage.
- If one of the two solutions is dropped, its critical-module rows and its
  tests may be removed, but the remaining solution must still meet all the
  gates above.