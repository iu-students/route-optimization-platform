# ADR-005: Configurable Solver Time Limits for Predictable Completion

**Status:** Accepted

**Quality requirements addressed:** QR-004

## Context

The CP-SAT solver (`CP-SAT/main.py`) can run for unpredictable durations depending on problem size, constraint complexity, and search-space branching. A solve that never terminates would block the background thread, prevent subsequent solves, and waste server resources. The team needed a mechanism to bound solver runtime while still producing useful solutions.

Options considered:
- Hard-coded CP-SAT `max_time_in_seconds` parameter
- Configurable time limit via `general_parameters` in input JSON
- External watchdog process that kills the solver thread
- No time limit (best-effort)

## Decision

Set CP-SAT's `max_time_in_seconds` solver parameter to 240 seconds per solver invocation (vehicle routing and loader assignment each get 240s), exposed as a configurable value in `general_parameters.max_solver_time` in the input JSON schema. If the parameter is absent, a default of 240s applies.

## Rationale

- CP-SAT natively supports `max_time_in_seconds` - no external infrastructure needed.
- 240 seconds is long enough for practical instances (up to 20 orders) to reach near-optimal solutions but short enough that the total solve (vehicles + loaders + feedback iteration) fits within QR-004's 15-minute bound.
- Making it configurable lets the customer trade off solution quality against response time per problem instance.

## Consequences

### Positive

- Solver runtime is bounded at the algorithm level - the background thread always progresses to the output + verification step within a known window.
- The bound propagates to the API: the client's polling loop can set a worst-case upper bound on total wait time.
- No separate watchdog process needed.

### Negative

- A hard time limit may stop the solver before it finds the optimal solution. The returned solution is the best feasible solution found within the time limit, not necessarily the global optimum.
- Two solver invocations (vehicles, loaders) each consume up to 240s - total wall-clock solve time can reach ~480s plus post-processing.

### Tradeoffs

- An external watchdog was rejected: CP-SAT's internal time limit is cleaner because it lets the solver return the best solution found so far instead of killing it mid-search.

## Links

- [QR-004: Solver completion time](../../quality-requirements.md#qr-004-solver-completion-time)
- [Sequence Diagram](../dynamic-view/sequence-diagram.puml)
