## Learning points

1. **Departure Time Optimization and Route Restructuring** The final 2% gap on test case 4 was by fixing a specific logistical flaw: vehicles were leaving the depot too late. Implementing optimal departure time logic, route rearrangement, and multi-run checks for small inputs allowed the algorithm to outperform the baseline on 100% (10/10) of test cases.
2. **Explicit security and configuration hygiene is crucial for independent deployment.** Team recieved customer feedback regarding runtime data (`data/`, `history.db`) not being in `.gitignore` and undocumented network ports. Fixing these issues ensured a clean, secure handover without risking user data leaks.
3. **Heuristic algorithm stability must be clearly communicated as a known limitation.** Because the solution uses CP-SAT and metaheuristics, results can vary slightly between runs. Documenting this in `docs/customer-handover.md` was essential to set correct customer expectations and prevent future support conflicts.
4. **Structured handover documentation directly drives customer acceptance.** Providing clear  instructions and administrator access allowed the customer to independently pull, deploy, and verify the product in local environment without requiring live team assistance.

## Validated assumptions

### Confirmed

- **CP-solver optimization resolves the final performance gap.** By expanding the route pool with high-quality paths and changing generation settings to reduce loader count, the CP Solver successfully beat the baseline on all 10 test cases.
- **Customer is ready to independently use and operate the product.** The customer successfully pulled the repository, verified the documentation was sufficient, and officially accepted the solution during the Week 7 Sprint Review.

### Rejected

- **[An automatic threshold-based algorithm switcher was required to beat case 4].** The team initially thought a fallback switcher (based on order count) would be necessary, but directly optimizing the depot departure logic in the primary CP solver resolved the gap without needing a secondary pipeline.

## Friction and gaps

- **Heuristic algorithm variance.** Although accepted by the customer, there is a minor risk that results might vary slightly between runs or on different machines.

## Planned response

- Maintain post-handover support availability for the customer as they continue running local tests and verifying algorithm metrics.