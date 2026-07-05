# Reflection

## Learning points

1. **Architecture documentation is more than diagrams.** Writing three views forced the team to articulate implicit decisions: why two pipelines coexist, why the API is async, why the verifier is shared. This made the codebase more understandable for everyone.

2. **ADRs make trade-offs visible.** ADR-001 for dual pipelines captures the rationale behind duplication, preventing future confusion about why the code is structured that way.

3. **Stage-based progress is harder than it looks.** Customer wants stage feedback, but algorithm stages vary across input sizes, the algorithm is not yet deterministic enough to expose its internal structure to users.

4. **Customer feedback accumulates and must be tracked.** The feedback table spans sprints and requires regular re-evaluation to keep items from being deferred indefinitely.

5. **Multi-route per vehicle was an overlooked constraint.** The team missed that vehicles can complete multiple routes per shift, this constraint only became apparent later.

## Validated assumptions

### Confirmed

- The asynchronous API design (202 Accepted + polling) works well for the customer — no complaints about the interaction model itself, only about the lack of progress information during polling.
- The customer does not need a visual UI, confirming the API/endpoint-only approach was the right call for this product.
- UAT recording format (customer records independently after the meeting) continues to work reliably.
- Documenting architecture in PlantUML and storing diagram sources in the repository is practical, the team was able to produce three views within the sprint.

### Rejected

- [Vehicles can go through only one route]. The team missed that vehicles can complete multiple routes per shift, this constraint only became apparent later.
- [Adding the remaining time for solution to the \solution endpoint is sufficient for interactivity]. The customer requested a stage-based progress indicator rather than a simple time estimate - showing which algorithm stage is currently in progress and how many stages remain.

## Friction and gaps

- **Stage-based progress indicator not delivered.** The customer has now mentioned this twice (Weeks 4 and 5). The blocker is that the algorithm is not stable enough to define consistent stages.
- **CP-solver time limit.** Timur's CP-solver-based approach now outperforms the baseline on 8 out of 10 test cases, but exceeds the 15-minute limit on some inputs.
- **Calculation history not started.** The customer suggested this feature as an optional quality-of-life improvement. 

## Planned response

- Implement stage-based progress indicator in the next sprint once the stable algorithm version is defined. Use algorithm stages as the unit of progress, not elapsed time.
- Analyze CP-solver time budget and identify where the 15-minute limit is being exceeded. Restructure or cap the solver before the next release.
- Add calculation history to the backlog as a concrete PBI with acceptance criteria and story points. Evaluate whether it fits in the next sprint alongside algorithm work.
- Keep the architecture documentation current as the algorithm stabilizes, update the static view if the pipeline structure changes, and update the dynamic view if the solve flow changes.
