# Testing

## Testing Strategy

Our platform solves the CVRPTW problem in two steps. First, PyVRP builds the
vehicle routes. Second, a greedy algorithm in `loaders.py` assigns the loaders
to the orders that need them. `script.py` runs the whole pipeline, writes
`output.json`, and checks the result with `verifier.py`. We also use
`tester.py` to calculate the total cost and compare our solution to the baseline.

We focus our testing on two things, because a bug here breaks the result and
the baseline comparison:

- **Feasibility:** every route must respect capacity, time windows and the shift
  limit. `verifier.py` checks this for every solution.
- **Correct data:** arrival times and the loader task list must be calculated
  correctly, because the loader step and the verifier use them.

Test types:

- **Unit tests** for the functions that need no solver: `find_distance`,
  `compute_times`, the three checks in `verifier.py`, the cost calculation in
  `tester.py`, and the greedy logic in `loaders.py`. `loaders.py` keeps global
  state, so we call `clear_loaders_state()` before each test.
- **Integration tests** that run the full `solve_pipeline` on a small example
  with a short runtime, and check that all orders are served once and the
  feasibility check passes.

PyVRP can give different results on every run, so we only use it in integration
tests. Each integration test runs in its own temporary folder because the code
writes files with fixed names.

## Critical Modules and Coverage

| Critical module | Why critical | Required line coverage | Current line coverage | Evidence |
|---|---|---:|---:|---|
| `script.py` | Pipeline orchestration and data transforms that feed the loader step and the output. | 30% | 99% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645) |
| `loaders.py` | Greedy loader assignment. Core logic for minimizing loaders (US-006). | 30% | 97% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645) |
| `verifier.py` | Feasibility check (capacity, time windows, shift). Guards the correctness of every solution. | 30% | 90% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645) |
| `tester.py` | Calculates the total cost of a solution. Used to compare with the baseline. | 30% | 66% | [Coverage run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645) |

**Global repository coverage:** 91%

## Automated Test Status

| Test type | Scope | Command or CI check | Latest result | Evidence |
|---|---|---|---|---|
| Unit tests | `find_distance`, `compute_times`, verifier checks, tester cost calc, loader logic | `pytest tests/test_verifier.py tests/test_tester.py tests/test_loaders.py tests/test_script.py` | 28 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645) |
| Integration tests | Full `solve_pipeline` on a small instance, verified by `verifier.py` | `pytest tests/test_integration.py` | 7 passed | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645) |
| Automated QRTs | To be added after QR/QRT are defined | — | — | — |

## CI and QA Check Status

| Gate or check | Required for Done? | Latest protected-branch status | Evidence |
|---|---|---|---|
| Linting (`flake8`) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645) |
| Unit tests | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645) |
| Integration tests | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645) |
| Line coverage (≥30% per critical module) | Yes | Passing (91% global) | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645) |
| Additional QA check (`pip-audit`) | Yes | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645) |

## Additional QA Check Rationale

| QA objective or risk | Additional QA check | Scope | Latest result | Evidence | Limitations or follow-up |
|---|---|---|---|---|---|
| Known vulnerabilities in dependencies (pyvrp, numpy, ortools) could cause incorrect results or security issues | `pip-audit` | All Python dependencies | Passing | [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645) | Only checks known CVEs; does not cover zero-day vulnerabilities |

## Manual Evidence That Does Not Count as QRT

| Evidence | Scope | Result | Follow-up PBI or issue |
|---|---|---|---|
| Manual run of `verifier.py` on full `input.json` (113 orders) | Feasibility of the full solution | ALL CHECKS PASSED | — |

## CI and Branch Protection

- **CI pipeline:** [CI workflow](https://github.com/iu-students/route-optimization-platform/actions)
- **Latest protected-default-branch run:** [CI run](https://github.com/iu-students/route-optimization-platform/actions/runs/28206696619/job/83558877645)
- **Branch protection / rules evidence:** ![Branch protection](../img/branch-protection.png)

## Continuation of Quality Gates

All testing and CI gates introduced in Assignment 4 remain active for later
sprints. Specifically:

- Unit and integration tests must keep passing on every merge to `main`.
- Line coverage for critical modules must stay above 30%.
- `pip-audit` must keep running in CI.
- If any gate is replaced, the replacement must be documented and provide equal
  or stronger coverage.