# ADR-005: Single Overall Deadline, Distributed Across Pipeline Stages and Scaled by Instance Size

**Status:** Accepted

**Quality requirements addressed:** QR-004

## Context

The CP-SAT solver (`CP-SAT/main.py`) can run for unpredictable durations depending on problem size, constraint complexity, and search-space branching. As the pipeline grew a multi-start loop and an LNS polishing phase on top of pool generation and CP-SAT selection (see [ADR-008](ADR-008-multistart-lns-search.md)), a fixed per-call time limit no longer bounds the *pipeline's* total runtime - many independently-timed steps, run an unknown number of times, could each take their full allowance and still blow past a wall-clock target.

A further complication: a fixed restart count and pool-generation budget that works well on large instances (hundreds of orders) wastes most of the time budget on small instances (tens of orders), where the pool fills up in seconds and the rest of the budget would otherwise sit idle instead of running more multi-start attempts.

## Decision

`solve_pipeline()` computes a single absolute `deadline = t_start + max_total_time` at the start of the run (`max_total_time` defaults to 840s - a 60s margin under QR-004's 900s/15-minute bound, reserved for parsing, verification, and file I/O that are not themselves deadline-aware). This deadline is threaded through every stage, and every stage's resource allocation additionally scales with instance size `n` (number of orders):

- Restart counts: `n > 500` gets fewer restarts (50/30 for vehicles/loaders), `n > 200` gets more (100/60), everything else gets the most (200/100) - larger instances need fewer restarts per pool-generation call because each call already explores more of the search space.
- Pool-generation time budgets and the per-cycle CP-SAT time limit scale the other way: `n <= 120` gets a tight budget (60/30s pool, 60s CP-SAT limit) so a full cycle finishes fast and leaves time for many multi-start attempts; `n <= 250` gets a medium budget (140/60s pool, 120s CP-SAT limit); larger instances get the original fixed budget (300/120s pool, full `time_limit`).
- Each CP-SAT selection call receives the overall `deadline` plus a `reserve_after` (30s after the vehicle CP-SAT call, 5s after the loader CP-SAT call) so it stops early enough to leave time for the steps that follow.
- The multi-start loop keeps running independent full attempts while enough time remains for at least a truncated attempt (`MIN_TIME_FOR_FEEDBACK`/`MIN_ATTEMPT_TIME` thresholds), scaling down pool budgets for a final truncated attempt rather than skipping it outright.
- Any time left after multi-start stops goes to the LNS polishing phase (see [ADR-008](ADR-008-multistart-lns-search.md)), which runs until the deadline minus a small reserve for verification and file I/O.
- `time_limit` (default 240s) remains a per-invocation upper bound as a secondary safety net, but the overall `deadline` and the size-scaled budgets are what actually govern how much work each stage gets.

This replaces the earlier fixed-240s-per-call design; `general_parameters.max_solver_time` is not read from the input JSON in the current implementation.

## Rationale

- A single deadline computed once, and passed down, is the only way to bound the *pipeline's* total wall-clock time when the number of solve attempts is itself dynamic (multi-start) rather than fixed.
- Scaling restarts and pool budgets by instance size directs time toward whichever lever actually improves solution quality for that size of problem: more independent attempts on small/medium instances (where variance between attempts matters more relative to a cheap baseline cost), more search depth per attempt on large instances (where a single pool-generation pass already consumes most of the available time).
- Reserving time for later stages (`reserve_after`) avoids the failure mode where an early stage consumes its full allowance and starves verification or the LNS phase of any time at all.
- Running a final truncated multi-start attempt (rather than stopping outright once the "comfortable" budget for a full attempt runs out) avoids idle time being wasted when a smaller, faster attempt could still fit and possibly improve on the best result so far.

## Consequences

### Positive

- Solver runtime is bounded at the pipeline level, not just per solver call - the background thread reliably progresses to the output + verification step within a known overall window.
- The bound propagates to the API: the client's polling loop can set a worst-case upper bound on total wait time.
- Small and medium instances get meaningfully more multi-start attempts than a fixed-budget design would allow, directly improving the "random variance across attempts" problem that motivated multi-start in the first place (see [ADR-008](ADR-008-multistart-lns-search.md)).

### Negative

- A hard deadline may stop any given stage before it finds its best possible result. The returned solution is the best feasible solution found within the time actually available, not necessarily the global optimum.
- The time-budgeting logic (restart counts, pool budgets, `reserve_after`, per-instance-size thresholds) is now split across `main.py`'s `solve_pipeline`/`solve_with_feedback` and the size-scaling table itself - reasoning about "how much time/how many attempts does instance size X actually get" requires reading several places together.
- `general_parameters.max_solver_time` is no longer configurable per request; all deployments share the same hard-coded defaults and size thresholds unless the code itself is changed.

### Tradeoffs

- An external watchdog was rejected: CP-SAT's internal time limit combined with an application-level deadline is cleaner because it lets each stage return the best solution/pool found so far instead of being killed mid-search.
- A fixed, non-size-scaled budget (the MVPv2.2 design) was simpler to reason about but left small instances under-utilizing their time budget and, empirically, showed higher run-to-run variance in solution cost than a scaled multi-start design.

## Links

- [QR-004: Solver completion time](../../quality-requirements.md#qr-004-solver-completion-time)
- [Sequence Diagram](../dynamic-view/sequence-diagram.puml)
- [ADR-008: Multi-start search with LNS polishing](ADR-008-multistart-lns-search.md)
