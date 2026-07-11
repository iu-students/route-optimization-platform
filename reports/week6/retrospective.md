# Sprint 4 Retrospective

## What went well

1. **Significant algorithm improvement:** The CP-solver-based algorithm, now integrated with the multi-route per vehicle logic, outperforms the baseline on 9 out of 10 test cases. All cases run within the 10–14 minute timeframe, which is a major step forward in solution quality and time management.
2. **Calculation history feature delivered:** The team successfully implemented US-017 (calculation history) with database integration, allowing past runs to be tracked and metrics to be saved, directly addressing the customer's request from the previous sprint.
3. **Successful transition-readiness meeting:** The customer confirmed that the product is functionally ready for handover. The team began preparing the repository for transfer, including admin rights. Prepared handover/collaboration files (`docs/customer-handover.md`, `CONTRIBUTING.md`, `AGENTS.md`).


## What did not go well

1. **Test case 4 still underperforms:** The algorithm loses to the baseline by approximately 2% on the 4th test case due to vehicle routing issues. This remains the only unresolved algorithmic gap before the final handover.
2. **Iterative algorithm delays:** The new iterative algorithm (point removal and reinsertion) still lacks the vehicle depot-return logic and underperforms on 2-3 test cases. It is not yet stable enough to be the primary production pipeline.

## What changed compared to the previous Sprint based on the previous Sprint Retrospective

1. **Calculation history implemented:** Following the action point from the previous retrospective, the team started implementation of the calculation history feature, including persistent storage for run results, execution time, and objective function value per run.
2. **Algorithm directions investigated:** The team acted on the customer's previous suggestions by integrating the multi-route per vehicle concept into the CP-solver algorithm, which significantly contributed to beating the baseline on 9 out of 10 cases.

## Action points (Process improvements for the next Sprint)

1. **Consider the need of implementing threshold-based algorithm switching.** Investigate an automatic switcher based on general parameters (e.g., the number of orders, like a limit of 100) to ethically leverage the strengths of both algorithm pipelines without tying them to specific test cases.
2. **Resolve the test case 4 gap and iterative algorithm delays.** Focus algorithm corrections on case 4 to close the remaining 2% gap. Complete the vehicle depot-return logic in the iterative algorithm and re-test all cases before the final `MVP v3` release.
3. **Finalize independent deployment.** Send clear deployment instructions to the customer and provide async support to ensure they can successfully deploy the solution on their side for the final transition.
