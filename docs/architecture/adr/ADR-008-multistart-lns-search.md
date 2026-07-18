# ADR-008: Multi-Start Search with Best-of Selection, Plus LNS Polishing

**Status:** Accepted

**Quality requirements addressed:** QR-004

## Context

A single solve attempt (pool generation via Clarke-Wright/insertion heuristics, CP-SAT set-partition selection, consolidation, loader assignment) is stochastic - restarts inside pool generation use randomized jitter, so `total_cost` varies from run to run. On small/medium instances (tens to low hundreds of orders), a single attempt finishes in a small fraction of the overall time budget, so most of QR-004's allowance sat unused while run-to-run cost variance (observed up to several percent of `total_cost` on some instances) meant the pipeline could land on a noticeably worse-than-typical result depending on which random pool it happened to build. The team needed a way to use the remaining time budget to reduce this variance and improve typical solution quality, without changing the correctness guarantees the single-attempt design already provided.

Options considered:
- Keep a single attempt per solve (status quo)
- Multi-start: run independent full attempts until time runs out, keep the best by real cost
- Simulated annealing / genetic algorithm over the whole solution from scratch
- Increase CP-SAT's own internal time limit instead of adding an outer loop

## Decision

`solve_pipeline()` runs solve attempts in a loop ("multi-start"): each attempt calls `solve_with_feedback()` with a fresh randomized pool, and the attempt's real `total_cost` (computed against the actual, unmodified weights via `stats_scenario`, even if the attempt itself solved against an artificially inflated `optional_order_penalty` - see `optional_penalty_factor`) decides whether it replaces the current best. The loop keeps running while enough time remains for at least a truncated attempt, shrinking pool budgets for that final attempt rather than skipping it. Once multi-start stops, remaining time goes to an LNS (Large Neighborhood Search) polishing phase: `inter_route_local_search` and `merge_multi_trip_routes` refine the current best, loaders are re-solved, and if the result strictly improves on the best cost so far it is accepted; otherwise `perturb_solution` applies random relocate-moves to the best solution and the loop tries again, with perturbation strength increasing after consecutive non-improving rounds. Separately, a one-time OR-Tools routing run (`ortools_generate_routes`, optional, off by default) can seed additional candidate routes into every attempt's pool at negligible extra cost, rather than being regenerated inside each attempt.

## Rationale

- Multi-start directly targets the observed problem: the minimum of several independent stochastic attempts has materially lower variance than a single attempt, and on small/medium instances there is enough spare time budget to run several attempts instead of one.
- Deriving best-attempt selection from the real cost (`stats_scenario`), independent of any artificially inflated internal penalty used to bias the CP-SAT solver's own missed-order tradeoff, keeps `optional_penalty_factor` a purely internal tuning knob that cannot silently change what "best" means to the customer.
- LNS polishing reuses the same route-evaluation and local-search building blocks already needed elsewhere (`inter_route_local_search`, `merge_multi_trip_routes`), so it adds a controlled outer loop rather than a second, differently-structured optimization engine.
- A one-time OR-Tools seed avoids the wasted work of the earlier design, where enabling OR-Tools re-ran it inside every multi-start attempt's pool generation - regenerating routes that then still had to compete for room in that attempt's pool.

## Consequences

### Positive

- Solution quality on small/medium instances is both better on average and less variable run-to-run, since the pipeline no longer commits to whichever single random pool it happened to build first.
- Large instances, where a single attempt already consumes most of the time budget, automatically degrade to the original single-attempt behavior without any special-casing - the loop simply doesn't have time for a second attempt.
- The LNS phase ensures the time budget is never fully idle: any time left after multi-start stops is spent trying to improve the best solution found so far, monotonically (a perturbed candidate is only kept if it strictly improves on the current best).

### Negative

- Total pipeline behavior is now materially harder to reason about and test: the number of multi-start attempts and LNS rounds actually run depends on wall-clock timing, machine speed, and instance size, making exact output non-reproducible run-to-run even for the same input (only the never-degrading-best-cost property is guaranteed).
- Failed attempts (e.g., a truncated pool leaving no feasible loader assignment) are caught and discarded rather than surfaced, which could mask a systematic bug that only manifests under tight budgets, since the pipeline "silently" falls back to whatever earlier attempt succeeded.
- The interaction between `optional_penalty_factor` (internal solver bias) and `stats_scenario` (real-cost comparison) is subtle - a future change to either needs to preserve the property that internal bias never leaks into the externally-reported cost used for the best-of comparison.

### Tradeoffs

- A from-scratch metaheuristic (simulated annealing/genetic algorithm) was rejected: it would require a new solution representation and move-set independent of the existing CP-SAT/local-search building blocks, a much larger change than reusing what the pipeline already had.
- Simply raising CP-SAT's own internal time limit was rejected: earlier empirical testing (see [ADR-005](ADR-005-solver-time-limits.md)) found that beyond a point, more time inside a single CP-SAT call did not improve `total_cost` - the bottleneck was the composition of the route pool, not solver search time within a fixed pool, which is what motivated running multiple independently-generated pools instead.

## Links

- [QR-004: Solver completion time](../../quality-requirements.md#qr-004-solver-completion-time)
- [Sequence Diagram](../dynamic-view/sequence-diagram.puml)
- [ADR-005: Deadline distribution and size-adaptive budgets](ADR-005-solver-time-limits.md)
